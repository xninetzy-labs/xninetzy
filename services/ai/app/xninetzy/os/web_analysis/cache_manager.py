from __future__ import annotations

import os
import re
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.web_analysis.models import ModuleRecord, SiteAnalysis
from app.xninetzy.os.web_analysis.sites import get_site


class AnalysisBusyError(RuntimeError):
    pass


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


class AnalysisCacheManager:
    def __init__(self, root: str | Path | None = None) -> None:
        settings = get_settings()
        self.root = Path(root or settings.WEB_ANALYSIS_DATA_DIR) / "analyses"

    def site_dir(self, site_slug: str) -> Path:
        normalized = site_slug.strip().lower()
        if re.fullmatch(r"public-[0-9a-f]{16}", normalized):
            slug = normalized
        else:
            slug = get_site(site_slug).slug
        path = self.root / slug
        path.mkdir(parents=True, exist_ok=True)
        return path

    def json_path(self, site_slug: str) -> Path:
        return self.site_dir(site_slug) / "analysis.json"

    def markdown_path(self, site_slug: str) -> Path:
        return self.site_dir(site_slug) / "analisis_web.md"

    def load(self, site_slug: str) -> SiteAnalysis | None:
        path = self.json_path(site_slug)
        if not path.exists():
            return None
        return SiteAnalysis.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, analysis: SiteAnalysis) -> Path:
        get_site(analysis.site_slug)
        json_payload = analysis.model_dump_json(indent=2)
        self._atomic_write(self.json_path(analysis.site_slug), json_payload + "\n")
        self._atomic_write(self.markdown_path(analysis.site_slug), self._render_markdown(analysis))
        return self.markdown_path(analysis.site_slug)

    def get_module(self, site_slug: str, module_name: str) -> ModuleRecord | None:
        analysis = self.load(site_slug)
        if not analysis:
            return None
        return next((module for module in analysis.modules if module.name == module_name), None)

    def is_stale(self, site_slug: str, module_name: str | None = None, ttl_days: int | None = None) -> bool:
        analysis = self.load(site_slug)
        if not analysis:
            return True
        settings = get_settings()
        ttl = timedelta(days=ttl_days or settings.WEB_ANALYSIS_DEFAULT_TTL_DAYS)
        if module_name:
            module = self.get_module(site_slug, module_name)
            if not module:
                return True
            analyzed_at = _parse_timestamp(module.analyzed_at)
        else:
            analyzed_at = _parse_timestamp(analysis.analyzed_at)
        return datetime.now(timezone.utc) - analyzed_at >= ttl

    @contextmanager
    def lease(self, site_slug: str) -> Iterator[None]:
        lock_path = self.site_dir(site_slug) / ".analysis.lock"
        stale_after = get_settings().WEB_ANALYSIS_LOCK_STALE_SECONDS
        if lock_path.exists():
            age = datetime.now(timezone.utc).timestamp() - lock_path.stat().st_mtime
            if age > stale_after:
                lock_path.unlink(missing_ok=True)
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise AnalysisBusyError(f"Analisis {site_slug} sedang berjalan") from exc
        try:
            os.write(fd, str(os.getpid()).encode("ascii"))
            os.close(fd)
            yield
        finally:
            try:
                os.close(fd)
            except OSError:
                pass
            lock_path.unlink(missing_ok=True)

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(content, encoding="utf-8")
        # Structural cache is intentionally free of personal/session data and
        # must remain readable by the local host owner even when Docker runs as root.
        os.chmod(temp, 0o644)
        temp.replace(path)

    @staticmethod
    def _render_markdown(analysis: SiteAnalysis) -> str:
        lines = [
            f"# Analisis Web: {analysis.site_name}",
            "",
            f"- URL: {analysis.base_url}",
            f"- Terakhir dianalisis: {analysis.analyzed_at}",
            f"- Status auth: {analysis.auth_status}",
            f"- Versi skema: v{analysis.schema_version}",
            "- Catatan privasi: file ini hanya memuat struktur; data akademik owner disimpan terpisah dan terenkripsi.",
            "",
            "## Modul Terdeteksi",
        ]
        if not analysis.modules:
            lines.append("- Belum ada modul terdeteksi.")
        for module in analysis.modules:
            lines.extend(
                [
                    "",
                    f"### {module.name}",
                    f"- Path: `{module.path}`",
                    f"- Klasifikasi: {module.classification}",
                    f"- Selector: {', '.join(f'`{item}`' for item in module.selectors) or '-'}",
                    f"- Field names: {', '.join(f'`{item}`' for item in module.field_names) or '-'}",
                    f"- Structure hash: `{module.structure_hash}`",
                ]
            )
        lines.extend(["", "## Endpoint Read-only Terdeteksi"])
        if analysis.endpoints:
            for endpoint in analysis.endpoints:
                suffix = f"?{'&'.join(endpoint.query_keys)}" if endpoint.query_keys else ""
                lines.append(f"- {endpoint.method} `{endpoint.path}{suffix}` ({endpoint.status or '-'})")
        else:
            lines.append("- Tidak ada endpoint GET/HEAD yang dicatat.")
        lines.extend(["", "## Flag Perlindungan (DO NOT AUTOMATE)"])
        lines.extend(f"- {flag}" for flag in analysis.protection_flags)
        if not analysis.protection_flags:
            lines.append("- Tidak ada flag tambahan; semua aksi mutasi tetap dinonaktifkan oleh engine.")
        lines.extend(["", "## Catatan Login"])
        lines.extend(f"- {note}" for note in analysis.login_notes)
        if not analysis.login_notes:
            lines.append("- Tidak ada credential, cookie, token, atau nilai field yang disimpan di file ini.")
        if analysis.errors:
            lines.extend(["", "## Error Aman"])
            lines.extend(f"- {error}" for error in analysis.errors)
        return "\n".join(lines).rstrip() + "\n"
