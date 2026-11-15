from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from xninetzy.integrations.document_studio.errors import DocumentStudioError, MissingDependencyError


def office_binary() -> str | None:
    return shutil.which("soffice") or shutil.which("libreoffice")


def to_pdf(source: Path, out_dir: Path, timeout: int = 240) -> Path:
    binary = office_binary()
    if not binary:
        raise MissingDependencyError("LibreOffice (soffice) is required for PDF output; install libreoffice-core.")
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{source.stem}.pdf"
    if target.exists():
        target.unlink()
    with tempfile.TemporaryDirectory(prefix="xn-studio-lo-") as profile:
        command = [
            binary,
            f"-env:UserInstallation=file://{profile}",
            "--headless",
            "--norestore",
            "--nolockcheck",
            "--convert-to",
            "pdf",
            "--outdir",
            str(out_dir),
            str(source),
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            raise DocumentStudioError(f"PDF conversion timed out after {timeout}s") from exc
    if not target.is_file():
        detail = (result.stderr or result.stdout or "").strip()[-400:]
        raise DocumentStudioError(f"PDF conversion failed for {source.name}: {detail}")
    return target


def pdf_pages_text(pdf: Path) -> list[str]:
    try:
        import pypdf
    except ImportError as exc:
        raise MissingDependencyError("pypdf is required; install xninetzy-mcp[documents].") from exc
    reader = pypdf.PdfReader(str(pdf))
    return [(page.extract_text() or "") for page in reader.pages]


def pdf_fonts(pdf: Path) -> list[str]:
    import pypdf

    reader = pypdf.PdfReader(str(pdf))
    names: set[str] = set()
    for page in reader.pages:
        fonts = (page.get("/Resources") or {}).get("/Font") or {}
        for ref in fonts.values():
            font = ref.get_object()
            base = str(font.get("/BaseFont", "")).lstrip("/")
            if "+" in base:
                base = base.split("+", 1)[1]
            if base:
                names.add(base)
    return sorted(names)
