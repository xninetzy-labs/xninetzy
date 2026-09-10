from __future__ import annotations

from scripts import configure_flaz


def test_configure_flaz_uses_getpass_and_never_prints_secret(
    tmp_path, monkeypatch, capsys
):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "FLAZ_API_KEY=\nFLAZ_BASE_URL=old\nFLAZ_MODEL=old\nKEEP_ME=yes\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(configure_flaz, "ENV_PATH", env_path)
    monkeypatch.setattr(
        configure_flaz.getpass, "getpass", lambda prompt: "private-test-key"
    )

    configure_flaz.main()

    output = capsys.readouterr().out
    saved = env_path.read_text(encoding="utf-8")
    assert "private-test-key" not in output
    assert "FLAZ_API_KEY=private-test-key" in saved
    assert "FLAZ_BASE_URL=https://ai.flaz.id/v1" in saved
    assert "FLAZ_MODEL=deepseek-v4-pro" in saved
    assert "KEEP_ME=yes" in saved
    assert env_path.stat().st_mode & 0o777 == 0o600
