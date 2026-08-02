from __future__ import annotations

import json
import subprocess
import sys

import pytest

from app.xninetzy.core.config import Settings
from app.xninetzy.interfaces.config_cli import (
    ConfigurationCatalog,
    ConfigurationError,
    EnvConfiguration,
)


@pytest.fixture
def env_configuration(tmp_path):
    example = tmp_path / ".env.example"
    example.write_text(
        "BOT_NAME=Xninetzy AI\nWA_AUTH_DIR=./sessions\nFLAZ_API_KEY=\n",
        encoding="utf-8",
    )
    catalog = ConfigurationCatalog.load(example)
    return EnvConfiguration(catalog=catalog, env_path=tmp_path / ".env")


def test_catalog_contains_every_settings_field():
    catalog = ConfigurationCatalog.load()

    assert set(Settings.model_fields).issubset(
        {field.name for field in catalog.fields()}
    )


def test_set_preserves_comments_validates_types_and_redacts_secrets(env_configuration):
    env_configuration.env_path.write_text(
        "# Keep this comment\nBOT_NAME=\"Old name\"\n",
        encoding="utf-8",
    )

    result = env_configuration.set("BOT_NAME", "Updated name")
    env_configuration.set("OBSIDIAN_SEARCH_INDEX_MAX_FILES", "250")
    env_configuration.set("WA_AUTH_DIR", "/tmp/xninetzy-session")
    secret = env_configuration.set("FLAZ_API_KEY", "private-value")

    content = env_configuration.env_path.read_text(encoding="utf-8")
    listed = env_configuration.list_fields(show_values=True)
    secret_get = env_configuration.get("FLAZ_API_KEY")

    assert result["configured"] is True
    assert "# Keep this comment" in content
    assert 'BOT_NAME="Updated name"' in content
    assert 'OBSIDIAN_SEARCH_INDEX_MAX_FILES="250"' in content
    assert 'WA_AUTH_DIR="/tmp/xninetzy-session"' in content
    assert "private-value" in content
    assert secret["secret"] is True
    assert "value" not in secret
    assert "value" not in secret_get
    assert next(item for item in listed if item["key"] == "BOT_NAME")["value"] == "Updated name"


def test_invalid_and_unknown_values_do_not_modify_configuration(env_configuration):
    before = env_configuration.env_path.read_text(encoding="utf-8") if env_configuration.env_path.exists() else ""

    with pytest.raises(ConfigurationError):
        env_configuration.set("OBSIDIAN_SEARCH_INDEX_MAX_FILES", "not-a-number")
    with pytest.raises(ConfigurationError):
        env_configuration.set("NOT_A_XNINETZY_SETTING", "value")

    assert env_configuration.env_path.read_text(encoding="utf-8") if env_configuration.env_path.exists() else "" == before


def test_unset_and_validate_report_unknown_and_invalid_values(env_configuration):
    env_configuration.set("BOT_NAME", "Xninetzy")
    env_configuration.set("FLAZ_API_KEY", "private-value")

    removed = env_configuration.unset("FLAZ_API_KEY")
    env_configuration.env_path.write_text(
        env_configuration.env_path.read_text(encoding="utf-8")
        + "UNKNOWN_SETTING=value\nOBSIDIAN_SEARCH_INDEX_MAX_FILES=invalid\n",
        encoding="utf-8",
    )
    validation = env_configuration.validate()

    assert removed["removed"] is True
    assert "FLAZ_API_KEY" not in env_configuration.values()
    assert validation["valid"] is False
    assert validation["unknown"] == ["UNKNOWN_SETTING"]
    assert validation["errors"][0]["key"] == "OBSIDIAN_SEARCH_INDEX_MAX_FILES"


def test_module_cli_writes_and_reads_a_selected_env_file(tmp_path):
    env_path = tmp_path / ".env"
    command = [
        sys.executable,
        "-m",
        "app.xninetzy.interfaces.config_cli",
        "set",
        "BOT_NAME",
        "CLI configured",
        "--env-file",
        str(env_path),
        "--json",
    ]
    written = subprocess.run(command, capture_output=True, text=True, check=False)
    read = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.xninetzy.interfaces.config_cli",
            "get",
            "BOT_NAME",
            "--env-file",
            str(env_path),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert written.returncode == 0, written.stderr
    assert read.returncode == 0, read.stderr
    assert json.loads(written.stdout)["configured"] is True
    assert json.loads(read.stdout)["value"] == "CLI configured"
    assert Settings(_env_file=env_path).BOT_NAME == "CLI configured"

