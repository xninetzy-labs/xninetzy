from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.web_analysis.security import looks_like_login
from app.xninetzy.os.web_analysis.session_manager import SessionManager


class AcademicPortalReadError(RuntimeError):
    pass


class GradeTokenRejected(AcademicPortalReadError):
    pass


GRADE_FETCH_SCRIPT = """
async ({period, token}) => {
  const body = new URLSearchParams({aksi: "tampil", semes: period, token});
  const response = await fetch("/modul/mhs/proses/_akademik-khs-tampil.php", {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
      "X-Requested-With": "XMLHttpRequest"
    },
    body: body.toString()
  });
  if (!response.ok) throw new Error(`KHS endpoint ${response.status}`);
  return await response.text();
}
"""


@dataclass(frozen=True, slots=True)
class ScheduleEntry:
    course: str
    credits: str
    class_code: str
    schedule: str
    room: str
    lecturers: str


@dataclass(frozen=True, slots=True)
class ScheduleResult:
    period: str
    entries: tuple[ScheduleEntry, ...]


@dataclass(frozen=True, slots=True)
class GradeEntry:
    values: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class GradeResult:
    period: str
    entries: tuple[GradeEntry, ...]


@dataclass(frozen=True, slots=True)
class AcademicPeriod:
    value: str
    label: str


@dataclass(slots=True)
class PreparedGradeRequest:
    challenge_id: str
    period: AcademicPeriod
    playwright: Any
    browser: Any
    context: Any
    page: Any
    expiry_handle: asyncio.TimerHandle | None = None


def _text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _table_rows(html: str) -> list[tuple[list[str], list[list[str]]]]:
    soup = BeautifulSoup(html or "", "lxml")
    tables: list[tuple[list[str], list[list[str]]]] = []
    for table in soup.select("table"):
        rows = table.select("tr")
        if not rows:
            continue
        headers = [_text(cell.get_text(" ")) for cell in rows[0].select("th,td")]
        body = [
            [_text(cell.get_text(" ")) for cell in row.select("th,td")]
            for row in rows[1:]
        ]
        body = [row for row in body if any(row)]
        tables.append((headers, body))
    return tables


def parse_schedule_html(html: str) -> ScheduleResult:
    soup = BeautifulSoup(html or "", "lxml")
    heading = soup.find(
        lambda tag: tag.name in {"h1", "h2", "h3", "h4"}
        and "jadwal" in _text(tag.get_text(" ")).casefold()
    )
    period = _text(heading.get_text(" ")) if heading else "Jadwal aktif"
    expected = ("mata ajar", "sks", "kelas", "jadwal", "ruang", "petugas")
    for headers, rows in _table_rows(html):
        normalized = tuple(value.casefold() for value in headers[:6])
        if normalized != expected:
            continue
        entries = tuple(
            ScheduleEntry(*((row + [""] * 6)[:6]))
            for row in rows
            if len(row) >= 4
        )
        return ScheduleResult(period=period, entries=entries)
    raise AcademicPortalReadError("Tabel jadwal tidak ditemukan dalam struktur portal.")


def parse_grade_html(html: str, period: str) -> GradeResult:
    grade_markers = (
        "nilai",
        "huruf",
        "bobot",
        "mutu",
        "grade",
        "indeks",
        "kredit",
        "kode",
        "nama",
        "mata ajar",
        "mata kuliah",
        "sks",
    )
    soup = BeautifulSoup(html or "", "lxml")
    for table in soup.select("table"):
        rows = [
            [_text(cell.get_text(" ")) for cell in row.select("th,td")]
            for row in table.select("tr")
        ]
        rows = [row for row in rows if any(row)]
        for header_index, headers in enumerate(rows):
            normalized = [header.casefold() for header in headers]
            marker_count = sum(
                1
                for header in normalized
                if any(marker in header for marker in grade_markers)
            )
            if len(headers) < 3 or marker_count < 2:
                continue
            body = [
                row
                for row in rows[header_index + 1 :]
                if len(row) >= 2 and row != headers
            ]
            entries = tuple(
                GradeEntry(
                    values=tuple(
                        (header or f"Kolom {index + 1}", value)
                        for index, (header, value) in enumerate(
                            zip(
                                headers,
                                (row + [""] * len(headers))[: len(headers)],
                            ),
                            start=0,
                        )
                    )
                )
                for row in body
            )
            if entries:
                return GradeResult(period=period, entries=entries)
    soup = BeautifulSoup(html or "", "lxml")
    alert_messages = []
    for script in soup.select("script"):
        script_text = script.get_text(" ") or script.string or ""
        alert_messages.extend(
            re.findall(
                r"alert\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
                script_text,
                flags=re.IGNORECASE,
            )
        )
    visible_message = _text(soup.get_text(" "))
    message = _text(" ".join([*alert_messages, visible_message]))
    if message:
        safe_message = re.sub(r"\b\d{4,10}\b", "[angka]", message)
        raise GradeTokenRejected(f"Respons portal: {safe_message[:240]}")
    table_count = len(soup.select("table"))
    if table_count:
        raise GradeTokenRejected(
            f"Struktur KHS berubah: {table_count} tabel tidak dikenali."
        )
    raise GradeTokenRejected("Portal tidak mengembalikan data KHS.")


def validate_grade_token_page(html: str) -> None:
    soup = BeautifulSoup(html or "", "lxml")
    token_input = soup.select_one("input[name=token]")
    page_text = _text(soup.get_text(" ")).casefold()
    if token_input is None or "telegram" not in page_text or "token" not in page_text:
        raise AcademicPortalReadError(
            "Halaman permintaan token KHS tidak dikenali."
        )


def select_academic_period(
    options: list[dict[str, Any]], requested: str, entry_year: int = 0
) -> AcademicPeriod:
    available = [
        AcademicPeriod(
            value=_text(item.get("value")),
            label=_text(item.get("label")),
        )
        for item in options
        if _text(item.get("value")) not in {"", "0"}
    ]
    if not available:
        raise AcademicPortalReadError("Periode KHS tidak tersedia.")
    query = _text(requested).casefold()
    if not query or query == "latest":
        return available[0]
    semester_match = re.fullmatch(r"(?:semester|sem)\s*(\d{1,2})", query)
    if semester_match:
        semester = int(semester_match.group(1))
        if semester < 1 or not 2000 <= entry_year <= 2100:
            raise AcademicPortalReadError(
                "Alias semester membutuhkan CYBER_CAMPUS_ENTRY_YEAR yang valid."
            )
        academic_start = entry_year + (semester - 1) // 2
        academic_year = f"{academic_start}/{academic_start + 1}"
        term = "ganjil" if semester % 2 else "genap"
        semester_periods = [
            item
            for item in available
            if academic_year in item.label and term in item.label.casefold()
        ]
        if len(semester_periods) == 1:
            return semester_periods[0]
        raise AcademicPortalReadError(
            f"Periode untuk semester {semester} tidak tersedia."
        )
    exact = [
        item
        for item in available
        if query in {item.value.casefold(), item.label.casefold()}
    ]
    if len(exact) == 1:
        return exact[0]
    partial = [item for item in available if query in item.label.casefold()]
    if len(partial) == 1:
        return partial[0]
    raise AcademicPortalReadError(
        "Periode KHS tidak dikenali. Gunakan /nilai latest atau /nilai <kode-periode>."
    )


class AcademicPortalReader:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._prepared_grade_requests: dict[str, PreparedGradeRequest] = {}
        self._grade_lock = asyncio.Lock()

    def _entry_year(self) -> int:
        configured = self.settings.CYBER_CAMPUS_ENTRY_YEAR
        if 2000 <= configured <= 2100:
            return configured
        match = re.fullmatch(r"\d{3}(\d{2})\d+", self.settings.HEBAT_USERNAME)
        return 2000 + int(match.group(1)) if match else 0

    async def _browser(self):
        state = SessionManager().load_storage_state("mahasiswa")
        if not state:
            raise AcademicPortalReadError("Session Cyber Campus belum tersedia.")
        from playwright.async_api import async_playwright

        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=self.settings.CYBER_CAMPUS_BROWSER_HEADLESS
        )
        context = await browser.new_context(storage_state=state)
        return playwright, browser, context

    async def read_schedule(self) -> ScheduleResult:
        playwright, browser, context = await self._browser()
        try:
            page = await context.new_page()
            target = urljoin(
                self.settings.CYBER_CAMPUS_BASE_URL,
                "/modul/mhs/akademik-jadwal.php",
            )
            response = await page.goto(
                target,
                wait_until="domcontentloaded",
                timeout=self.settings.CYBER_CAMPUS_LOGIN_TIMEOUT_MS,
            )
            html = await page.content()
            if not response or response.status >= 400 or looks_like_login(html):
                raise AcademicPortalReadError(
                    "Session Cyber Campus kedaluwarsa. Jalankan /cyber-login."
                )
            return parse_schedule_html(html)
        finally:
            await context.close()
            await browser.close()
            await playwright.stop()

    async def read_grades(
        self,
        token: str,
        academic_period: str = "latest",
        challenge_id: str = "",
    ) -> GradeResult:
        clean_token = token.strip()
        if not re.fullmatch(r"\d{4,10}", clean_token):
            raise GradeTokenRejected("Format token nilai tidak valid.")
        if not challenge_id:
            raise GradeTokenRejected("Challenge token nilai tidak tersedia.")
        async with self._grade_lock:
            prepared = self._prepared_grade_requests.get(challenge_id)
        if prepared is None:
            raise GradeTokenRejected(
                "Session permintaan token nilai tidak ditemukan atau kedaluwarsa."
            )
        try:
            await prepared.page.locator("input[name=token]").fill(clean_token)
            await prepared.page.locator(
                "select[name=thn_akademik]"
            ).evaluate(
                "(element, value) => { element.value = value; }",
                prepared.period.value,
            )
            result_html = await prepared.page.evaluate(
                GRADE_FETCH_SCRIPT,
                {
                    "period": prepared.period.value,
                    "token": clean_token,
                },
            )
            if looks_like_login(result_html):
                raise AcademicPortalReadError(
                    "Session Cyber Campus kedaluwarsa. Jalankan /cyber-login."
                )
            return parse_grade_html(result_html, prepared.period.label)
        finally:
            clean_token = ""
            await self.cancel_grade_request(challenge_id)

    async def prepare_grade_request(
        self, challenge_id: str, academic_period: str = "latest"
    ) -> AcademicPeriod:
        await self.cancel_all_grade_requests()
        playwright, browser, context = await self._browser()
        try:
            page = await context.new_page()
            target = urljoin(
                self.settings.CYBER_CAMPUS_BASE_URL,
                "/modul/mhs/akademik-khs.php",
            )
            response = await page.goto(
                target,
                wait_until="domcontentloaded",
                timeout=self.settings.CYBER_CAMPUS_LOGIN_TIMEOUT_MS,
            )
            html = await page.content()
            if not response or response.status >= 400 or looks_like_login(html):
                raise AcademicPortalReadError(
                    "Session Cyber Campus kedaluwarsa. Jalankan /cyber-login."
                )
            validate_grade_token_page(html)
            options = await page.locator(
                "select[name=thn_akademik] option"
            ).evaluate_all(
                "els => els.map(option => ({value: option.value, label: (option.textContent || '').trim()}))"
            )
            selected = select_academic_period(
                options,
                academic_period,
                self._entry_year(),
            )
            prepared = PreparedGradeRequest(
                challenge_id=challenge_id,
                period=selected,
                playwright=playwright,
                browser=browser,
                context=context,
                page=page,
            )
            loop = asyncio.get_running_loop()
            prepared.expiry_handle = loop.call_later(
                self.settings.CYBER_CAMPUS_GRADE_TOKEN_TTL_SECONDS,
                self._schedule_grade_request_cleanup,
                challenge_id,
            )
            async with self._grade_lock:
                self._prepared_grade_requests[challenge_id] = prepared
            return selected
        except Exception:
            await context.close()
            await browser.close()
            await playwright.stop()
            raise

    def _schedule_grade_request_cleanup(self, challenge_id: str) -> None:
        task = asyncio.create_task(self.cancel_grade_request(challenge_id))
        task.add_done_callback(lambda completed: completed.exception())

    async def cancel_grade_request(self, challenge_id: str) -> None:
        async with self._grade_lock:
            prepared = self._prepared_grade_requests.pop(challenge_id, None)
        if prepared is None:
            return
        if prepared.expiry_handle:
            prepared.expiry_handle.cancel()
        await prepared.context.close()
        await prepared.browser.close()
        await prepared.playwright.stop()

    async def cancel_all_grade_requests(self) -> None:
        async with self._grade_lock:
            challenge_ids = tuple(self._prepared_grade_requests)
        for challenge_id in challenge_ids:
            await self.cancel_grade_request(challenge_id)


ACADEMIC_PORTAL_READER = AcademicPortalReader()
