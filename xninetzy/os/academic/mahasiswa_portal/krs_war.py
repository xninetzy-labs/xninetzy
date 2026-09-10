from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.db.sqlite import connect
from app.xninetzy.os.academic.mahasiswa_portal.krs_watcher import KrsAnnouncement
from app.xninetzy.os.academic.mahasiswa_portal.reader import (
    AcademicPortalReadError,
    PORTAL_READ_FETCH_SCRIPT,
    parse_current_krs_html,
)
from app.xninetzy.os.notes.vault_service import ObsidianVaultService
from app.xninetzy.os.notifications.admin_notifier import notify_admin
from app.xninetzy.os.web_analysis.security import looks_like_login
from app.xninetzy.os.web_analysis.session_manager import SessionManager

logger = logging.getLogger(__name__)

OWNER_SCOPE = "local-owner"
KRS_PLAN_PATH = "Akademik/KRS_Plan_Semester_5.md"
KRS_WAR_LOG_PATH = "System/Logs/krs-war.md"
_CODE_RE = re.compile(r"^[A-Z]{2,4}\d{2,3}$")
_CLASS_RE = re.compile(r"^(?:I\d|BCDLITS\d+)$")
_SID_RE = re.compile(r"&sid=([a-z0-9]+)")
_TAKE_ACTION_RE = re.compile(r"krstambah_kirim\((\d+),\s*(\d+)\)")
_DROP_ACTION_RE = re.compile(r"(?:krstambah_hapus|krshapus_kirim)\((\d+)\)")
_UPGRADE_COOLDOWN_SECONDS = 180
_SEMESTER_HEADING_RE = re.compile(r"^#\s+KRS Plan Semester\s+(\d+)", re.IGNORECASE)
_MUTATION_RE = re.compile(
    r"(simpan|tambah|ambil|delete|hapus|update|submit|batal|cancel)",
    re.IGNORECASE,
)
_PRACTIKUM_FALLBACK_CODES = frozenset({"SIA302", "SID304", "SII209", "SII319"})
_BCD_SAFE_CLASSES = ("BCDLITS6", "BCDLITS5", "BCDLITS4", "BCDLITS3")
_TAKE_LINK_RE = re.compile(r"proses/[^?#]*_akademik[^?#]*\.php")
_TAKE_BONUS_RE = re.compile(r"(simpan|tambah|ambil|save|add|submit)", re.IGNORECASE)
_TAKE_PENALTY_RE = re.compile(
    r"(dilihat|lihat|view|tampil|cetak|print)", re.IGNORECASE
)

PENAWARAN_DISCOVER_SCRIPT = """
async () => {
  const results = {};
  const codePattern = /^[A-Z]{2,4}\\d{2,3}$/;
  const takeHref = (root) => {
    let best = '';
    let bestScore = -1;
    const collect = (node) => {
      const url = node.tagName === 'A' ? node.href
        : node.tagName === 'FORM' ? node.action : '';
      if (url && /proses\\/[^?#]*_akademik[^?#]*\\.php/.test(url)) {
        const score = /(simpan|tambah|ambil|save|add|submit)/i.test(url) ? 2
          : /(dilihat|lihat|view|tampil|cetak|print)/i.test(url) ? 0 : 1;
        if (score > bestScore) {
          best = url;
          bestScore = score;
        }
      }
    };
    const roots = root.tagName === 'A' || root.tagName === 'FORM' ? [root] : [];
    for (const node of roots) collect(node);
    const children = root.querySelectorAll ? root.querySelectorAll('a[href], form[action]') : [];
    for (const node of children) collect(node);
    return best;
  };
  const cells = document.querySelectorAll('td, th, li, span, div, p');
  for (const cell of cells) {
    const text = (cell.textContent || '').trim();
    if (!codePattern.test(text)) continue;
    if (results[text]) continue;
    let node = cell;
    for (let depth = 0; depth < 6 && node; depth += 1) {
      const url = takeHref(node);
      if (url) {
        results[text] = url;
        break;
      }
      node = node.parentElement;
    }
  }
  return results;
}
"""

PANEL_ENDPOINTS_SCRIPT = """
async () => {
  const found = [];
  const push = (value) => {
    if (typeof value !== 'string') return;
    const matches = value.match(/proses\\/_akademik[A-Za-z0-9_-]*\\.php/g) || [];
    for (const match of matches) {
      if (!found.includes(match)) found.push(match);
    }
  };
  const elements = document.querySelectorAll(
    'a[href], form[action], input[onclick], button[onclick], script'
  );
  for (const element of elements) {
    const source = element.getAttribute('href')
      || element.getAttribute('action')
      || element.getAttribute('onclick')
      || element.textContent
      || '';
    push(source);
  }
  return found;
}
"""

PORTAL_POST_SCRIPT = """
async (args) => {
  const resp = await fetch(args.endpoint, {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
    body: args.body
  });
  return await resp.text();
}
"""


@dataclass(frozen=True, slots=True)
class KrsPlanCourse:
    code: str
    name: str
    credits: str
    target_class: str
    fallback_classes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class KrsPlan:
    courses: tuple[KrsPlanCourse, ...]
    source_path: str
    source_hash: str
    semester_label: str

    def allowlist(self) -> frozenset[str]:
        return frozenset(course.code for course in self.courses)

    def find(self, code: str) -> KrsPlanCourse | None:
        for course in self.courses:
            if course.code == code:
                return course
        return None


def _normalize_plan_text(text: str) -> str:
    normalized = "\n".join(
        line.rstrip() for line in text.replace("\r\n", "\n").splitlines()
    )
    return normalized.strip()


def parse_krs_plan_markdown(text: str, source_path: str = "") -> KrsPlan:
    courses: list[KrsPlanCourse] = []
    seen: set[str] = set()
    semester_label = ""
    for line in text.splitlines():
        heading_match = _SEMESTER_HEADING_RE.match(line.strip())
        if heading_match:
            semester_label = f"Semester {heading_match.group(1)}"
            continue
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        code_cells = [cell for cell in cells if _CODE_RE.fullmatch(cell)]
        class_cells: list[str] = []
        for cell in cells:
            for token in re.split(r"[,/\s]+", cell):
                if _CLASS_RE.fullmatch(token) and token not in class_cells:
                    class_cells.append(token)
        if not code_cells or not class_cells:
            continue
        code = code_cells[0]
        if code in seen:
            continue
        seen.add(code)
        code_index = cells.index(code)
        name = cells[code_index - 1] if code_index > 0 else ""
        credits = cells[code_index + 1] if code_index + 1 < len(cells) else ""
        if len(class_cells) > 1:
            fallback_classes = tuple(class_cells[1:])
        else:
            fallback_classes = (
                ("I2", "I3", "I4")
                if code in _PRACTIKUM_FALLBACK_CODES
                else ("I2",)
            )
        courses.append(
            KrsPlanCourse(
                code=code,
                name=name,
                credits=credits,
                target_class=class_cells[0],
                fallback_classes=fallback_classes,
            )
        )
    source_hash = hashlib.sha256(
        _normalize_plan_text(text).encode("utf-8")
    ).hexdigest()
    return KrsPlan(
        courses=tuple(courses),
        source_path=source_path,
        source_hash=source_hash,
        semester_label=semester_label,
    )


def plan_to_json(plan: KrsPlan) -> str:
    payload = {
        "source_path": plan.source_path,
        "source_hash": plan.source_hash,
        "semester_label": plan.semester_label,
        "courses": [
            {
                "code": course.code,
                "name": course.name,
                "credits": course.credits,
                "target_class": course.target_class,
                "fallback_classes": list(course.fallback_classes),
            }
            for course in plan.courses
        ],
    }
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def plan_from_json(payload: str) -> KrsPlan | None:
    if not payload:
        return None
    try:
        data = json.loads(payload)
        courses = tuple(
            KrsPlanCourse(
                code=course["code"],
                name=course.get("name", ""),
                credits=course.get("credits", ""),
                target_class=course["target_class"],
                fallback_classes=tuple(course.get("fallback_classes") or ()),
            )
            for course in data.get("courses", [])
        )
        return KrsPlan(
            courses=courses,
            source_path=data.get("source_path", ""),
            source_hash=data.get("source_hash", ""),
            semester_label=data.get("semester_label", ""),
        )
    except (TypeError, KeyError, ValueError):
        return None


class KrsWarStore:
    def __init__(self, owner_scope: str = OWNER_SCOPE) -> None:
        self.owner_scope = owner_scope

    def get(self) -> dict:
        with connect() as conn:
            row = conn.execute(
                "SELECT * FROM krs_war_state WHERE owner_scope = ?",
                (self.owner_scope,),
            ).fetchone()
        if row is None:
            return {
                "armed": 0,
                "plan_hash": None,
                "plan_json": None,
                "last_armed_at": None,
                "last_run_window": None,
                "last_run_at": None,
                "last_status": "idle",
                "last_summary": None,
                "updated_at": None,
            }
        return dict(row)

    def set_armed(self, armed: bool, plan: KrsPlan | None = None) -> dict:
        now = datetime.now(UTC).isoformat()
        plan_hash = plan.source_hash if plan else None
        plan_json = plan_to_json(plan) if plan else None
        with connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO krs_war_state(owner_scope, armed, updated_at) "
                "VALUES(?, 0, ?)",
                (self.owner_scope, now),
            )
            if armed:
                conn.execute(
                    """
                    UPDATE krs_war_state
                    SET armed = 1,
                        plan_hash = COALESCE(?, plan_hash),
                        plan_json = COALESCE(?, plan_json),
                        last_armed_at = ?, updated_at = ?
                    WHERE owner_scope = ?
                    """,
                    (plan_hash, plan_json, now, now, self.owner_scope),
                )
            else:
                conn.execute(
                    """
                    UPDATE krs_war_state
                    SET armed = 0, updated_at = ?
                    WHERE owner_scope = ?
                    """,
                    (now, self.owner_scope),
                )
        return self.get()

    def update_run(
        self,
        *,
        window: str | None,
        status: str,
        summary: str | None = None,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO krs_war_state(owner_scope, armed, updated_at) "
                "VALUES(?, 0, ?)",
                (self.owner_scope, now),
            )
            conn.execute(
                """
                UPDATE krs_war_state
                SET last_run_window = COALESCE(?, last_run_window),
                    last_run_at = ?, last_status = ?, last_summary = ?, updated_at = ?
                WHERE owner_scope = ?
                """,
                (window, now, status, summary, now, self.owner_scope),
            )

    def record_action(
        self,
        window: str,
        action: str,
        course_code: str = "",
        class_code: str = "",
        detail: str = "",
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO krs_war_actions(
                    owner_scope, window, action, course_code, class_code, detail, created_at
                ) VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.owner_scope,
                    window,
                    action,
                    course_code,
                    class_code,
                    detail,
                    now,
                ),
            )


class KrsWarCalibrationStore:
    def __init__(self, owner_scope: str = OWNER_SCOPE) -> None:
        self.owner_scope = owner_scope

    def get(self, window: str) -> dict | None:
        with connect() as conn:
            row = conn.execute(
                "SELECT * FROM krs_war_calibration WHERE owner_scope = ? AND window = ?",
                (self.owner_scope, window),
            ).fetchone()
        return dict(row) if row is not None else None

    def save(
        self,
        window: str,
        targets: dict[str, str],
        strategy: str,
        status: str,
        attempts: int,
    ) -> dict:
        now = datetime.now(UTC).isoformat()
        targets_json = json.dumps(targets, ensure_ascii=False, sort_keys=True)
        with connect() as conn:
            conn.execute(
                """
                INSERT INTO krs_war_calibration(
                    owner_scope, window, targets_json, strategy, target_count,
                    status, attempts, last_attempt_at, updated_at
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(owner_scope, window) DO UPDATE SET
                    targets_json = excluded.targets_json,
                    strategy = excluded.strategy,
                    target_count = excluded.target_count,
                    status = excluded.status,
                    attempts = excluded.attempts,
                    last_attempt_at = excluded.last_attempt_at,
                    updated_at = excluded.updated_at
                """,
                (
                    self.owner_scope,
                    window,
                    targets_json,
                    strategy,
                    len(targets),
                    status,
                    attempts,
                    now,
                    now,
                ),
            )
        saved = self.get(window)
        return saved if saved is not None else {}

    def bump_attempt(self, window: str) -> int:
        now = datetime.now(UTC).isoformat()
        with connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO krs_war_calibration(owner_scope, window, updated_at) "
                "VALUES(?, ?, ?)",
                (self.owner_scope, window, now),
            )
            conn.execute(
                """
                UPDATE krs_war_calibration
                SET attempts = attempts + 1, last_attempt_at = ?, updated_at = ?
                WHERE owner_scope = ? AND window = ?
                """,
                (now, now, self.owner_scope, window),
            )
            row = conn.execute(
                "SELECT attempts FROM krs_war_calibration "
                "WHERE owner_scope = ? AND window = ?",
                (self.owner_scope, window),
            ).fetchone()
        return int(row["attempts"])


def _read_plan_file_text(vault_service: ObsidianVaultService | None) -> str | None:
    try:
        if vault_service is not None:
            return vault_service.read_note(KRS_PLAN_PATH)
        settings = get_settings()
        candidates = [
            Path(os.path.expanduser(settings.OBSIDIAN_VAULT_HOST_PATH)) / KRS_PLAN_PATH,
            Path(settings.OBSIDIAN_VAULT_PATH) / KRS_PLAN_PATH,
        ]
        for path in candidates:
            if path.exists():
                return path.read_text(encoding="utf-8")
        return None
    except Exception as exc:
        logger.warning("KRS plan file read failed: %s", exc)
        return None


async def load_krs_plan(
    vault_service: ObsidianVaultService | None = None,
    store: KrsWarStore | None = None,
) -> KrsPlan | None:
    store = store or KrsWarStore()
    state = store.get()
    db_plan = None
    if state.get("armed") and state.get("plan_json"):
        db_plan = plan_from_json(state["plan_json"])
        if db_plan is not None and db_plan.source_hash != state.get("plan_hash"):
            db_plan = None
    text = _read_plan_file_text(vault_service)
    if text is None:
        return db_plan
    try:
        file_plan = parse_krs_plan_markdown(text, source_path=KRS_PLAN_PATH)
    except Exception as exc:
        logger.warning("KRS plan parse failed: %s", exc)
        return db_plan
    if not file_plan.courses:
        return db_plan
    if db_plan is not None and db_plan.source_hash == file_plan.source_hash:
        return db_plan
    return file_plan


def _update_stored_plan(store: KrsWarStore, plan: KrsPlan) -> None:
    now = datetime.now(UTC).isoformat()
    with connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO krs_war_state(owner_scope, armed, updated_at) "
            "VALUES(?, 0, ?)",
            (store.owner_scope, now),
        )
        conn.execute(
            """
            UPDATE krs_war_state
            SET plan_hash = ?, plan_json = ?, updated_at = ?
            WHERE owner_scope = ?
            """,
            (plan.source_hash, plan_to_json(plan), now, store.owner_scope),
        )


def _clean_text(element) -> str:
    return re.sub(r"\s+", " ", element.get_text(" ") or "").strip()


def _take_link_score(url: str) -> int:
    if _TAKE_BONUS_RE.search(url):
        return 2
    if _TAKE_PENALTY_RE.search(url):
        return 0
    return 1


def _nearest_take_url(element, base_url: str) -> str:
    best = ""
    best_score = -1
    node = element
    for _depth in range(6):
        if node is None:
            break
        candidates = []
        if node.name in {"a", "form"}:
            candidates.append(node)
        for child in node.select("a[href], form[action]"):
            candidates.append(child)
        for candidate in candidates:
            url = candidate.get("href") or candidate.get("action") or ""
            if not _TAKE_LINK_RE.search(url):
                continue
            score = _take_link_score(url)
            if score > best_score:
                best = url
                best_score = score
        if best:
            break
        node = node.parent
    return urljoin(base_url, best) if best else ""


def _extract_take_targets(html: str, base_url: str) -> dict[str, str]:
    soup = BeautifulSoup(html or "", "lxml")
    results: dict[str, str] = {}
    for cell in soup.select("td, th, li, span, div, p"):
        text = _clean_text(cell)
        if not _CODE_RE.fullmatch(text) or text in results:
            continue
        url = _nearest_take_url(cell, base_url)
        if url:
            results[text] = url
    return results


async def _discover_panel_endpoint(page) -> str | None:
    try:
        candidates = await page.evaluate(PANEL_ENDPOINTS_SCRIPT)
    except Exception as exc:
        logger.warning("KRS panel endpoint discovery failed: %s", exc)
        return None
    if not isinstance(candidates, list):
        return None
    settings = get_settings()
    seen: set[str] = set()
    display: list[str] = []
    for item in candidates:
        raw = str(item).strip()
        if not raw or "dilihat" in raw or "cetak" in raw:
            continue
        if _MUTATION_RE.search(raw):
            continue
        url = urljoin(settings.CYBER_CAMPUS_BASE_URL, raw)
        if url in seen:
            continue
        seen.add(url)
        display.append(url)
    if not display:
        return None
    for url in display:
        if "penawaran" in url:
            return url
    return display[0]


async def _discover_with_strategy(page) -> tuple[dict[str, str], str]:
    settings = get_settings()
    try:
        direct = await page.evaluate(PENAWARAN_DISCOVER_SCRIPT)
    except Exception as exc:
        logger.warning("KRS penawaran DOM discovery failed: %s", exc)
        direct = None
    if isinstance(direct, dict):
        targets = {
            str(code): str(url) for code, url in direct.items() if url
        }
        if targets:
            return targets, "dom"
    endpoint = await _discover_panel_endpoint(page)
    if not endpoint:
        return {}, "none"
    try:
        html = await page.evaluate(
            PORTAL_READ_FETCH_SCRIPT,
            {"target": endpoint, "payload": {"aksi": "tampil"}},
        )
    except Exception as exc:
        logger.warning("KRS penawaran fragment fetch failed: %s", exc)
        return {}, "none"
    if looks_like_login(html):
        raise AcademicPortalReadError(
            "Session Cyber Campus kedaluwarsa. Jalankan /cyber-login."
        )
    targets = _extract_take_targets(html, settings.CYBER_CAMPUS_BASE_URL)
    return targets, ("fragment_bs4" if targets else "none")


async def discover_penawaran_targets(page) -> dict[str, str]:
    targets, _strategy = await _discover_with_strategy(page)
    return targets


def _with_class_param(url: str, class_code: str) -> str:
    parsed = urlsplit(url)
    pairs: list[tuple[str, str]] = []
    replaced = False
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key.casefold() in {"kelas", "class"}:
            pairs.append((key, class_code))
            replaced = True
        else:
            pairs.append((key, value))
    if not replaced:
        pairs.append(("kelas", class_code))
    return urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urlencode(pairs), parsed.fragment)
    )


async def _fetch_taken_map(page) -> dict[str, str]:
    krs_html = await page.evaluate(
        PORTAL_READ_FETCH_SCRIPT,
        {"target": "proses/_akademik-krs_dilihat.php", "payload": {"aksi": "tampil"}},
    )
    if looks_like_login(krs_html):
        raise AcademicPortalReadError(
            "Session Cyber Campus kedaluwarsa. Jalankan /cyber-login."
        )
    result = parse_current_krs_html(krs_html)
    return {entry.course_code: entry.class_code for entry in result.entries}


async def _post_form(page, endpoint: str, body: str) -> str:
    return await page.evaluate(
        PORTAL_POST_SCRIPT, {"endpoint": endpoint, "body": body}
    )


async def _fetch_sid(page) -> str:
    html = await page.content()
    match = _SID_RE.search(html)
    return match.group(1) if match else ""


async def _fetch_offers(page) -> dict[str, dict[str, tuple[str, str, bool]]]:
    html = await _post_form(page, "proses/_akademik-krs_ditambah.php", "aksi=tampil")
    if looks_like_login(html):
        raise AcademicPortalReadError(
            "Session Cyber Campus kedaluwarsa. Jalankan /cyber-login."
        )
    soup = BeautifulSoup(html or "", "lxml")
    offers: dict[str, dict[str, tuple[str, str, bool]]] = {}
    for tr in soup.select("tr"):
        tds = tr.find_all("td", recursive=False)
        if len(tds) < 4:
            continue
        code = tds[0].get_text(strip=True)
        if not _CODE_RE.fullmatch(code):
            continue
        kelas = tds[3].get_text(strip=True)
        if not _CLASS_RE.fullmatch(kelas):
            continue
        entry = offers.setdefault(code, {})
        button = tr.find("input")
        onclick = button.get("onclick", "") if button else ""
        match = _TAKE_ACTION_RE.search(onclick)
        if match:
            entry[kelas] = (match.group(1), match.group(2), True)
        else:
            entry.setdefault(kelas, ("", "", False))
    return offers


async def _fetch_droppable(page) -> dict[str, tuple[str, str]]:
    html = await _post_form(page, "proses/_akademik-krs_hapus.php", "aksi=tampil")
    if looks_like_login(html):
        raise AcademicPortalReadError(
            "Session Cyber Campus kedaluwarsa. Jalankan /cyber-login."
        )
    soup = BeautifulSoup(html or "", "lxml")
    droppable: dict[str, tuple[str, str]] = {}
    for tr in soup.select("tr"):
        cells = tr.find_all("td", recursive=False)
        if len(cells) < 4:
            continue
        code = ""
        kelas = ""
        for cell in cells:
            text = cell.get_text(strip=True)
            if not code and _CODE_RE.fullmatch(text):
                code = text
            if not kelas and _CLASS_RE.fullmatch(text):
                kelas = text
        if not code or not kelas:
            continue
        button = tr.find("input")
        onclick = button.get("onclick", "") if button else ""
        match = _DROP_ACTION_RE.search(onclick)
        if not match:
            continue
        droppable[code] = (kelas, match.group(1))
    return droppable


def _upgrade_cooldown_ok(store: KrsWarStore, window: str, code: str) -> bool:
    with connect() as conn:
        row = conn.execute(
            "SELECT created_at FROM krs_war_actions "
            "WHERE owner_scope = ? AND window = ? AND course_code = ? "
            "AND action = 'upgrade_attempt' ORDER BY created_at DESC LIMIT 1",
            (store.owner_scope, window, code),
        ).fetchone()
    if row is None or not row["created_at"]:
        return True
    try:
        last = datetime.fromisoformat(row["created_at"])
    except ValueError:
        return True
    return (datetime.now(UTC) - last).total_seconds() >= _UPGRADE_COOLDOWN_SECONDS


async def _reload_krs_page(page) -> None:
    settings = get_settings()
    response = await page.goto(
        urljoin(settings.CYBER_CAMPUS_BASE_URL, "/modul/mhs/akademik-krs.php"),
        wait_until="domcontentloaded",
        timeout=settings.CYBER_CAMPUS_LOGIN_TIMEOUT_MS,
    )
    page_html = await page.content()
    if not response or response.status >= 400 or looks_like_login(page_html):
        raise AcademicPortalReadError(
            "Session Cyber Campus kedaluwarsa. Jalankan /cyber-login."
        )


def _is_flexible_goal(course: KrsPlanCourse) -> bool:
    return course.target_class.startswith("BCDLITS")


def _classes_to_try(course: KrsPlanCourse) -> tuple[str, ...]:
    if _is_flexible_goal(course):
        ordered: list[str] = []
        for class_code in (course.target_class, *course.fallback_classes):
            if class_code in _BCD_SAFE_CLASSES and class_code not in ordered:
                ordered.append(class_code)
        for class_code in _BCD_SAFE_CLASSES:
            if class_code not in ordered:
                ordered.append(class_code)
        return tuple(ordered)
    ordered: list[str] = []
    for class_code in (course.target_class, *course.fallback_classes):
        if class_code and class_code not in ordered:
            ordered.append(class_code)
    return tuple(ordered)


async def _attempt_take(
    page,
    course: KrsPlanCourse,
    window: str,
    store: KrsWarStore,
    offers: dict[str, dict[str, tuple[str, str, bool]]],
    sid: str,
) -> tuple[bool, str]:
    course_offers = offers.get(course.code)
    if not course_offers:
        store.record_action(
            window, "verify_failed", course.code, course.target_class,
            detail="tidak tampil di penawaran",
        )
        return False, course.target_class
    for class_code in _classes_to_try(course):
        slot = course_offers.get(class_code)
        if not slot or not slot[2]:
            continue
        id_kelas, id_kur, _open = slot
        store.record_action(
            window, "take_attempt", course.code, class_code,
            detail=f"kelas={id_kelas} kur={id_kur}",
        )
        await _post_form(
            page,
            "proses/_akademik-krs_ditambah.php",
            f"aksi=input&kelas={id_kelas}&id_kur_mk={id_kur}&sid={sid}",
        )
        await _reload_krs_page(page)
        taken_map = await _fetch_taken_map(page)
        if course.code in taken_map:
            actual_class = taken_map[course.code] or class_code
            store.record_action(
                window, "taken", course.code, actual_class, detail="post_take"
            )
            return True, actual_class
    tried = ",".join(_classes_to_try(course))
    store.record_action(
        window,
        "verify_failed",
        course.code,
        course.target_class,
        detail=f"tidak terkonfirmasi di MK Terambil (coba: {tried})",
    )
    return False, course.target_class


def _build_summary(
    window: str,
    taken: list[dict],
    already_taken: list[str],
    skipped: list[dict],
) -> str:
    reasons: dict[str, int] = {}
    for item in skipped:
        reason = item["reason"]
        reasons[reason] = reasons.get(reason, 0) + 1
    parts = [
        f"taken={len(taken)}",
        f"already_taken={len(already_taken)}",
        f"skipped={len(skipped)}",
    ]
    for reason in sorted(reasons):
        parts.append(f"{reason}={reasons[reason]}")
    return f"KRS war {window}: " + ", ".join(parts)


async def take_krs_plan(
    plan: KrsPlan,
    window: str,
    dry_run: bool = False,
    store: KrsWarStore | None = None,
) -> dict:
    store = store or KrsWarStore()
    settings = get_settings()
    allowlist = plan.allowlist()
    taken: list[dict] = []
    already_taken: list[str] = []
    skipped: list[dict] = []
    playwright = None
    browser = None
    context = None
    try:
        state = SessionManager().load_storage_state("mahasiswa")
        if not state:
            raise AcademicPortalReadError("Session Cyber Campus belum tersedia.")
        from playwright.async_api import async_playwright

        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=settings.CYBER_CAMPUS_BROWSER_HEADLESS
        )
        context = await browser.new_context(storage_state=state)
        page = await context.new_page()
        base_url = settings.CYBER_CAMPUS_BASE_URL
        response = await page.goto(
            urljoin(base_url, "/modul/mhs/akademik-krs.php"),
            wait_until="domcontentloaded",
            timeout=settings.CYBER_CAMPUS_LOGIN_TIMEOUT_MS,
        )
        page_html = await page.content()
        if not response or response.status >= 400 or looks_like_login(page_html):
            raise AcademicPortalReadError(
                "Session Cyber Campus kedaluwarsa. Jalankan /cyber-login."
            )
        store.record_action(
            window,
            "take_started",
            detail=(
                f"dry_run={'yes' if dry_run else 'no'}, "
                f"courses={len(plan.courses)}"
            ),
        )
        taken_before = await _fetch_taken_map(page)
        offers = await _fetch_offers(page)
        droppable = await _fetch_droppable(page)
        sid = await _fetch_sid(page)
        upgrade_pending: list[str] = []
        lost: list[str] = []
        for course in plan.courses:
            current_class = taken_before.get(course.code)
            if course.code not in allowlist:
                skipped.append({"code": course.code, "reason": "not in allowlist"})
                store.record_action(
                    window, "take_skipped", course.code, detail="not in allowlist"
                )
                continue
            if current_class:
                desired = _classes_to_try(course)
                if desired and desired[0] == current_class:
                    already_taken.append(course.code)
                    store.record_action(
                        window, "take_skipped", course.code, detail="already_taken"
                    )
                    continue
                if _is_flexible_goal(course):
                    already_taken.append(course.code)
                    store.record_action(
                        window,
                        "take_skipped",
                        course.code,
                        current_class,
                        detail="already_taken flexible",
                    )
                    continue
                if dry_run:
                    store.record_action(
                        window,
                        "take_started",
                        course.code,
                        desired[0] if desired else course.target_class,
                        detail="upgrade dry_run",
                    )
                    upgrade_pending.append(course.code)
                    continue
                goal_slot = (offers.get(course.code) or {}).get(course.target_class)
                if not goal_slot or not goal_slot[2]:
                    upgrade_pending.append(course.code)
                    store.record_action(
                        window,
                        "take_skipped",
                        course.code,
                        current_class,
                        detail="upgrade_pending goal tidak terlihat/open",
                    )
                    continue
                drop_id = (droppable.get(course.code) or (None, None))[1]
                if not drop_id:
                    upgrade_pending.append(course.code)
                    store.record_action(
                        window,
                        "take_skipped",
                        course.code,
                        current_class,
                        detail="upgrade_pending drop id tidak ditemukan",
                    )
                    continue
                if not _upgrade_cooldown_ok(store, window, course.code):
                    upgrade_pending.append(course.code)
                    store.record_action(
                        window,
                        "take_skipped",
                        course.code,
                        current_class,
                        detail="upgrade_pending cooldown",
                    )
                    continue
                store.record_action(
                    window, "upgrade_attempt", course.code, course.target_class
                )
                await _post_form(
                    page,
                    "proses/_akademik-krs_hapus.php",
                    f"aksi=hapus&pengambilan_mk={drop_id}",
                )
                await _reload_krs_page(page)
                fresh_offers = await _fetch_offers(page)
                fresh_goal = (fresh_offers.get(course.code) or {}).get(
                    course.target_class
                )
                if fresh_goal and fresh_goal[2]:
                    await _post_form(
                        page,
                        "proses/_akademik-krs_ditambah.php",
                        f"aksi=input&kelas={fresh_goal[0]}&id_kur_mk={fresh_goal[1]}&sid={sid}",
                    )
                    await _reload_krs_page(page)
                    taken_map = await _fetch_taken_map(page)
                    if course.code in taken_map:
                        actual_class = taken_map[course.code] or course.target_class
                        taken.append(
                            {"code": course.code, "class": actual_class, "upgraded": True}
                        )
                        store.record_action(
                            window, "taken", course.code, actual_class, detail="upgraded"
                        )
                        continue
                back_slot = (fresh_offers.get(course.code) or {}).get(current_class)
                if back_slot and back_slot[2]:
                    await _post_form(
                        page,
                        "proses/_akademik-krs_ditambah.php",
                        f"aksi=input&kelas={back_slot[0]}&id_kur_mk={back_slot[1]}&sid={sid}",
                    )
                    await _reload_krs_page(page)
                    taken_map = await _fetch_taken_map(page)
                    if course.code in taken_map:
                        already_taken.append(course.code)
                        store.record_action(
                            window,
                            "take_skipped",
                            course.code,
                            taken_map[course.code] or current_class,
                            detail="upgrade_rolled_back",
                        )
                        continue
                lost.append(course.code)
                store.record_action(
                    window,
                    "verify_failed",
                    course.code,
                    current_class,
                    detail="upgrade_lost MK tidak kembali",
                )
                continue
            take_url = offers.get(course.code)
            if not take_url:
                skipped.append({"code": course.code, "reason": "kelas penuh/tersembunyi"})
                store.record_action(
                    window,
                    "take_skipped",
                    course.code,
                    course.target_class,
                    detail="target not found",
                )
                continue
            if dry_run:
                store.record_action(
                    window,
                    "take_started",
                    course.code,
                    course.target_class,
                    detail="dry_run",
                )
                continue
            try:
                taken_ok, actual_class = await _attempt_take(
                    page, course, window, store, offers, sid
                )
            except AcademicPortalReadError as exc:
                if "kedaluwarsa" in str(exc):
                    raise
                skipped.append({"code": course.code, "reason": f"take gagal: {exc}"})
                store.record_action(
                    window,
                    "verify_failed",
                    course.code,
                    course.target_class,
                    detail=str(exc),
                )
            except Exception as exc:
                skipped.append({"code": course.code, "reason": f"take gagal: {exc}"})
                store.record_action(
                    window,
                    "verify_failed",
                    course.code,
                    course.target_class,
                    detail=str(exc),
                )
            else:
                if taken_ok:
                    taken.append({"code": course.code, "class": actual_class})
                else:
                    skipped.append({"code": course.code, "reason": "verify failed"})
        final_taken_codes: list[str] = []
        try:
            await _reload_krs_page(page)
            final_taken_codes = sorted(await _fetch_taken_map(page))
        except Exception as exc:
            logger.warning("KRS war final verification failed: %s", exc)
            store.record_action(
                window,
                "verify_failed",
                detail=f"final verification: {exc}",
            )
        plan_codes = {course.code for course in plan.courses}
        remaining = sorted(
            (plan_codes - set(final_taken_codes)) | set(upgrade_pending)
        )
        return {
            "window": window,
            "status": "done" if not remaining else "partial",
            "taken": taken,
            "already_taken": already_taken,
            "skipped": skipped,
            "upgrade_pending": upgrade_pending,
            "lost": lost,
            "remaining": remaining,
            "final_taken_codes": final_taken_codes,
            "dry_run": dry_run,
            "strategy": "post",
            "summary": _build_summary(window, taken, already_taken, skipped),
        }
    finally:
        if context is not None:
            await context.close()
        if browser is not None:
            await browser.close()
        if playwright is not None:
            await playwright.stop()


async def calibrate_penawaran(page) -> dict:
    targets, strategy = await _discover_with_strategy(page)
    return {"targets": targets, "strategy": strategy, "count": len(targets)}


async def _open_krs_page() -> tuple[Any, Any, Any, Any]:
    settings = get_settings()
    state = SessionManager().load_storage_state("mahasiswa")
    if not state:
        raise AcademicPortalReadError("Session Cyber Campus belum tersedia.")
    from playwright.async_api import async_playwright

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=settings.CYBER_CAMPUS_BROWSER_HEADLESS
    )
    context = await browser.new_context(storage_state=state)
    page = await context.new_page()
    return playwright, browser, context, page


async def auto_calibrate_if_needed(
    announcement: KrsAnnouncement | None = None,
    now: datetime | None = None,
    store: KrsWarCalibrationStore | None = None,
) -> dict:
    if announcement is None:
        return {"calibration": {"skipped": "no_window"}}
    store = store or KrsWarCalibrationStore()
    window_key = f"{announcement.period_start}|{announcement.period_end}"
    existing = store.get(window_key)
    if existing and existing["target_count"] > 0:
        return {
            "calibration": {
                "skipped": "already_calibrated",
                "window": window_key,
                "strategy": existing["strategy"],
                "target_count": existing["target_count"],
            }
        }
    if existing and existing["attempts"] >= 8:
        return {
            "calibration": {
                "skipped": "max_attempts",
                "window": window_key,
                "attempts": existing["attempts"],
            }
        }
    attempt_count = (existing["attempts"] if existing else 0) + 1
    settings = get_settings()
    playwright = None
    browser = None
    context = None
    try:
        playwright, browser, context, page = await _open_krs_page()
        response = await page.goto(
            urljoin(settings.CYBER_CAMPUS_BASE_URL, "/modul/mhs/akademik-krs.php"),
            wait_until="domcontentloaded",
            timeout=settings.CYBER_CAMPUS_LOGIN_TIMEOUT_MS,
        )
        page_html = await page.content()
        if not response or response.status >= 400 or looks_like_login(page_html):
            raise AcademicPortalReadError(
                "Session Cyber Campus kedaluwarsa. Jalankan /cyber-login."
            )
        calibrated = await calibrate_penawaran(page)
        targets = calibrated["targets"]
        strategy = calibrated["strategy"]
        count = calibrated["count"]
    except AcademicPortalReadError as exc:
        if "kedaluwarsa" in str(exc):
            store.save(window_key, {}, "none", "error", attempt_count)
        logger.warning("KRS war calibration failed: %s", exc)
        return {"calibration": {"status": "error", "error": str(exc)}}
    except Exception as exc:
        logger.warning("KRS war calibration failed: %s", exc)
        return {"calibration": {"status": "error", "error": str(exc)}}
    finally:
        if context is not None:
            await context.close()
        if browser is not None:
            await browser.close()
        if playwright is not None:
            await playwright.stop()
    status = "ok" if count > 0 else "empty"
    store.save(window_key, targets, strategy, status, attempt_count)
    if status == "ok" and (existing is None or existing["status"] != "ok"):
        await notify_admin(
            "krs_war_calibrated",
            {
                "window": window_key,
                "strategy": strategy,
                "target_count": count,
                "status": status,
            },
            impact="high",
        )
    return {
        "calibration": {
            "window": window_key,
            "status": status,
            "strategy": strategy,
            "target_count": count,
            "attempts": attempt_count,
        }
    }


async def _append_war_log(
    vault_service: ObsidianVaultService | None,
    result: dict,
    window: str,
    now: datetime | None,
) -> str | None:
    try:
        vault = vault_service or ObsidianVaultService()
        timestamp = (now or datetime.now(UTC)).isoformat()
        taken_codes = ", ".join(item["code"] for item in result["taken"]) or "-"
        already_codes = ", ".join(result["already_taken"]) or "-"
        skipped_codes = ", ".join(item["code"] for item in result["skipped"]) or "-"
        content = (
            f"## KRS War — {window}\n\n"
            f"- Timestamp: {timestamp}\n"
            f"- Status: {result.get('status')}\n"
            f"- Taken: {taken_codes}\n"
            f"- Already taken: {already_codes}\n"
            f"- Skipped: {skipped_codes}\n"
            f"- Summary: {result.get('summary')}"
        )
        vault.append_note(KRS_WAR_LOG_PATH, content)
        return None
    except Exception as exc:
        logger.warning("KRS war log append failed: %s", exc)
        return str(exc)


async def run_krs_war_if_armed(
    now: datetime | None = None,
    announcement: KrsAnnouncement | None = None,
    vault_service: ObsidianVaultService | None = None,
    store: KrsWarStore | None = None,
    kprs_opened: bool = False,
) -> dict:
    store = store or KrsWarStore()
    state = store.get()
    if not state["armed"]:
        return {"war": {"skipped": "not_armed"}}
    if announcement is None and not kprs_opened:
        return {"war": {"skipped": "no_window"}}
    if announcement is not None:
        window_key = f"{announcement.period_start}|{announcement.period_end}"
    else:
        window_key = (
            state["last_run_window"]
            or f"{datetime.now(UTC).date().isoformat()}|{datetime.now(UTC).date().isoformat()}"
        )
    if state["last_run_window"] == window_key and state["last_status"] == "done":
        return {"war": {"skipped": "already_run", "window": window_key}}
    first_run_for_window = state["last_run_window"] != window_key
    plan = await load_krs_plan(vault_service=vault_service, store=store)
    if plan is None:
        store.record_action(window_key, "run_error", detail="plan tidak tersedia")
        store.update_run(
            window=window_key, status="error", summary="plan tidak tersedia"
        )
        if first_run_for_window or state["last_status"] != "error":
            await notify_admin(
                "krs_war_error",
                {"window": window_key, "detail": "plan tidak tersedia"},
                impact="high",
            )
        return {"war": {"skipped": "no_plan"}}
    if state.get("plan_hash") != plan.source_hash:
        _update_stored_plan(store, plan)
    store.record_action(
        window_key, "window_detected", detail=f"courses={len(plan.courses)}"
    )
    store.record_action(
        window_key,
        "plan_loaded",
        detail=f"hash={plan.source_hash[:12]}, semester={plan.semester_label}",
    )
    if first_run_for_window:
        await notify_admin(
            "krs_war_started",
            {
                "window": window_key,
                "courses": len(plan.courses),
                "semester": plan.semester_label,
            },
            impact="high",
        )
    try:
        result = await take_krs_plan(plan, window_key, store=store)
        if "remaining" in result:
            remaining = result["remaining"] or []
        else:
            retryable_skips = any(
                item["reason"] in {"target not found", "verify failed", "kelas penuh/tersembunyi"}
                or str(item["reason"]).startswith("take gagal")
                for item in result.get("skipped", [])
            )
            remaining = (
                result.get("upgrade_pending")
                or (["__retry__"] if retryable_skips else [])
            )
        status = "partial" if remaining else "done"
        store.record_action(window_key, "run_done", detail=result["summary"])
        store.update_run(window=window_key, status=status, summary=result["summary"])
        if first_run_for_window or state["last_status"] != status:
            await notify_admin(
                "krs_war_taken",
                {
                    "window": window_key,
                    "taken": len(result["taken"]),
                    "already_taken": len(result["already_taken"]),
                    "skipped": len(result["skipped"]),
                    "upgrade_pending": result.get("upgrade_pending"),
                    "lost": result.get("lost"),
                    "remaining": remaining,
                    "summary": result["summary"],
                },
                impact="high",
            )
        log_error = await _append_war_log(vault_service, result, window_key, now)
        war = dict(result)
        if log_error:
            war["log_error"] = log_error
        return {"war": war}
    except Exception as exc:
        message = str(exc)
        store.record_action(window_key, "run_error", detail=message)
        store.update_run(window=window_key, status="error", summary=message)
        if first_run_for_window or state["last_status"] != "error":
            await notify_admin(
                "krs_war_error",
                {"window": window_key, "error": message},
                impact="high",
            )
        return {"war": {"status": "error", "error": message}}


async def krs_war_status_text() -> str:
    state = KrsWarStore().get()
    lines = [
        "KRS War status:",
        f"- Armed: {'yes' if state['armed'] else 'no'}",
        f"- Plan hash: {state['plan_hash'] or '-'}",
        f"- Last run window: {state['last_run_window'] or '-'}",
        f"- Last status: {state['last_status'] or 'idle'}",
        f"- Last summary: {state['last_summary'] or '-'}",
    ]
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM krs_war_calibration ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
    if row is not None:
        cal = dict(row)
        lines.append(f"- Calibration window: {cal['window']}")
        lines.append(
            f"- Calibration strategy: {cal['strategy']} / targets: {cal['target_count']}"
        )
        lines.append(f"- Calibration attempts: {cal['attempts']}")
    return "\n".join(lines)
