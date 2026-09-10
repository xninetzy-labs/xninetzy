from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import yaml

from app.xninetzy.core.config import Settings, get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.skills.models import SkillDefinition, SkillMatch

logger = logging.getLogger(__name__)

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SECRET_PATTERN = re.compile(
    r"(?i)(?:api[_ -]?key|password|passwd|secret|token|cookie|storage[_ -]?state)\s*[:=]\s*[^\s]+"
)
EXTERNAL_REFERENCE_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
RESOURCE_ROOTS = {"agents", "assets", "references", "scripts"}
FRONTMATTER_PATTERN = re.compile(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", re.DOTALL)
ALLOWED_FRONTMATTER = {"name", "description", "license", "compatibility", "metadata"}
ALIASES = {
    "it": "it-learning",
    "it_learning": "it-learning",
    "learning": "it-learning",
    "programming": "it-learning",
    "coding": "it-learning",
    "management": "life-management",
    "graph_rag": "graph-rag",
    "hebat": "hebat-academic",
    "obsidian": "obsidian-knowledge",
    "cyber": "cyber-campus",
}
SKILL_TOPIC_HINTS = {
    "it-learning": {
        "clustering",
        "cluster",
        "kmeans",
        "dbscan",
        "hierarchical",
        "machine",
        "learning",
        "analytics",
        "algorithm",
        "roadmap",
        "study",
        "mastery",
        "recall",
    },
    "research": {
        "research",
        "riset",
        "source",
        "literature",
        "paper",
        "youtube",
        "citation",
    },
    "graph-rag": {
        "graph",
        "relationship",
        "prerequisite",
        "connection",
        "neighborhood",
    },
    "define-goal": {"goal", "objective", "target", "milestone", "outcome", "priorities"},
    "jupyter-notebook": {"jupyter", "notebook", "pandas", "data", "analytics", "experiment", "visualization"},
    "pdf": {"pdf", "document", "extract", "render", "page", "material"},
    "playwright": {"browser", "playwright", "portal", "login", "form", "automation"},
    "playwright-interactive": {"browser", "interactive", "inspect", "locator", "portal"},
    "screenshot": {"screenshot", "capture", "visual", "screen", "image"},
    "security-best-practices": {"security", "secure", "vulnerability", "secret", "authentication", "authorization"},
    "security-ownership-map": {"security", "ownership", "repository", "service", "maintainer"},
    "security-threat-model": {"threat", "risk", "attack", "boundary", "security", "model"},
    "transcribe": {"audio", "voice", "transcribe", "transcription", "speech", "recording"},
    "cli-creator": {"cli", "command", "interface", "tool", "developer"},
    "gh-fix-ci": {"ci", "github", "workflow", "build", "test", "failure"},
}

STOPWORDS = {
    "aku",
    "anda",
    "atau",
    "buat",
    "dalam",
    "dari",
    "dan",
    "dengan",
    "ingin",
    "kamu",
    "minta",
    "pada",
    "mau",
    "ingin",
    "tolong",
    "bisa",
    "saya",
    "the",
    "untuk",
    "yang",
}


class SkillValidationError(ValueError):
    pass


def _resource_paths(path: Path | None) -> list[str]:
    if path is None:
        return []
    root = path.parent
    resources: list[str] = []
    for directory in sorted(RESOURCE_ROOTS):
        resource_root = root / directory
        if resource_root.is_symlink() or not resource_root.is_dir():
            continue
        for candidate in sorted(resource_root.rglob("*")):
            if candidate.is_file() and not candidate.is_symlink():
                resources.append(candidate.relative_to(root).as_posix())
    return resources


def _quality_warnings(content: str, body: str, path: Path | None) -> list[str]:
    settings = get_settings()
    warnings: list[str] = []
    line_count = len(content.splitlines())
    if line_count > settings.XNINETZY_SKILL_MAX_BODY_LINES:
        warnings.append(
            f"SKILL.md memiliki {line_count} baris; target progressive disclosure "
            f"adalah <= {settings.XNINETZY_SKILL_MAX_BODY_LINES} baris."
        )
    if SECRET_PATTERN.search(body):
        warnings.append("Body mengandung pola credential atau token; audit sebelum dipakai.")
    if re.search(r"https?://", body):
        warnings.append("Body memuat URL eksternal; verifikasi provenance dan network intent.")
    if path is not None:
        root = path.parent
        for target in EXTERNAL_REFERENCE_PATTERN.findall(body):
            clean_target = target.split("#", 1)[0].strip()
            if not clean_target or clean_target.startswith(("http://", "https://")):
                continue
            referenced = Path(clean_target)
            if referenced.is_absolute() or ".." in referenced.parts:
                warnings.append(f"Referensi keluar dari folder skill: {clean_target}")
            elif not (root / referenced).is_file():
                warnings.append(f"Referensi skill tidak ditemukan: {clean_target}")
    return list(dict.fromkeys(warnings))


def _trust_level(source: str) -> str:
    if source == "builtin":
        return "trusted-builtin"
    if source == "user":
        return "owner-installed"
    return "untrusted"


def builtin_skill_dir() -> Path:
    return Path(__file__).resolve().parents[3] / ".agents" / "skills"


def user_skill_dir(settings: Settings | None = None) -> Path:
    current = settings or get_settings()
    configured = current.XNINETZY_SKILLS_DIR.strip()
    if configured:
        return Path(configured).expanduser()
    return Path(current.DATA_DIR) / "opencode-config" / "opencode" / "skills"


def _normalized_name(name: str) -> str:
    key = (name or "").strip().lower()
    return ALIASES.get(key, key.replace("_", "-"))


def _body_from_content(content: str) -> str:
    match = FRONTMATTER_PATTERN.match(content)
    return content[match.end() :].strip() if match else ""


def parse_skill_markdown(
    content: str,
    *,
    path: Path | None = None,
    source: str = "user",
    max_bytes: int | None = None,
) -> tuple[SkillDefinition, str]:
    encoded = content.encode("utf-8")
    limit = max_bytes or get_settings().XNINETZY_SKILL_MAX_BYTES
    if not encoded or len(encoded) > limit:
        raise SkillValidationError(f"SKILL.md harus berukuran 1-{limit} byte.")
    match = FRONTMATTER_PATTERN.match(content)
    if not match:
        raise SkillValidationError("SKILL.md harus diawali YAML frontmatter yang valid.")
    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise SkillValidationError(f"YAML frontmatter tidak valid: {exc}") from exc
    if not isinstance(frontmatter, dict):
        raise SkillValidationError("Frontmatter harus berupa mapping YAML.")
    unexpected = set(frontmatter) - ALLOWED_FRONTMATTER
    if unexpected:
        raise SkillValidationError(
            "Frontmatter tidak dikenal: " + ", ".join(sorted(unexpected))
        )
    name = str(frontmatter.get("name") or "").strip()
    description = re.sub(r"\s+", " ", str(frontmatter.get("description") or "")).strip()
    if not NAME_PATTERN.fullmatch(name) or len(name) > 64:
        raise SkillValidationError(
            "name harus lowercase kebab-case, 1-64 karakter, tanpa hyphen ganda."
        )
    if not description or len(description) > 1024:
        raise SkillValidationError("description harus berukuran 1-1024 karakter.")
    if path is not None and path.parent.name != name:
        raise SkillValidationError(
            f"Nama skill `{name}` harus sama dengan folder `{path.parent.name}`."
        )
    body = _body_from_content(content)
    if not body:
        raise SkillValidationError("Body SKILL.md tidak boleh kosong.")
    metadata_value = frontmatter.get("metadata") or {}
    if not isinstance(metadata_value, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in metadata_value.items()
    ):
        raise SkillValidationError("metadata harus berupa mapping string ke string.")
    warnings = _quality_warnings(content, body, path)
    definition = SkillDefinition(
        name=name,
        description=description,
        path=str(path) if path else "",
        source=source,
        content_hash=hashlib.sha256(encoded).hexdigest(),
        metadata=dict(metadata_value),
        line_count=len(content.splitlines()),
        resource_paths=_resource_paths(path),
        trust_level=_trust_level(source),
        quality_warnings=warnings,
    )
    return definition, body


def _load_directory(root: Path, source: str) -> dict[str, SkillDefinition]:
    discovered: dict[str, SkillDefinition] = {}
    if not root.is_dir():
        return discovered
    for path in sorted(root.glob("*/SKILL.md")):
        try:
            content = path.read_text(encoding="utf-8")
            skill, _ = parse_skill_markdown(content, path=path, source=source)
        except (OSError, UnicodeError, SkillValidationError) as exc:
            logger.warning("Skill dilewati (%s): %s", path, exc)
            continue
        discovered[skill.name] = skill
    return discovered


def discover_skills(
    *,
    builtin_dir: Path | None = None,
    user_dir: Path | None = None,
) -> dict[str, SkillDefinition]:
    skills = _load_directory(builtin_dir or builtin_skill_dir(), "builtin")
    for name, skill in _load_directory(user_dir or user_skill_dir(), "user").items():
        if name in skills and not get_settings().XNINETZY_SKILL_ALLOW_BUILTIN_OVERRIDE:
            logger.warning("User skill `%s` tidak boleh menimpa built-in skill.", name)
            continue
        skills[name] = skill
    return dict(sorted(skills.items()))


def list_skills() -> list[SkillDefinition]:
    return list(discover_skills().values())


def get_skill(name: str) -> SkillDefinition | None:
    return discover_skills().get(_normalized_name(name))


def read_skill_markdown(name: str) -> str | None:
    skill = get_skill(name)
    if not skill:
        return None
    try:
        content = Path(skill.path).read_text(encoding="utf-8")
        _, body = parse_skill_markdown(content, path=Path(skill.path), source=skill.source)
    except (OSError, UnicodeError, SkillValidationError):
        return None
    return body


def _terms(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", value.casefold())
        if len(token) >= 3 and token not in STOPWORDS
    }


def rank_skills(request: str, limit: int = 3) -> list[SkillMatch]:
    normalized = re.sub(r"[^a-z0-9]+", " ", request.casefold()).strip()
    request_terms = _terms(request)
    matches: list[SkillMatch] = []
    for skill in list_skills():
        name_phrase = skill.name.replace("-", " ")
        name_terms = _terms(name_phrase)
        description_terms = _terms(skill.description)
        hint_terms = set(SKILL_TOPIC_HINTS.get(skill.name, set()))
        metadata_terms = _terms(skill.metadata.get("triggers", ""))
        matched_name = sorted(request_terms & name_terms)
        matched_description = sorted(request_terms & description_terms)
        matched_hints = sorted(request_terms & hint_terms)
        matched_metadata = sorted(request_terms & metadata_terms)
        score = (
            len(matched_name) * 5
            + len(matched_description)
            + len(matched_hints) * 3
            + len(matched_metadata) * 4
        )
        reasons: list[str] = []
        if matched_name:
            reasons.append("name")
        if matched_description:
            reasons.append("description")
        if matched_hints:
            reasons.append("topic-hint")
        if matched_metadata:
            reasons.append("metadata-trigger")
        if name_phrase and name_phrase in normalized:
            score += 8
            reasons.append("phrase")
        explicit_names = {f"${skill.name}", f"/skill {skill.name}"}
        if any(value in request.casefold() for value in explicit_names):
            score += 20
            reasons.append("explicit")
        if score:
            matches.append(
                SkillMatch(
                    skill=skill,
                    score=score,
                    matched_terms=list(
                        dict.fromkeys(
                            matched_name + matched_description + matched_hints + matched_metadata
                        )
                    ),
                    selection_reasons=reasons,
                )
            )
    matches.sort(key=lambda item: (-item.score, item.skill.name))
    top_score = matches[0].score if matches else 1
    for match in matches:
        match.confidence = round(min(1.0, match.score / top_score), 3)
    return matches[: min(max(int(limit), 1), 10)]


def validate_skill_markdown(
    content: str,
    *,
    path: Path | None = None,
) -> tuple[SkillDefinition, list[str]]:
    skill, _ = parse_skill_markdown(content, path=path)
    return skill, list(skill.quality_warnings)


def skill_catalog_health() -> dict[str, object]:
    roots = [(builtin_skill_dir(), "builtin"), (user_skill_dir(), "user")]
    valid: list[dict[str, object]] = []
    invalid: list[dict[str, str]] = []
    warnings: list[dict[str, object]] = []
    for root, source in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*/SKILL.md")):
            try:
                skill, _ = parse_skill_markdown(
                    path.read_text(encoding="utf-8"), path=path, source=source
                )
            except (OSError, UnicodeError, SkillValidationError) as exc:
                invalid.append({"path": str(path), "error": str(exc)})
                continue
            valid.append(
                {
                    "name": skill.name,
                    "source": skill.source,
                    "trust_level": skill.trust_level,
                    "line_count": skill.line_count,
                    "resource_count": len(skill.resource_paths),
                }
            )
            if skill.quality_warnings:
                warnings.append(
                    {"name": skill.name, "warnings": skill.quality_warnings}
                )
    return {
        "valid": valid,
        "invalid": invalid,
        "warnings": warnings,
        "valid_count": len(valid),
        "invalid_count": len(invalid),
    }


def list_skill_resources(name: str) -> list[str]:
    skill = get_skill(name)
    if skill is None:
        return []
    return list(skill.resource_paths)


def read_skill_resource(
    name: str,
    relative_path: str,
    *,
    max_bytes: int | None = None,
) -> str:
    skill = get_skill(name)
    if skill is None:
        raise SkillValidationError(f"Skill `{name}` tidak ditemukan atau tidak valid.")
    requested = Path(relative_path)
    if requested.is_absolute() or ".." in requested.parts:
        raise SkillValidationError("Resource harus berupa path relatif tanpa parent traversal.")
    if not requested.parts or requested.parts[0] not in RESOURCE_ROOTS:
        raise SkillValidationError(
            "Resource hanya boleh berada di agents, references, scripts, atau assets."
        )
    root = Path(skill.path).parent.resolve()
    raw_target = root / requested
    if raw_target.is_symlink():
        raise SkillValidationError("Resource symlink tidak diizinkan.")
    target = raw_target.resolve()
    if root not in target.parents or not target.is_file():
        raise SkillValidationError("Resource tidak ditemukan atau keluar dari folder skill.")
    limit = max_bytes or get_settings().XNINETZY_SKILL_RESOURCE_MAX_BYTES
    payload = target.read_bytes()
    if len(payload) > limit:
        raise SkillValidationError(f"Resource melebihi batas {limit} byte.")
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        raise SkillValidationError(
            "Resource binary tidak dapat dimuat sebagai teks; gunakan daftar resource."
        )


def _write_atomic(path: Path, content: str) -> None:
    temporary = path.parent / f".{path.name}.{uuid4().hex}.tmp"
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def _normalize_resource_payloads(resources: dict[str, str] | None) -> dict[str, str]:
    if resources is None:
        return {}
    if not isinstance(resources, dict):
        raise SkillValidationError("resources harus berupa mapping path ke teks.")
    limit = get_settings().XNINETZY_SKILL_RESOURCE_MAX_BYTES
    normalized: dict[str, str] = {}
    for raw_path, content in resources.items():
        if not isinstance(raw_path, str) or not isinstance(content, str):
            raise SkillValidationError("Setiap resource harus memiliki path dan isi teks.")
        requested = Path(raw_path)
        if requested.is_absolute() or ".." in requested.parts:
            raise SkillValidationError("Resource harus berupa path relatif tanpa parent traversal.")
        if not requested.parts or requested.parts[0] not in RESOURCE_ROOTS:
            raise SkillValidationError(
                "Resource hanya boleh berada di agents, references, scripts, atau assets."
            )
        encoded = content.encode("utf-8")
        if not encoded or len(encoded) > limit:
            raise SkillValidationError(
                f"Resource `{raw_path}` harus berukuran 1-{limit} byte."
            )
        normalized[requested.as_posix()] = content
    return normalized


def _resource_manifest(resources: dict[str, str]) -> dict[str, str]:
    return {
        path: hashlib.sha256(content.encode("utf-8")).hexdigest()
        for path, content in sorted(resources.items())
    }


def install_skill(
    content: str,
    *,
    resources: dict[str, str] | None = None,
    replace: bool = False,
    idempotency_key: str = "",
    destination: Path | None = None,
) -> tuple[SkillDefinition, str]:
    skill, _ = parse_skill_markdown(content, source="user")
    resource_payloads = _normalize_resource_payloads(resources)
    resource_manifest = _resource_manifest(resource_payloads)
    payload_hash = hashlib.sha256(
        json.dumps(
            {
                "skill": skill.content_hash,
                "resources": resource_manifest,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    root = (destination or user_skill_dir()).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    root = root.resolve()
    target_dir = root / skill.name
    if target_dir.is_symlink():
        raise SkillValidationError("Folder skill tidak boleh berupa symlink.")
    target_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    if target_dir.resolve().parent != root:
        raise SkillValidationError("Path skill keluar dari katalog yang diizinkan.")
    target = target_dir / "SKILL.md"
    operation_key = hashlib.sha256(
        (idempotency_key.strip() or f"{skill.name}:{payload_hash}:{replace}").encode()
    ).hexdigest()
    operations = root / ".operations"
    operations.mkdir(mode=0o700, exist_ok=True)
    receipt_path = operations / f"{operation_key}.json"
    if receipt_path.is_file():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("payload_hash") != payload_hash:
            raise SkillValidationError("Idempotency key sudah dipakai untuk skill berbeda.")
        existing = get_skill_from_path(target, "user")
        if existing is None:
            raise SkillValidationError("Receipt ada tetapi file skill tidak ditemukan.")
        return existing, "unchanged"
    action = "installed"
    existing_content = target.read_text(encoding="utf-8") if target.is_file() else None
    existing_manifest: dict[str, str] = {}
    for relative_path in resource_manifest:
        resource_path = target_dir / relative_path
        if resource_path.is_file() and not resource_path.is_symlink():
            existing_manifest[relative_path] = hashlib.sha256(
                resource_path.read_bytes()
            ).hexdigest()
    if existing_content is not None:
        existing_skill_hash = hashlib.sha256(existing_content.encode("utf-8")).hexdigest()
        if existing_skill_hash == skill.content_hash and existing_manifest == resource_manifest:
            action = "unchanged"
        elif not replace:
            raise SkillValidationError(
                f"Skill `{skill.name}` sudah ada. Gunakan replace=true untuk memperbarui."
            )
        else:
            timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            shutil.copy2(target, target_dir / f"SKILL.md.bak.{timestamp}")
            _write_atomic(target, content)
            action = "updated"
    else:
        _write_atomic(target, content)
    if action != "unchanged":
        for relative_path, resource_content in resource_payloads.items():
            resource_path = target_dir / relative_path
            resource_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            if resource_path.is_symlink():
                raise SkillValidationError("Resource target symlink tidak diizinkan.")
            if resource_path.is_file() and replace:
                timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
                shutil.copy2(resource_path, resource_path.with_name(f"{resource_path.name}.bak.{timestamp}"))
            elif resource_path.is_file() and not replace:
                existing_hash = hashlib.sha256(resource_path.read_bytes()).hexdigest()
                if existing_hash != resource_manifest[relative_path]:
                    raise SkillValidationError(
                        f"Resource `{relative_path}` sudah ada dan berbeda; gunakan replace=true."
                    )
                continue
            _write_atomic(resource_path, resource_content)
    receipt = {
        "skill": skill.name,
        "payload_hash": payload_hash,
        "skill_hash": skill.content_hash,
        "resources": resource_manifest,
        "action": action,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _write_atomic(receipt_path, json.dumps(receipt, sort_keys=True))
    installed = get_skill_from_path(target, "user")
    if installed is None:
        raise SkillValidationError("Skill gagal divalidasi setelah instalasi.")
    return installed, action


def get_skill_from_path(path: Path, source: str) -> SkillDefinition | None:
    try:
        content = path.read_text(encoding="utf-8")
        skill, _ = parse_skill_markdown(content, path=path, source=source)
        return skill
    except (OSError, UnicodeError, SkillValidationError):
        return None
