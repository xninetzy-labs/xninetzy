from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from xml.etree import ElementTree as ET

from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.ir import WORKBOOK_NS
from xninetzy.integrations.tableau.parser import parse_workbook


@dataclass(slots=True)
class ValidationReport:
    path: str
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)
    xml_root_present: bool = False
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "checks": dict(self.checks),
            "xml_root_present": self.xml_root_present,
            "metadata": dict(self.metadata),
        }


def validate_workbook(path: Path | str) -> ValidationReport:
    p = Path(path)
    report = ValidationReport(path=str(p))

    if not p.is_file():
        report.errors.append(f"TWB_PARSE_ERROR: workbook not found at {p}")
        report.valid = False
        report.checks["xml"] = False
        return report

    try:
        tree = ET.parse(p)
    except ET.ParseError as exc:
        report.errors.append(f"TWB_PARSE_ERROR: cannot parse {p.name}: {exc}")
        report.valid = False
        report.checks["xml"] = False
        return report

    root = tree.getroot()
    local = root.tag.split("}", 1)[-1] if "}" in root.tag else root.tag
    if local != "workbook":
        report.errors.append(
            f"TWB_PARSE_ERROR: root element must be <workbook>, got <{local}>"
        )
        report.valid = False
        report.checks["xml"] = False
        return report

    report.xml_root_present = True
    report.checks["xml"] = True
    report.metadata = {
        "source_platform": root.get("source-platform", "linux"),
        "version": root.get("version", "18.1"),
    }

    ns_ok = WORKBOOK_NS in ET.tostring(root, encoding="unicode") or root.tag.startswith("{" + WORKBOOK_NS.split("/")[0])
    report.checks["namespace"] = ns_ok

    datasources = root.findall(".//datasources/datasource") or root.findall(".//datasource")
    ds_names = {ds.get("name") for ds in datasources if ds.get("name")}
    report.checks["datasources"] = bool(datasources) and bool(ds_names)
    if not report.checks["datasources"]:
        report.warnings.append("TWB_NO_DATASOURCES: workbook declares no datasources")

    worksheets = root.findall(".//worksheets/worksheet") or root.findall(".//worksheet")
    ws_names = {ws.get("name") for ws in worksheets if ws.get("name")}
    report.checks["worksheets"] = bool(worksheets) and bool(ws_names)

    dashboards = root.findall(".//dashboards/dashboard") or root.findall(".//dashboard")
    for db in dashboards:
        for zone in db.findall(".//zones/zone"):
            ref = zone.get("name") or zone.get("worksheet")
            if ref and ref not in ws_names:
                report.errors.append(
                    f"TWB_DANGLING_DASHBOARD_REF: dashboard '{db.get('name')}' "
                    f"references unknown worksheet '{ref}'"
                )
                report.valid = False

    raw = p.read_text(encoding="utf-8", errors="replace")
    if re.search(r'[A-Za-z]:\\\\', raw) or "C:\\" in raw:
        report.warnings.append(
            "TWB_WINDOWS_PATH: stale Windows path detected, repath for Linux/Mac deployment"
        )

    # Round-trip serialization smoke test
    try:
        parsed = parse_workbook(p)
        from xninetzy.integrations.tableau.compiler import compile_workbook

        body = compile_workbook(parsed)
        report.checks["serialization_roundtrip"] = isinstance(body, (bytes, bytearray)) and len(body) > 0
    except TableauIntegrationError as exc:
        report.errors.append(f"TWB_ROUNDTRIP_ERROR: {exc}")
        report.valid = False
        report.checks["serialization_roundtrip"] = False

    return report


__all__ = ["ValidationReport", "validate_workbook"]
