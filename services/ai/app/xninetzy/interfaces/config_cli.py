from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import stat
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import dotenv_values
from pydantic import TypeAdapter, ValidationError

from app.xninetzy.core.config import Settings


_SECRET_MARKERS = (
    "API_KEY",
    "PASSWORD",
    "TOKEN",
    "SECRET",
    "ENCRYPTION_KEY",
)
_ASSIGNMENT_PATTERN = re.compile(
    r"^\s*(?:export\s+)?(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*="
)


class ConfigurationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ConfigField:
    name: str
    annotation: Any
    source: str
    secret: bool

    def as_dict(self, configured: bool, value: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "key": self.name,
            "type": _annotation_name(self.annotation),
            "source": self.source,
            "secret": self.secret,
            "configured": configured,
        }
        if value is not None and not self.secret:
            payload["value"] = value
        return payload


class ConfigurationCatalog:
    def __init__(self, fields: dict[str, ConfigField]) -> None:
        self._fields = fields

    @classmethod
    def load(cls, example_path: Path | None = None) -> "ConfigurationCatalog":
        fields = {
            name: ConfigField(
                name=name,
                annotation=field.annotation,
                source="settings",
                secret=_is_secret(name),
            )
            for name, field in Settings.model_fields.items()
        }
        for key in _documented_keys(example_path or _example_path()):
            fields.setdefault(
                key,
                ConfigField(
                    name=key,
                    annotation=str,
                    source="example",
                    secret=_is_secret(key),
                ),
            )
        return cls(fields)

    def get(self, key: str) -> ConfigField:
        field = self._fields.get(key)
        if field is None:
            raise ConfigurationError(
                f"Unknown configuration key: {key}. Use 'xninetzy config list'."
            )
        return field

    def fields(self) -> list[ConfigField]:
        return [self._fields[key] for key in sorted(self._fields)]

    def normalize(self, key: str, raw_value: str) -> str:
        field = self.get(key)
        if field.source != "settings":
            return raw_value
        adapter = TypeAdapter(field.annotation)
        try:
            value = adapter.validate_python(raw_value)
        except ValidationError as first_error:
            try:
                value = adapter.validate_json(raw_value)
            except ValidationError as second_error:
                raise ConfigurationError(
                    f"Invalid value for {key}: {second_error.errors()[0]['msg']}"
                ) from first_error
        return _serialize_typed_value(value)


class EnvConfiguration:
    def __init__(
        self,
        catalog: ConfigurationCatalog | None = None,
        env_path: Path | None = None,
    ) -> None:
        self.catalog = catalog or ConfigurationCatalog.load()
        self.env_path = (env_path or _default_env_path()).expanduser().resolve()

    def values(self) -> dict[str, str]:
        if not self.env_path.exists():
            return {}
        parsed = dotenv_values(self.env_path, interpolate=False)
        return {
            key: value
            for key, value in parsed.items()
            if key and value is not None
        }

    def list_fields(self, show_values: bool = False) -> list[dict[str, Any]]:
        values = self.values()
        return [
            field.as_dict(
                configured=field.name in values,
                value=values.get(field.name) if show_values else None,
            )
            for field in self.catalog.fields()
        ]

    def get(self, key: str) -> dict[str, Any]:
        field = self.catalog.get(key)
        values = self.values()
        return field.as_dict(
            configured=key in values,
            value=values.get(key),
        )

    def set(self, key: str, raw_value: str) -> dict[str, Any]:
        field = self.catalog.get(key)
        value = self.catalog.normalize(key, raw_value)
        self._replace_assignment(key, value)
        return field.as_dict(configured=True)

    def unset(self, key: str) -> dict[str, Any]:
        field = self.catalog.get(key)
        removed = self._remove_assignment(key)
        payload = field.as_dict(configured=False)
        payload["removed"] = removed
        return payload

    def validate(self) -> dict[str, Any]:
        values = self.values()
        known = {field.name for field in self.catalog.fields()}
        unknown = sorted(key for key in values if key not in known)
        errors: list[dict[str, str]] = []
        for key, raw_value in values.items():
            if key not in known:
                continue
            try:
                self.catalog.normalize(key, raw_value)
            except ConfigurationError as error:
                errors.append({"key": key, "error": str(error)})
        return {
            "env_file": str(self.env_path),
            "valid": not unknown and not errors,
            "unknown": unknown,
            "errors": errors,
            "configured": len(values),
        }

    def _replace_assignment(self, key: str, value: str) -> None:
        lines = self._read_lines()
        replacement = f"{key}={_quote_env_value(value)}\n"
        updated: list[str] = []
        replaced = False
        for line in lines:
            matched = _ASSIGNMENT_PATTERN.match(line)
            if matched and matched.group("key") == key:
                if not replaced:
                    updated.append(replacement)
                    replaced = True
                continue
            updated.append(line)
        if not replaced:
            if updated and not updated[-1].endswith(("\n", "\r")):
                updated[-1] += "\n"
            updated.append(replacement)
        self._atomic_write("".join(updated))

    def _remove_assignment(self, key: str) -> bool:
        lines = self._read_lines()
        updated = [
            line
            for line in lines
            if not (
                (matched := _ASSIGNMENT_PATTERN.match(line))
                and matched.group("key") == key
            )
        ]
        removed = len(updated) != len(lines)
        if removed:
            self._atomic_write("".join(updated))
        return removed

    def _read_lines(self) -> list[str]:
        if not self.env_path.exists():
            return []
        return self.env_path.read_text(encoding="utf-8").splitlines(keepends=True)

    def _atomic_write(self, content: str) -> None:
        self.env_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{self.env_path.name}.",
            dir=self.env_path.parent,
            text=True,
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            temporary_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
            os.replace(temporary_path, self.env_path)
        finally:
            temporary_path.unlink(missing_ok=True)


def _annotation_name(annotation: Any) -> str:
    return getattr(annotation, "__name__", str(annotation))


def _is_secret(key: str) -> bool:
    upper_key = key.upper()
    return any(marker in upper_key for marker in _SECRET_MARKERS)


def _serialize_typed_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _quote_env_value(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _documented_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        matched.group("key")
        for line in path.read_text(encoding="utf-8").splitlines()
        if (matched := _ASSIGNMENT_PATTERN.match(line))
    }


def _repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "docker-compose.yml").exists():
            return parent
    return Path.cwd()


def _example_path() -> Path:
    return _repository_root() / ".env.example"


def _default_env_path() -> Path:
    return _repository_root() / ".env"


def _add_env_file_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--env-file", type=Path, default=_default_env_path())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Xninetzy configuration.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List supported configuration keys.")
    _add_env_file_option(list_parser)
    list_parser.add_argument("--json", action="store_true")
    list_parser.add_argument("--show-values", action="store_true")

    get_parser = subparsers.add_parser("get", help="Read one configuration key.")
    _add_env_file_option(get_parser)
    get_parser.add_argument("key")
    get_parser.add_argument("--json", action="store_true")

    set_parser = subparsers.add_parser("set", help="Set one configuration key.")
    _add_env_file_option(set_parser)
    set_parser.add_argument("key")
    set_parser.add_argument("value", nargs="?")
    set_parser.add_argument("--stdin", action="store_true")
    set_parser.add_argument("--json", action="store_true")

    unset_parser = subparsers.add_parser("unset", help="Remove one configuration key.")
    _add_env_file_option(unset_parser)
    unset_parser.add_argument("key")
    unset_parser.add_argument("--json", action="store_true")

    validate_parser = subparsers.add_parser(
        "validate", help="Validate documented configuration values."
    )
    _add_env_file_option(validate_parser)
    validate_parser.add_argument("--json", action="store_true")
    return parser


def _set_value(args: argparse.Namespace, field: ConfigField) -> str:
    if args.stdin:
        return sys.stdin.read().rstrip("\r\n")
    if args.value is not None:
        return args.value
    if field.secret:
        return getpass.getpass(f"{field.name}: ")
    return input(f"{field.name}: ")


def _emit(payload: Any, json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if isinstance(payload, list):
        for item in payload:
            state = "set" if item["configured"] else "unset"
            secret = " secret" if item["secret"] else ""
            print(f"{item['key']} ({item['type']}, {state}{secret})")
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, (list, dict)):
                value = json.dumps(value, ensure_ascii=False)
            print(f"{key}: {value}")


def main() -> None:
    args = build_parser().parse_args()
    config = EnvConfiguration(env_path=args.env_file)
    try:
        if args.command == "list":
            _emit(config.list_fields(args.show_values), args.json)
            return
        if args.command == "get":
            _emit(config.get(args.key), args.json)
            return
        if args.command == "set":
            value = _set_value(args, config.catalog.get(args.key))
            _emit(config.set(args.key, value), args.json)
            return
        if args.command == "unset":
            _emit(config.unset(args.key), args.json)
            return
        result = config.validate()
        _emit(result, args.json)
        if not result["valid"]:
            raise SystemExit(1)
    except ConfigurationError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()

