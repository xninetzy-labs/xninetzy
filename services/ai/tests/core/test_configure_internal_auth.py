from pathlib import Path

from scripts import configure_internal_auth


def test_internal_auth_configuration_preserves_values_and_generates_missing_keys(
    monkeypatch,
    tmp_path: Path,
):
    example = tmp_path / ".env.example"
    environment = tmp_path / ".env"
    example.write_text(
        "AI_API_KEY=\nMCP_API_KEY=\nWA_MCP_API_KEY=\nADMIN_JID=\nNEW_SETTING=default\n",
        encoding="utf-8",
    )
    environment.write_text(
        "FLAZ_API_KEY=keep-this\nHEBAT_NOTIFY_CHAT_ID=628123@s.whatsapp.net\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(configure_internal_auth, "ENV_EXAMPLE_PATH", example)
    monkeypatch.setattr(configure_internal_auth, "ENV_PATH", environment)

    configure_internal_auth.main()
    first = configure_internal_auth.read_values(environment)
    configure_internal_auth.main()
    second = configure_internal_auth.read_values(environment)

    assert first["FLAZ_API_KEY"] == "keep-this"
    assert first["NEW_SETTING"] == "default"
    assert first["AI_API_KEY"]
    assert first["MCP_API_KEY"] == first["WA_MCP_API_KEY"]
    assert first["ADMIN_JID"] == "628123@s.whatsapp.net"
    assert second == first
    assert environment.stat().st_mode & 0o777 == 0o600


def test_internal_auth_can_enable_cyber_campus_safely(monkeypatch, tmp_path: Path):
    example = tmp_path / ".env.example"
    environment = tmp_path / ".env"
    example.write_text(
        "AI_API_KEY=\nMCP_API_KEY=\nWA_MCP_API_KEY=\nWEB_ANALYSIS_ENCRYPTION_KEY=\n",
        encoding="utf-8",
    )
    environment.write_text(
        "HEBAT_USERNAME=owner\n"
        "HEBAT_PASSWORD=secret\n"
        "ADMIN_JID=628123@s.whatsapp.net\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(configure_internal_auth, "ENV_EXAMPLE_PATH", example)
    monkeypatch.setattr(configure_internal_auth, "ENV_PATH", environment)

    configure_internal_auth.main(enable_cyber_campus=True)
    values = configure_internal_auth.read_values(environment)

    assert values["CYBER_CAMPUS_ENABLED"] == "true"
    assert values["WEB_ANALYSIS_AUTHENTICATED_CRAWL_ENABLED"] == "true"
    assert values["WEB_ANALYSIS_ENCRYPTION_KEY"]
    assert values["HEBAT_PASSWORD"] == "secret"
