from __future__ import annotations

from xninetzy.context.capability_graph.match_cache import (
    cache_size,
    clear_cache,
    token_id,
    tokenize_cached,
)


def setup_function(_fn):
    clear_cache()


def teardown_function(_fn):
    clear_cache()


def test_tokenize_cached_returns_frozenset():
    out = tokenize_cached("hello world")
    assert isinstance(out, frozenset)


def test_tokenize_cached_dedupes_across_calls():
    a = tokenize_cached("hello world")
    b = tokenize_cached("world hello")
    assert a == b


def test_tokenize_cached_drops_short_tokens():
    out = tokenize_cached("a b c hello")
    assert "hello" in out
    assert "a" not in out


def test_tokenize_cached_empty_input():
    assert tokenize_cached("") == frozenset()
    assert tokenize_cached(None) == frozenset()


def test_tokenize_cached_handles_punctuation():
    out = tokenize_cached("hello-world/foo.bar")
    assert "hello" in out
    assert "world" in out
    assert "foo" in out
    assert "bar" in out


def test_token_id_returns_same_id_for_same_tokens():
    a = token_id("alpha beta")
    b = token_id("beta alpha")
    assert a == b


def test_token_id_distinguishes_different_tokens():
    a = token_id("alpha beta")
    b = token_id("gamma delta")
    assert a != b


def test_token_id_grows_cache_size():
    token_id("one")
    token_id("two")
    token_id("three")
    assert cache_size() >= 2


def test_clear_cache_resets_state():
    token_id("alpha")
    clear_cache()
    assert cache_size() == 0
    assert token_id("alpha") >= 1
