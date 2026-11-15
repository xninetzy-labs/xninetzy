from pathlib import Path

import pytest

from scripts.check_installed_package import compare_package_files


@pytest.mark.parametrize("change", ["none", "source_changed", "asset_missing", "obsolete_installed"])
def test_installed_wheel_integrity(tmp_path: Path, change: str):
    source, installed = tmp_path / "source", tmp_path / "installed"
    for root in (source, installed):
        root.mkdir()
        (root / "module.py").write_text("VERSION = 1\n")
        (root / "policy.json").write_text('{"version":1}')
    if change == "source_changed":
        (source / "module.py").write_text("VERSION = 2\n")
    elif change == "asset_missing":
        (installed / "policy.json").unlink()
    elif change == "obsolete_installed":
        (installed / "obsolete.py").write_text("OLD = True\n")
    result = compare_package_files(source, installed)
    assert result["ok"] is (change == "none")
    assert result["files_checked"] == 2


def test_source_checkout_cannot_masquerade_as_installed_package(tmp_path):
    with pytest.raises(ValueError, match="shadowed"):
        compare_package_files(tmp_path, tmp_path)


def test_explicitly_excluded_source_test_package_is_not_runtime_code(tmp_path):
    source, installed = tmp_path / "source", tmp_path / "installed"
    for root in (source, installed):
        root.mkdir()
        (root / "runtime.py").write_text("RUNTIME = True\n")
    (source / "tests").mkdir()
    (source / "tests" / "__init__.py").write_text("")
    assert compare_package_files(source, installed)["ok"]
    # Unexpected installed files remain detectable; exclusion is source-only.
    (installed / "tests").mkdir()
    (installed / "tests" / "__init__.py").write_text("")
    assert not compare_package_files(source, installed)["ok"]
