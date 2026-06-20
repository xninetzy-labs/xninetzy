from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.os.style.store import format_style_for_prompt, get_style_text, reset_style, set_style

U = "style-test-user"


def _setup():
    init_db()
    run_migrations()


def test_set_and_get_style():
    _setup()
    u = U + "-1"
    set_style(u, "santai, teknis, to the point")
    assert get_style_text(u) == "santai, teknis, to the point"


def test_set_style_overwrites():
    _setup()
    u = U + "-2"
    set_style(u, "formal")
    set_style(u, "casual")
    assert get_style_text(u) == "casual"


def test_reset_style():
    _setup()
    u = U + "-3"
    set_style(u, "santai")
    assert reset_style(u) is True
    assert get_style_text(u) == ""


def test_format_style_for_prompt():
    _setup()
    u = U + "-4"
    reset_style(u)  # ensure clean state (pytest DB persists across runs)
    assert format_style_for_prompt(u) == ""
    set_style(u, "ringkas")
    out = format_style_for_prompt(u)
    assert "ringkas" in out and "Gaya jawaban" in out
