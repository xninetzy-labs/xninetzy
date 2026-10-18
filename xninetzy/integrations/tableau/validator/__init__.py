from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re

from lxml import etree

from xninetzy.integrations.tableau import xsd
from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.ir import DOCUMENT_FEATURES, FORMAT_VERSION, WORKBOOK_NS
from xninetzy.integrations.tableau.parser import parse_workbook

XSD_NOT_ASSESSED = "NOT_ASSESSED"
REQUIRED_FEATURES = ("SheetIdentifierTracking", "IntuitiveSorting", "IntuitiveSorting_SP2", "SortTagCleanup")


@dataclass(slots=True)
class ValidationReport:
    path: str
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: dict[str, bool | str] = field(default_factory=dict)
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


def _children(root: etree._Element, container: str, tag: str) -> list[etree._Element]:
    parent = root.find(container)
    return [el for el in (parent if parent is not None else []) if isinstance(el.tag, str) and el.tag == tag]


def _check_schema(raw: bytes, version: str, report: ValidationReport) -> None:
    if not xsd.available():
        report.checks["xsd"] = XSD_NOT_ASSESSED
        report.warnings.append("TWB_XSD_NOT_ASSESSED: lxml atau file XSD tidak tersedia")
        return
    resolved = xsd.resolve_version(version)
    if resolved not in xsd.supported_versions():
        report.checks["xsd"] = XSD_NOT_ASSESSED
        report.warnings.append(
            f"TWB_XSD_NOT_ASSESSED: version '{version}' tidak punya XSD resmi (didukung: {', '.join(xsd.supported_versions())})"
        )
        return
    problems = xsd.validate(raw, resolved)
    report.checks["xsd"] = not problems
    report.metadata["xsd_version"] = resolved
    if problems:
        report.valid = False
        report.errors.extend(f"TWB_XSD_ERROR: {problem}" for problem in problems)


def _check_manifest(root: etree._Element, version: str, report: ValidationReport) -> None:
    manifest = root.find("document-format-change-manifest")
    declared = {child.tag for child in manifest if isinstance(child.tag, str)} if manifest is not None else set()
    missing_required = [feature for feature in REQUIRED_FEATURES if feature not in declared]
    missing_optional = [feature for feature in DOCUMENT_FEATURES if feature not in declared and feature not in REQUIRED_FEATURES]
    report.checks["manifest"] = not missing_required and "ManifestByVersion" not in declared
    if "ManifestByVersion" in declared:
        report.valid = False
        report.errors.append("TWB_MANIFEST_INVALID: <ManifestByVersion> bukan elemen manifest Tableau; Tableau Desktop menolak dokumen ini")
    if missing_required:
        report.valid = False
        report.errors.append(
            f"TWB_MANIFEST_INCOMPLETE: fitur wajib tidak dideklarasikan ({', '.join(missing_required)}); "
            "Tableau Desktop memuat skema lama dan menolak worksheet"
        )
    if missing_optional:
        report.warnings.append(f"TWB_MANIFEST_PARTIAL: fitur tidak dideklarasikan ({', '.join(missing_optional)})")
    if version != FORMAT_VERSION:
        report.warnings.append(f"TWB_FORMAT_VERSION: version '{version}' bukan versi format dokumen Tableau terkini ({FORMAT_VERSION})")


def validate_workbook(path: Path | str, schema_version: str | None = None) -> ValidationReport:
    p = Path(path)
    report = ValidationReport(path=str(p))

    if not p.is_file():
        report.errors.append(f"TWB_PARSE_ERROR: workbook not found at {p}")
        report.valid = False
        report.checks["xml"] = False
        return report

    raw_bytes = p.read_bytes()
    if b"<!DOCTYPE" in raw_bytes[:4096].upper() or b"<!ENTITY" in raw_bytes[:4096].upper():
        report.errors.append("TWB_PARSE_ERROR: DOCTYPE/ENTITY tidak diizinkan di workbook")
        report.valid = False
        report.checks["xml"] = False
        return report
    try:
        root = etree.fromstring(raw_bytes, etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False))
    except etree.XMLSyntaxError as exc:
        report.errors.append(f"TWB_PARSE_ERROR: cannot parse {p.name}: {exc}")
        report.valid = False
        report.checks["xml"] = False
        return report

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
    version = str(root.get("version", ""))
    report.metadata = {
        "source_platform": root.get("source-platform", "win"),
        "version": version,
    }

    report.checks["namespace"] = root.nsmap.get("user") == WORKBOOK_NS

    datasources = _children(root, "datasources", "datasource")
    ds_names = {ds.get("name") for ds in datasources if ds.get("name")}
    report.checks["datasources"] = bool(ds_names)
    if not report.checks["datasources"]:
        report.warnings.append("TWB_NO_DATASOURCES: workbook declares no datasources")

    worksheets = _children(root, "worksheets", "worksheet")
    ws_names = {ws.get("name") for ws in worksheets if ws.get("name")}
    report.checks["worksheets"] = bool(ws_names)

    dashboards = _children(root, "dashboards", "dashboard")
    sheet_names = ws_names | {db.get("name") for db in dashboards if db.get("name")}
    for db in dashboards:
        for zone in db.iter("zone"):
            ref = zone.get("name")
            if ref and ref not in sheet_names:
                report.errors.append(
                    f"TWB_DANGLING_DASHBOARD_REF: dashboard '{db.get('name')}' "
                    f"references unknown worksheet '{ref}'"
                )
                report.valid = False
        for point in db.iter("story-point"):
            ref = point.get("captured-sheet")
            if ref and ref not in sheet_names:
                report.errors.append(
                    f"TWB_DANGLING_STORY_REF: story '{db.get('name')}' captures unknown sheet '{ref}'"
                )
                report.valid = False

    for window in _children(root, "windows", "window"):
        ref = window.get("name")
        if ref and ref not in sheet_names:
            report.warnings.append(f"TWB_DANGLING_WINDOW: window '{ref}' tidak punya worksheet/dashboard")

    for sheet in worksheets:
        for tag in ("rows", "cols"):
            for shelf in sheet.iter(tag):
                for ref in re.findall(r"\[([^\]]+)\]\.\[", shelf.text or ""):
                    if ref not in ds_names:
                        report.errors.append(
                            f"TWB_DANGLING_DATASOURCE_REF: worksheet '{sheet.get('name')}' memakai datasource '{ref}' yang tidak ada"
                        )
                        report.valid = False

    raw = raw_bytes.decode("utf-8", errors="replace")
    if re.search(r'[A-Za-z]:\\\\', raw) or "C:\\" in raw:
        report.warnings.append(
            "TWB_WINDOWS_PATH: stale Windows path detected, repath for Linux/Mac deployment"
        )

    _check_manifest(root, version, report)
    _check_schema(raw_bytes, schema_version or version, report)

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
