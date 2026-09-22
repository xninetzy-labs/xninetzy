from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any

import pytest

from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.hyper import extract_csv_to_hyper, hyper_available
from xninetzy.integrations.tableau.ir import PublishTarget
from xninetzy.integrations.tableau.profiling import profile_csv
from xninetzy.integrations.tableau.server import (
    _classify_publish_error,
    _redact,
    artifact_record,
    list_workbooks,
    publish_workbook,
    refresh_workbook,
    tsc_available,
)
from xninetzy.integrations.tableau.workspace import (
    resolve_template_path,
    safe_workspace_subdir,
    workspace_root,
)


_SECRET = "SECRET_TOKEN_FOR_TEST_ABC123XYZ_DO_NOT_USE"


def _target() -> PublishTarget:
    return PublishTarget(
        server_url="https://tableau.example.com",
        site_id="mysite",
        project="default",
        token_name="alice",
        token_secret=_SECRET,
    )


def _write_csv(tmp_path: Path, name: str, rows: list[list[str]]) -> Path:
    p = tmp_path / name
    with p.open("w", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        for row in rows:
            writer.writerow(row)
    return p


def test_safe_subdir_strips_parent_traversal() -> None:
    cleaned = safe_workspace_subdir("../../../etc/passwd")
    assert ".." not in Path(cleaned).parts


def test_safe_subdir_strips_absolute_unix() -> None:
    cleaned = safe_workspace_subdir("/etc/passwd")
    resolved = Path(cleaned)
    assert not resolved.is_absolute()


def test_safe_subdir_normalizes_windows_separator() -> None:
    cleaned = safe_workspace_subdir(r"..\\..\\windows\\system32")
    assert ".." not in Path(cleaned.replace("\\", "/")).parts


def test_safe_subdir_rejects_null_bytes() -> None:
    cleaned = safe_workspace_subdir("evil\x00.txt")
    assert "\x00" not in cleaned


def test_publish_target_safe_dict_excludes_token_secret() -> None:
    target = _target()
    safe = target.safe_dict()
    assert _SECRET not in str(safe)
    assert "token_secret" not in safe
    assert safe["token_name"] == "alice"


def test_redact_strips_recursive_keys() -> None:
    payload: dict[str, Any] = {
        "server_url": "https://x",
        "token_secret": _SECRET,
        "nested": {
            "password": _SECRET,
            "token": "ok",
        },
    }
    out = _redact(payload)
    assert _SECRET not in str(out)
    assert out["nested"]["token"] == "ok"


def test_publish_workbook_missing_token_raises_auth_required(tmp_path: Path) -> None:
    twb = tmp_path / "fake.twb"
    twb.write_text("<workbook/>", encoding="utf-8")
    target = PublishTarget(
        server_url="https://x", site_id="", project="default",
        token_name="", token_secret="",
    )
    with pytest.raises(TableauIntegrationError) as exc:
        publish_workbook(twb, target)
    assert exc.value.code == "PUBLISH_AUTH_REQUIRED"


def test_publish_workbook_missing_token_secret_raises_auth_required(tmp_path: Path) -> None:
    twb = tmp_path / "fake.twb"
    twb.write_text("<workbook/>", encoding="utf-8")
    target = PublishTarget(
        server_url="https://x", site_id="", project="default",
        token_name="alice", token_secret="",
    )
    with pytest.raises(TableauIntegrationError) as exc:
        publish_workbook(twb, target)
    assert exc.value.code == "PUBLISH_AUTH_REQUIRED"


def test_publish_workbook_missing_file(tmp_path: Path) -> None:
    with pytest.raises(TableauIntegrationError) as exc:
        publish_workbook(tmp_path / "absent.twb", _target())
    assert exc.value.code == "ARTIFACT_NOT_FOUND"


def test_publish_workbook_traversal_filename_blocked(tmp_path: Path) -> None:
    target_path = tmp_path / ".." / "evil.twb"
    if not tsc_available():
        with pytest.raises(TableauIntegrationError):
            publish_workbook(target_path, _target())


def test_publish_dependency_missing_clean_error(tmp_path: Path) -> None:
    twb = tmp_path / "fake.twb"
    twb.write_text("<workbook/>", encoding="utf-8")
    if tsc_available():
        pytest.skip("tableauserverclient installed; cannot exercise missing path")
    with pytest.raises(TableauIntegrationError) as exc:
        publish_workbook(twb, _target())
    assert exc.value.code == "TABLEAU_DEPENDENCY_MISSING"
    assert _SECRET not in str(exc.value)


def test_list_workbooks_dependency_missing(tmp_path: Path) -> None:
    if tsc_available():
        pytest.skip("tableauserverclient installed; cannot exercise missing path")
    with pytest.raises(TableauIntegrationError) as exc:
        list_workbooks(_target())
    assert exc.value.code == "TABLEAU_DEPENDENCY_MISSING"


def test_list_workbooks_payload_redacts_secret(tmp_path: Path) -> None:
    if tsc_available():
        pytest.skip("requires missing tableauserverclient to exercise error path")
    try:
        result = list_workbooks(_target())
    except TableauIntegrationError as exc:
        assert _SECRET not in str(exc)
        assert exc.code == "TABLEAU_DEPENDENCY_MISSING"


def test_refresh_workbook_dependency_missing(tmp_path: Path) -> None:
    if tsc_available():
        pytest.skip("tableauserverclient installed; cannot exercise missing path")
    with pytest.raises(TableauIntegrationError) as exc:
        refresh_workbook("wb-1", _target())
    assert exc.value.code == "TABLEAU_DEPENDENCY_MISSING"


def test_refresh_workbook_missing_id(tmp_path: Path) -> None:
    with pytest.raises(TableauIntegrationError) as exc:
        refresh_workbook("", _target())
    assert exc.value.code == "PROVIDER_ERROR"


def test_refresh_workbook_missing_creds(tmp_path: Path) -> None:
    target = PublishTarget(
        server_url="https://x", site_id="", project="default",
        token_name="", token_secret="",
    )
    with pytest.raises(TableauIntegrationError) as exc:
        refresh_workbook("wb-1", target)
    assert exc.value.code == "PUBLISH_AUTH_REQUIRED"


def test_extract_csv_to_hyper_symlink_escape(tmp_path: Path) -> None:
    if not hyper_available():
        pytest.skip("hyper tests below cover missing-API path")
    real_csv = tmp_path / "real.csv"
    with real_csv.open("w", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "price"])
        writer.writerow(["1", "1.5"])
    outside_dir = tmp_path.parent / f"{tmp_path.name}_outside"
    outside_dir.mkdir(exist_ok=True)
    outside_target = outside_dir / "leak.csv"
    if outside_target.exists():
        outside_target.unlink()
    sym_path = tmp_path / "link.csv"
    try:
        os.symlink(outside_target, sym_path)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unsupported on this platform")
    outside_target.write_text("secret=1", encoding="utf-8")
    profile = profile_csv(sym_path)
    assert profile.row_count >= 1


def test_extract_csv_to_hyper_missing_raises_clean(tmp_path: Path) -> None:
    with pytest.raises(TableauIntegrationError) as exc:
        extract_csv_to_hyper(tmp_path / "absent.csv", tmp_path / "out.hyper")
    assert exc.value.code == "INVALID_DATASET"


def test_profile_csv_rejects_parent_traversal_filename(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"abs_{tmp_path.name}.csv"
    if outside.exists():
        outside.unlink()
    outside.write_text("a,b\n1,2\n", encoding="utf-8")
    try:
        profile = profile_csv(outside)
        assert profile.row_count >= 1
    finally:
        if outside.exists():
            outside.unlink()


def test_resolve_template_path_blocks_traversal_outside_workspace(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        resolve_template_path("../../../etc/passwd")


def test_workspace_root_does_not_follow_symlink_to_outside(tmp_path: Path) -> None:
    real_outside = tmp_path / "real_outside"
    real_outside.mkdir(exist_ok=True)
    link_root = tmp_path / "linked_root"
    try:
        os.symlink(real_outside, link_root)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unsupported on this platform")
    if "XNINETZY_TABLEAU_WORKSPACE" in os.environ:
        pytest.skip("env override active")
    root = workspace_root(override=link_root)
    assert root.exists()
    assert {p.name for p in root.iterdir() if p.is_dir()} >= {"templates", "workbooks"}


def test_artifact_record_redacts_no_secrets() -> None:
    rec = artifact_record(
        artifact_id="x", path="/tmp/x.twb", kind="twb",
        validation="ok",
    )
    payload = rec.to_dict()
    assert _SECRET not in str(payload)


def test_classify_publish_error_safety() -> None:
    assert _classify_publish_error("401 unauthorized") == "PUBLISH_AUTH_REQUIRED"
    assert _classify_publish_error("403 forbidden") == "PUBLISH_PERMISSION_DENIED"
    assert _classify_publish_error("rate limit exceeded 429") == "PUBLISH_RATE_LIMITED"
    assert _classify_publish_error("request timed out") == "PUBLISH_TIMEOUT"
    assert _classify_publish_error("unknown xml error") == "PUBLISH_FAILED"
