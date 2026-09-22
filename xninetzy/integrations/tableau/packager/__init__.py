from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from xninetzy.integrations.tableau.errors import TableauIntegrationError


@dataclass(slots=True)
class PackageResult:
    package_path: Path
    workbook_present: bool
    entries: list[str] = field(default_factory=list)
    extras_included: list[str] = field(default_factory=list)


def package_twbx(
    *,
    twb_path: Path | str,
    resources: list[Path | str] | None = None,
    output_path: Path | str | None = None,
) -> PackageResult:
    src = Path(twb_path)
    if not src.is_file():
        raise TableauIntegrationError(
            f"TWBX_SOURCE_ERROR: workbook not found at {src}"
        )

    extras: list[tuple[Path, str]] = []
    for r in resources or []:
        rp = Path(r)
        if not rp.is_file():
            raise TableauIntegrationError(
                f"TWBX_RESOURCE_ERROR: resource not found at {rp}"
            )
        extras.append((rp, rp.name))

    entries: list[str] = [src.name]
    extras_included: list[str] = [name for _, name in extras]

    if output_path is None:
        return PackageResult(
            package_path=src,
            workbook_present=True,
            entries=entries,
            extras_included=extras_included,
        )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(src, arcname=src.name)
        for src_path, arcname in extras:
            zf.write(src_path, arcname=arcname)

    return PackageResult(
        package_path=out,
        workbook_present=True,
        entries=entries + extras_included,
        extras_included=extras_included,
    )


__all__ = ["package_twbx", "PackageResult"]
