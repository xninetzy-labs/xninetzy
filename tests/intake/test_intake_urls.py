from __future__ import annotations

import pytest

from xninetzy.context.intake.urls import (
    URL_KIND_GITHUB,
    URL_KIND_LOCAL,
    URL_KIND_RAW_GITHUB,
    URL_KIND_UNKNOWN,
    canonicalize_github_url,
    detect_url_kind,
    parse_github_url,
    parse_local_path,
    parse_url,
    parse_raw_github_url,
    sha256_hex,
)


def test_sha256_hex_is_deterministic_and_hex():
    assert sha256_hex("hello") == sha256_hex("hello")
    assert sha256_hex("hello") != sha256_hex("world")
    assert len(sha256_hex("xninetzy")) == 64
    assert all(ch in "0123456789abcdef" for ch in sha256_hex("xninetzy"))


def test_detect_url_kind_github_variants():
    assert detect_url_kind("https://github.com/foo/bar") == URL_KIND_GITHUB
    assert detect_url_kind("https://www.github.com/foo/bar") == URL_KIND_GITHUB
    assert detect_url_kind("https://github.com/foo/bar.git") == URL_KIND_GITHUB
    assert detect_url_kind("https://raw.githubusercontent.com/foo/bar/main/x.py") == URL_KIND_RAW_GITHUB
    assert detect_url_kind("") == URL_KIND_UNKNOWN
    assert detect_url_kind("ftp://example.com/x") == URL_KIND_UNKNOWN


def test_detect_url_kind_local():
    assert detect_url_kind("/tmp/repo") == URL_KIND_LOCAL
    assert detect_url_kind("./local/dir") == URL_KIND_LOCAL
    assert detect_url_kind("file:///var/data") == URL_KIND_LOCAL


def test_parse_github_url_extracts_owner_repo():
    parsed = parse_github_url("https://github.com/anthropics/anthropic-sdk-python")
    assert parsed.owner == "anthropics"
    assert parsed.repo == "anthropic-sdk-python"
    assert parsed.canonical == "https://github.com/anthropics/anthropic-sdk-python"
    assert parsed.ref is None


def test_parse_github_url_strips_git_suffix():
    parsed = parse_github_url("https://github.com/foo/bar.git")
    assert parsed.repo == "bar"


def test_parse_github_url_blob_extracts_ref_and_subpath():
    parsed = parse_github_url("https://github.com/foo/bar/blob/main/src/x.py")
    assert parsed.owner == "foo"
    assert parsed.repo == "bar"
    assert parsed.ref == "main"
    assert parsed.subpath == "src/x.py"


def test_parse_github_url_tree_extracts_subpath():
    parsed = parse_github_url("https://github.com/foo/bar/tree/main/src")
    assert parsed.ref == "main"
    assert parsed.subpath == "src"


def test_parse_github_url_strips_query_and_fragment():
    parsed = parse_github_url("https://github.com/foo/bar?ref=abc#readme")
    assert parsed.owner == "foo"
    assert parsed.repo == "bar"
    assert "ref=abc" not in parsed.raw


def test_parse_github_url_rejects_non_github_host():
    with pytest.raises(ValueError):
        parse_github_url("https://gitlab.com/foo/bar")


def test_parse_github_url_rejects_empty_path():
    with pytest.raises(ValueError):
        parse_github_url("https://github.com/")


def test_parse_raw_github_url_extracts_ref():
    parsed = parse_raw_github_url(
        "https://raw.githubusercontent.com/foo/bar/main/README.md"
    )
    assert parsed.owner == "foo"
    assert parsed.repo == "bar"
    assert parsed.ref == "main"
    assert parsed.subpath == "README.md"


def test_parse_raw_github_url_handles_at_ref_form():
    parsed = parse_raw_github_url(
        "https://raw.githubusercontent.com/foo/bar@v1.2.3/src/x.py"
    )
    assert parsed.ref == "v1.2.3"
    assert parsed.subpath == "src/x.py"


def test_parse_local_path_uses_path_name_as_repo(tmp_path):
    parsed = parse_local_path(str(tmp_path / "demo"))
    assert parsed.name == URL_KIND_LOCAL
    assert parsed.repo == "demo"


def test_parse_local_path_handles_file_scheme(tmp_path):
    parsed = parse_local_path(f"file://{tmp_path / 'x'}")
    assert parsed.name == URL_KIND_LOCAL


def test_canonicalize_github_url_returns_canonical_field():
    parsed = parse_github_url("https://github.com/foo/bar/blob/main/x.py")
    assert canonicalize_github_url(parsed) == "https://github.com/foo/bar"


def test_parse_url_dispatches_to_correct_parser():
    parsed = parse_url("https://github.com/foo/bar")
    assert parsed.name == URL_KIND_GITHUB
    parsed = parse_url("/tmp/anything")
    assert parsed.name == URL_KIND_LOCAL


def test_parse_url_raises_on_unknown():
    with pytest.raises(ValueError):
        parse_url("https://example.com/foo")
