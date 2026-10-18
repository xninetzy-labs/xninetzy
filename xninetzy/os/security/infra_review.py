from __future__ import annotations

import re
from typing import Any

DATA_STORE_PORTS: dict[int, str] = {5432: "postgres", 6379: "redis", 3306: "mysql", 27017: "mongodb", 9200: "elasticsearch"}
_ALL_INTERFACES = frozenset({"", "0.0.0.0", "::", "[::]"})
_GATEWAY_NAME = re.compile(r"nginx|proxy|gateway|traefik|caddy|haproxy|web|frontend|ingress|edge", re.IGNORECASE)
_PUBLIC_PORTS = frozenset({80, 443})
_LOAD_PROFILES = frozenset({"loadtest", "load-test", "perf", "k6", "load"})
_DANGEROUS_CAPS = frozenset({"SYS_ADMIN", "ALL", "NET_ADMIN", "SYS_PTRACE"})
_IP_LITERAL = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$|^\[[0-9a-f:]+\]$", re.IGNORECASE)


def _finding(rule: str, severity: str, where: str, message: str, remediation: str) -> dict[str, str]:
    return {"id": rule, "severity": severity, "where": where, "message": message, "remediation": remediation}


def parse_port(entry: Any) -> tuple[str, int, int] | None:
    if isinstance(entry, dict):
        target = entry.get("target")
        published = entry.get("published")
        if target is None:
            return None
        try:
            return str(entry.get("host_ip") or ""), int(published or 0), int(target)
        except (TypeError, ValueError):
            return None
    text = str(entry).split("/", 1)[0].strip()
    ipv6 = re.match(r"^(\[[0-9a-fA-F:]+\]):(\d+):(\d+)$", text)
    if ipv6:
        return ipv6.group(1), int(ipv6.group(2)), int(ipv6.group(3))
    parts = text.split(":")
    try:
        if len(parts) == 1:
            return "", 0, int(parts[0])
        if len(parts) == 2:
            return "", int(parts[0]), int(parts[1])
        if len(parts) == 3:
            return parts[0], int(parts[1]), int(parts[2])
    except ValueError:
        return None
    return None


def _command_text(service: dict[str, Any]) -> str:
    command = service.get("command") or ""
    return " ".join(command) if isinstance(command, list) else str(command)


def _environment(service: dict[str, Any]) -> dict[str, str]:
    env = service.get("environment") or {}
    if isinstance(env, list):
        return {item.split("=", 1)[0]: item.split("=", 1)[1] if "=" in item else "" for item in env}
    return {str(k): str(v) for k, v in env.items()}


def _volume_sources(service: dict[str, Any]) -> list[str]:
    sources: list[str] = []
    for volume in service.get("volumes") or []:
        sources.append(str(volume.get("source", "")) if isinstance(volume, dict) else str(volume).split(":", 1)[0])
    return sources


def _has_memory_limit(service: dict[str, Any]) -> bool:
    if service.get("mem_limit"):
        return True
    limits = (((service.get("deploy") or {}).get("resources") or {}).get("limits") or {})
    return bool(limits.get("memory"))


def review_compose(data: dict[str, Any], load_test: bool = False) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for name, service in sorted((data.get("services") or {}).items()):
        service = service or {}
        image = str(service.get("image") or "")
        for raw in service.get("ports") or []:
            parsed = parse_port(raw)
            if parsed is None:
                continue
            host_ip, published, target = parsed
            exposed = host_ip in _ALL_INTERFACES
            store = DATA_STORE_PORTS.get(target) or DATA_STORE_PORTS.get(published)
            where = f"{name}:{published or target}"
            if store and exposed:
                findings.append(_finding("datastore-exposed", "high", where, f"{store} published on all interfaces", "bind to 127.0.0.1 or keep it on an internal network"))
            elif exposed and target not in _PUBLIC_PORTS and not _GATEWAY_NAME.search(name):
                findings.append(_finding("service-exposed-all-interfaces", "medium", where, "internal service published on all interfaces", "bind to 127.0.0.1 or remove the port mapping"))
            if "redis" in image.lower() or target == 6379 or "redis" in name.lower():
                auth = "--requirepass" in _command_text(service) or any(k.upper() in {"REDIS_PASSWORD", "REDIS_ARGS"} and v for k, v in _environment(service).items())
                if not auth:
                    findings.append(_finding("redis-no-auth", "high" if exposed else "medium", where, "redis published without requirepass", "set --requirepass or REDIS_PASSWORD"))
        if not service.get("user") and (service.get("build") or image):
            findings.append(_finding("container-root", "low", name, "no user set; container may run as root", "set user or USER in the image"))
        if service.get("privileged") is True:
            findings.append(_finding("privileged-container", "high", name, "privileged: true", "drop privileged and add only required capabilities"))
        if any("docker.sock" in source for source in _volume_sources(service)):
            findings.append(_finding("docker-socket-mount", "high", name, "docker socket mounted", "remove the mount"))
        caps = {str(c).upper() for c in service.get("cap_add") or []}
        if caps & _DANGEROUS_CAPS:
            findings.append(_finding("dangerous-capability", "high", name, f"cap_add {sorted(caps & _DANGEROUS_CAPS)}", "drop the capability"))
        if service.get("network_mode") == "host":
            findings.append(_finding("host-network", "medium", name, "network_mode host", "use a bridge network"))
        profiles = {str(p) for p in service.get("profiles") or []}
        if (load_test or profiles & _LOAD_PROFILES) and not _has_memory_limit(service):
            findings.append(_finding("missing-mem-limit", "medium", name, "no memory limit in a load-test profile", "set mem_limit or deploy.resources.limits.memory"))
    return findings


def _strip_comments(text: str) -> str:
    return "\n".join(line.split("#", 1)[0] if not re.search(r"['\"].*#.*['\"]", line) else line for line in text.splitlines())


def _blocks(text: str, header: re.Pattern[str]) -> list[tuple[re.Match[str], str]]:
    found: list[tuple[re.Match[str], str]] = []
    for match in header.finditer(text):
        depth = 0
        start = text.index("{", match.start())
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    found.append((match, text[start + 1:i]))
                    break
    return found


def _size_bytes(value: str) -> int:
    match = re.fullmatch(r"(\d+)\s*([kmg]?)", value.strip().lower())
    if not match:
        return -1
    scale = {"": 1, "k": 1024, "m": 1024 ** 2, "g": 1024 ** 3}[match.group(2)]
    return int(match.group(1)) * scale


def review_nginx(conf: str) -> list[dict[str, str]]:
    text = _strip_comments(conf)
    findings: list[dict[str, str]] = []
    tokens = re.findall(r"server_tokens\s+(\w+)\s*;", text)
    if not tokens or any(t.lower() != "off" for t in tokens):
        findings.append(_finding("server-tokens", "low", "http", "server_tokens is not off", "set server_tokens off"))
    wanted = ["X-Frame-Options", "X-Content-Type-Options", "Content-Security-Policy", "Strict-Transport-Security", "Referrer-Policy"]
    missing = [h for h in wanted if not re.search(rf"add_header\s+{re.escape(h)}\b", text, re.IGNORECASE)]
    if missing:
        findings.append(_finding("missing-security-headers", "low", "http", "missing add_header for " + ", ".join(missing), "add the headers with the always flag"))
    xff = re.findall(r"proxy_set_header\s+X-Forwarded-For\s+(\S+?)\s*;", text)
    if any("$proxy_add_x_forwarded_for" in value for value in xff):
        findings.append(_finding("xff-append", "medium", "proxy", "X-Forwarded-For is appended; a client-supplied value is trusted downstream", "use $remote_addr at the edge, or set real_ip from trusted proxies"))
    if not re.search(r"limit_req\s+zone=", text):
        findings.append(_finding("no-rate-limit", "medium", "http", "no limit_req configured", "add limit_req_zone and limit_req"))
    for match in re.finditer(r"client_max_body_size\s+(\S+?)\s*;", text):
        size = _size_bytes(match.group(1))
        if size == 0:
            findings.append(_finding("unlimited-body-size", "high", "http", "client_max_body_size 0 disables the limit", "set an explicit limit"))
        elif size > 50 * 1024 ** 2:
            findings.append(_finding("large-body-size", "medium", "http", f"client_max_body_size {match.group(1)}", "lower the limit"))
    has_resolver = bool(re.search(r"^\s*resolver\s+\S+", text, re.MULTILINE))
    for header, body in _blocks(text, re.compile(r"upstream\s+(\S+)\s*\{")):
        for server in re.findall(r"server\s+([^\s;]+)([^;]*);", body):
            host = server[0].rsplit(":", 1)[0] if not server[0].startswith("[") else server[0].split("]")[0] + "]"
            if not _IP_LITERAL.match(host) and "resolve" not in server[1] and not has_resolver:
                findings.append(_finding("upstream-static-dns", "low", f"upstream {header.group(1)}", f"{host} is resolved only at start", "add a resolver and a variable proxy_pass, or restart nginx on IP change"))
    if re.search(r'proxy_set_header\s+Connection\s+"?upgrade"?\s*;', text, re.IGNORECASE) and not re.search(r"map\s+\$http_upgrade", text):
        findings.append(_finding("connection-upgrade-hardcoded", "low", "proxy", "Connection upgrade is hard-coded, which disables upstream keepalive", "use a map on $http_upgrade"))
    protective = re.compile(r"\bdeny\s+all\b|\ballow\s+|auth_basic|return\s+(?:401|403|404|444)\b|\binternal\s*;")
    for header, body in _blocks(text, re.compile(r"location\s+(?:[=~^*]+\s+)?(\S*(?:/docs|/openapi\.json|/metrics|/swagger)\S*)\s*\{")):
        if not protective.search(body):
            findings.append(_finding("public-docs-endpoint", "medium", f"location {header.group(1)}", "documentation or metrics location is public", "restrict with allow/deny, auth_basic, or return 404"))
    return findings
