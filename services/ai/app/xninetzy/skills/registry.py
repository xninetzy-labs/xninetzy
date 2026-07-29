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
    "saya",
    "the",
    "untuk",
    "yang",
}


class SkillValidationError(ValueError):
    pass


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
    definition = SkillDefinition(
        name=name,
        description=description,
        path=str(path) if path else "",
        source=source,
        content_hash=hashlib.sha256(encoded).hexdigest(),
        metadata=dict(metadata_value),
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
        matched_name = sorted(request_terms & name_terms)
        matched_description = sorted(request_terms & description_terms)
        score = len(matched_name) * 4 + len(matched_description)
        if name_phrase and name_phrase in normalized:
            score += 8
        explicit_names = {f"${skill.name}", f"/skill {skill.name}"}
        if any(value in request.casefold() for value in explicit_names):
            score += 20
        if score:
            matches.append(
                SkillMatch(
                    skill=skill,
                    score=score,
                    matched_terms=list(dict.fromkeys(matched_name + matched_description)),
                )
            )
    matches.sort(key=lambda item: (-item.score, item.skill.name))
    return matches[: min(max(int(limit), 1), 10)]


def _write_atomic(path: Path, content: str) -> None:
    temporary = path.parent / f".{path.name}.{uuid4().hex}.tmp"
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def install_skill(
    content: str,
    *,
    replace: bool = False,
    idempotency_key: str = "",
    destination: Path | None = None,
) -> tuple[SkillDefinition, str]:
    skill, _ = parse_skill_markdown(content, source="user")
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
    payload_hash = skill.content_hash
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
    if target.is_file():
        existing_content = target.read_text(encoding="utf-8")
        if hashlib.sha256(existing_content.encode()).hexdigest() == payload_hash:
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
    receipt = {
        "skill": skill.name,
        "payload_hash": payload_hash,
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
