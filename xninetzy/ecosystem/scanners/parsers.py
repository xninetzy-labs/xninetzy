from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from typing import Any

from xninetzy.ecosystem.scanners.hit import ScanHit, canonical_advisory, hash_prefix, make_hit

VULN_CATEGORY = "dependency-vulnerability"
SECRET_CATEGORY = "hardcoded-secret"
_SEMGREP_SEVERITY = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}
_ZAP_RISK = {"3": "high", "2": "medium", "1": "low", "0": "info"}


def _load(text: str) -> Any:
    if not text or not text.strip():
        return None
    return json.loads(text)


def parse_gitleaks(text: str) -> list[ScanHit]:
    data = _load(text) or []
    hits: list[ScanHit] = []
    for item in data:
        secret = str(item.get("Secret") or item.get("Match") or "")
        rule = str(item.get("RuleID") or "gitleaks")
        hits.append(make_hit(
            tool="gitleaks",
            rule=rule,
            severity="high",
            asset=str(item.get("File") or ""),
            location=str(item.get("File") or ""),
            line=int(item.get("StartLine") or 0),
            evidence=f"{rule} hash={hash_prefix(secret)}",
            category=SECRET_CATEGORY,
            extra={"commit": str(item.get("Commit") or "")[:12]},
        ))
    return hits


def parse_trivy(text: str) -> list[ScanHit]:
    data = _load(text) or {}
    hits: list[ScanHit] = []
    for result in data.get("Results") or []:
        target = str(result.get("Target") or "")
        for vuln in result.get("Vulnerabilities") or []:
            vid = str(vuln.get("VulnerabilityID") or "")
            pkg = f"{vuln.get('PkgName', '')}@{vuln.get('InstalledVersion', '')}"
            hits.append(make_hit(
                tool="trivy",
                rule=vid,
                severity=vuln.get("Severity"),
                asset=pkg,
                location=canonical_advisory([vid]),
                evidence=str(vuln.get("Title") or vuln.get("Description") or ""),
                category=VULN_CATEGORY,
                extra={
                    "target": target,
                    "fixed_version": str(vuln.get("FixedVersion") or ""),
                    "advisory": canonical_advisory([vid]),
                },
            ))
        for misconf in result.get("Misconfigurations") or []:
            meta = misconf.get("CauseMetadata") or {}
            hits.append(make_hit(
                tool="trivy",
                rule=str(misconf.get("ID") or misconf.get("AVDID") or "misconfig"),
                severity=misconf.get("Severity"),
                asset=target,
                location=target,
                line=int(meta.get("StartLine") or 0),
                evidence=str(misconf.get("Title") or misconf.get("Message") or ""),
                category="misconfiguration",
            ))
        for secret in result.get("Secrets") or []:
            rule = str(secret.get("RuleID") or "secret")
            hits.append(make_hit(
                tool="trivy",
                rule=rule,
                severity=secret.get("Severity") or "high",
                asset=target,
                location=target,
                line=int(secret.get("StartLine") or 0),
                evidence=f"{rule} {secret.get('Title', '')}".strip(),
                category=SECRET_CATEGORY,
            ))
    return hits


def _osv_severity(vuln: dict[str, Any]) -> str:
    specific = vuln.get("database_specific") or {}
    if specific.get("severity"):
        return str(specific["severity"])
    return "medium"


def parse_osv(text: str) -> list[ScanHit]:
    data = _load(text) or {}
    hits: list[ScanHit] = []
    for result in data.get("results") or []:
        source = str((result.get("source") or {}).get("path") or "")
        for entry in result.get("packages") or []:
            package = entry.get("package") or {}
            pkg = f"{package.get('name', '')}@{package.get('version', '')}"
            for vuln in entry.get("vulnerabilities") or []:
                ids = [str(vuln.get("id") or "")] + [str(a) for a in vuln.get("aliases") or []]
                advisory = canonical_advisory(ids)
                hits.append(make_hit(
                    tool="osv-scanner",
                    rule=str(vuln.get("id") or advisory),
                    severity=_osv_severity(vuln),
                    asset=pkg,
                    location=advisory,
                    evidence=str(vuln.get("summary") or ""),
                    category=VULN_CATEGORY,
                    extra={
                        "target": source,
                        "ecosystem": str(package.get("ecosystem") or ""),
                        "advisory": advisory,
                        "aliases": ids[1:],
                    },
                ))
    return hits


def parse_semgrep(text: str) -> list[ScanHit]:
    data = _load(text) or {}
    hits: list[ScanHit] = []
    for item in data.get("results") or []:
        extra = item.get("extra") or {}
        severity = _SEMGREP_SEVERITY.get(str(extra.get("severity") or "").upper(), "medium")
        path = str(item.get("path") or "")
        hits.append(make_hit(
            tool="semgrep",
            rule=str(item.get("check_id") or "semgrep"),
            severity=severity,
            asset=path,
            location=path,
            line=int((item.get("start") or {}).get("line") or 0),
            evidence=str(extra.get("message") or ""),
            category=str(item.get("check_id") or "semgrep").rsplit(".", 1)[-1],
        ))
    return hits


def parse_zap(text: str) -> list[ScanHit]:
    data = _load(text) or {}
    hits: list[ScanHit] = []
    for site in data.get("site") or []:
        for alert in site.get("alerts") or []:
            instances = alert.get("instances") or [{}]
            uri = str((instances[0] or {}).get("uri") or site.get("@name") or "")
            hits.append(make_hit(
                tool="zap",
                rule=str(alert.get("pluginid") or alert.get("alert") or "zap"),
                severity=_ZAP_RISK.get(str(alert.get("riskcode")), "medium"),
                asset=uri,
                location=uri,
                evidence=str(alert.get("alert") or ""),
                category=str(alert.get("alert") or "zap").lower().replace(" ", "-"),
                extra={"instances": len(instances), "confidence": str(alert.get("confidence") or "")},
            ))
    return hits


def parse_schemathesis_junit(text: str) -> list[ScanHit]:
    if not text or not text.strip():
        return []
    root = ET.fromstring(text)
    hits: list[ScanHit] = []
    for case in root.iter("testcase"):
        for failure in list(case.findall("failure")) + list(case.findall("error")):
            name = str(case.get("name") or "operation")
            message = str(failure.get("message") or (failure.text or "")[:200])
            hits.append(make_hit(
                tool="schemathesis",
                rule="api-contract-violation",
                severity="medium",
                asset=name,
                location=name,
                evidence=message,
                category="api-contract-violation",
            ))
    return hits


def parse_grype(text: str) -> list[ScanHit]:
    data = _load(text) or {}
    hits: list[ScanHit] = []
    for match in data.get("matches") or []:
        vuln = match.get("vulnerability") or {}
        artifact = match.get("artifact") or {}
        vid = str(vuln.get("id") or "")
        related = [str(r.get("id") or "") for r in match.get("relatedVulnerabilities") or []]
        advisory = canonical_advisory([vid] + related)
        hits.append(make_hit(
            tool="grype",
            rule=vid,
            severity=vuln.get("severity"),
            asset=f"{artifact.get('name', '')}@{artifact.get('version', '')}",
            location=advisory,
            evidence=str(vuln.get("description") or "")[:200],
            category=VULN_CATEGORY,
            extra={"advisory": advisory},
        ))
    return hits


def count_cyclonedx_components(text: str) -> int:
    data = _load(text) or {}
    return len(data.get("components") or [])
