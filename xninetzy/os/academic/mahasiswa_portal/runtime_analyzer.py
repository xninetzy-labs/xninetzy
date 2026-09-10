from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlsplit, urlunsplit

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.web_analysis.session_manager import SessionManager
from app.xninetzy.os.web_analysis.sites import get_site, is_allowed_url


_PHP_TARGET = re.compile(r"(?:[A-Za-z0-9_./-]+/)?[A-Za-z0-9_-]+\.php", re.I)
_WRITE_MARKERS = (
    "submit",
    "simpan",
    "hapus",
    "delete",
    "remove",
    "final",
    "proses/",
    "logout",
)
_KRS_MARKERS = ("krs", "kprs", "rencana studi", "mata kuliah")


@dataclass(frozen=True, slots=True)
class NavigationItem:
    label: str
    path: str
    source: str
    policy: str


@dataclass(slots=True)
class RuntimeManifest:
    landing_path: str
    navigation: list[NavigationItem] = field(default_factory=list)
    krs_tabs: list[str] = field(default_factory=list)
    form_methods: list[str] = field(default_factory=list)
    field_names: list[str] = field(default_factory=list)
    internal_targets: list[str] = field(default_factory=list)
    write_controls_present: bool = False
    verified_paths: list[str] = field(default_factory=list)
    unreachable_paths: list[str] = field(default_factory=list)
    structure_hash: str = ""


def extract_php_targets(value: str) -> list[str]:
    return sorted(set(_PHP_TARGET.findall(value or "")))


def classify_navigation(path: str, label: str = "") -> str:
    value = f"{path} {label}".casefold()
    if any(marker in value for marker in _WRITE_MARKERS):
        return "blocked_write"
    if any(marker in value for marker in _KRS_MARKERS):
        return "krs_guarded"
    return "read_only"


class PortalRuntimeAnalyzer:
    async def inspect(self, verify_navigation: bool = False) -> RuntimeManifest:
        state = SessionManager().load_storage_state("mahasiswa")
        landing = SessionManager().load_landing_url("mahasiswa")
        if not state or not landing:
            raise RuntimeError("Session Cyber Campus belum tersedia.")

        from playwright.async_api import async_playwright

        settings = get_settings()
        site = get_site("mahasiswa")
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=settings.CYBER_CAMPUS_BROWSER_HEADLESS
            )
            try:
                context = await browser.new_context(storage_state=state)

                async def guard(route) -> None:
                    if (
                        route.request.method in {"GET", "HEAD"}
                        and is_allowed_url(site, route.request.url)
                    ):
                        await route.continue_()
                    else:
                        await route.abort("blockedbyclient")

                await context.route("**/*", guard)
                page = await context.new_page()
                await page.goto(
                    landing,
                    wait_until="domcontentloaded",
                    timeout=settings.WEB_ANALYSIS_TIMEOUT_MS,
                )
                await page.wait_for_timeout(
                    max(500, int(settings.WEB_ANALYSIS_REQUEST_DELAY_SECONDS * 1000))
                )
                navigation = await self._navigation(page, site.base_url)
                krs = await self._inspect_krs(page, site.base_url)
                if verify_navigation:
                    verified, unreachable = await self._verify_navigation(
                        page,
                        navigation,
                        site.base_url,
                    )
                else:
                    verified, unreachable = [], []
            finally:
                await browser.close()

        manifest = RuntimeManifest(
            landing_path=urlsplit(landing).path or "/",
            navigation=navigation,
            krs_tabs=krs["tabs"],
            form_methods=krs["form_methods"],
            field_names=krs["field_names"],
            internal_targets=krs["internal_targets"],
            write_controls_present=krs["write_controls_present"],
            verified_paths=verified,
            unreachable_paths=unreachable,
        )
        manifest.structure_hash = self._hash(manifest)
        return manifest

    async def _verify_navigation(
        self,
        page,
        navigation: list[NavigationItem],
        base_url: str,
    ) -> tuple[list[str], list[str]]:
        site = get_site("mahasiswa")
        verified: list[str] = []
        unreachable: list[str] = []
        for item in navigation:
            if item.policy == "blocked_write":
                continue
            target = urljoin(base_url.rstrip("/") + "/", item.path.lstrip("/"))
            try:
                response = await page.goto(
                    target,
                    wait_until="domcontentloaded",
                    timeout=get_settings().WEB_ANALYSIS_TIMEOUT_MS,
                )
                if (
                    response
                    and 200 <= response.status < 400
                    and is_allowed_url(site, page.url)
                ):
                    verified.append(item.path)
                else:
                    unreachable.append(item.path)
            except Exception:
                unreachable.append(item.path)
        return sorted(set(verified)), sorted(set(unreachable))

    async def _navigation(self, page, base_url: str) -> list[NavigationItem]:
        site = get_site("mahasiswa")
        found: dict[tuple[str, str], NavigationItem] = {}
        for frame in page.frames:
            try:
                anchors = await frame.locator("a[href]").evaluate_all(
                    r"""
                    elements => elements.map(element => ({
                      label: (element.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 120),
                      href: element.href
                    }))
                    """
                )
                handlers = await frame.locator("[onclick]").evaluate_all(
                    r"""
                    elements => elements.map(element => ({
                      label: (element.textContent || element.value || '').trim().replace(/\s+/g, ' ').slice(0, 120),
                      handler: element.getAttribute('onclick') || ''
                    }))
                    """
                )
            except Exception:
                continue
            for item in anchors:
                self._add_navigation(
                    found,
                    site,
                    base_url,
                    str(item.get("href") or ""),
                    str(item.get("label") or ""),
                    "anchor",
                )
            for item in handlers:
                label = str(item.get("label") or "")
                for target in extract_php_targets(str(item.get("handler") or "")):
                    self._add_navigation(
                        found,
                        site,
                        base_url,
                        target,
                        label,
                        "handler",
                    )
        return sorted(found.values(), key=lambda item: (item.policy, item.path, item.label))

    def _add_navigation(
        self,
        found: dict[tuple[str, str], NavigationItem],
        site,
        base_url: str,
        target: str,
        label: str,
        source: str,
    ) -> None:
        absolute = urljoin(base_url.rstrip("/") + "/modul/mhs/", target)
        if not is_allowed_url(site, absolute):
            return
        parsed = urlsplit(absolute)
        path = urlunsplit(("", "", parsed.path or "/", "", ""))
        clean_label = re.sub(r"\s+", " ", label).strip()[:120]
        policy = classify_navigation(path, clean_label)
        found[(path, clean_label)] = NavigationItem(
            label=clean_label or path.rsplit("/", 1)[-1],
            path=path,
            source=source,
            policy=policy,
        )

    async def _inspect_krs(self, page, base_url: str) -> dict:
        target = urljoin(base_url.rstrip("/") + "/", "modul/mhs/akademik-krs.php")
        await page.goto(target, wait_until="domcontentloaded", timeout=30_000)
        controls = await page.locator("[onclick]").evaluate_all(
            r"""
            elements => elements.map(element => ({
              label: (element.textContent || element.value || '').trim().replace(/\s+/g, ' ').slice(0, 120),
              handler: element.getAttribute('onclick') || ''
            }))
            """
        )
        forms = await page.locator("form").evaluate_all(
            """
            elements => elements.map(form => ({
              method: (form.method || 'get').toUpperCase(),
              fields: [...form.elements].map(element => element.name).filter(Boolean)
            }))
            """
        )
        scripts = await page.locator("script:not([src])").all_text_contents()
        tabs: list[str] = []
        targets: set[str] = set()
        for control in controls:
            label = re.sub(r"\s+", " ", str(control.get("label") or "")).strip()
            if label and len(label) <= 80 and "function " not in label.casefold():
                tabs.append(label)
            targets.update(extract_php_targets(str(control.get("handler") or "")))
        for script in scripts:
            targets.update(extract_php_targets(script))
        methods = sorted({str(form.get("method") or "GET") for form in forms})
        fields = sorted(
            {
                str(name)
                for form in forms
                for name in form.get("fields", [])
                if re.fullmatch(r"[A-Za-z][A-Za-z0-9_.:\[\]-]{0,79}", str(name))
            }
        )
        selectable = await page.locator(
            "input[type=checkbox],input[type=radio],select,button,input[type=submit]"
        ).count()
        return {
            "tabs": sorted(set(tabs)),
            "form_methods": methods,
            "field_names": fields,
            "internal_targets": sorted(targets),
            "write_controls_present": bool(selectable or any(m != "GET" for m in methods)),
        }

    @staticmethod
    def _hash(manifest: RuntimeManifest) -> str:
        payload = {
            "landing_path": manifest.landing_path,
            "navigation": [
                {
                    "label": item.label,
                    "path": item.path,
                    "source": item.source,
                    "policy": item.policy,
                }
                for item in manifest.navigation
            ],
            "krs_tabs": manifest.krs_tabs,
            "form_methods": manifest.form_methods,
            "field_names": manifest.field_names,
            "internal_targets": manifest.internal_targets,
            "write_controls_present": manifest.write_controls_present,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
