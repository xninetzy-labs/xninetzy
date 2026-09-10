import pytest

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.academic.mahasiswa_portal.login_coordinator import (
    CampusLoginCoordinator,
)
from app.xninetzy.os.web_analysis.sites import get_site


@pytest.mark.parametrize("answer", ["ABC9", "A1-2", "12+7", "token_value"])
def test_captcha_answer_accepts_bounded_manual_input(answer):
    assert CampusLoginCoordinator.validate_captcha_answer(answer) == answer


@pytest.mark.parametrize("answer", ["", "contains space", "<script>", "a" * 33])
def test_captcha_answer_rejects_invalid_input(answer):
    with pytest.raises(ValueError, match="Format jawaban CAPTCHA"):
        CampusLoginCoordinator.validate_captcha_answer(answer)


@pytest.mark.asyncio
async def test_captcha_capture_reads_image_bytes_without_screenshot():
    class Image:
        screenshot_called = False

        async def evaluate(self, script):
            return list(b"valid-captcha-image-bytes")

        async def screenshot(self, **kwargs):
            self.screenshot_called = True
            return b"fallback"

    image = Image()
    content = await CampusLoginCoordinator()._capture_captcha(image)

    assert content == b"valid-captcha-image-bytes"
    assert image.screenshot_called is False


@pytest.mark.asyncio
async def test_captcha_capture_uses_bounded_screenshot_fallback():
    class Image:
        timeout = None

        async def evaluate(self, script):
            raise RuntimeError("fetch unavailable")

        async def screenshot(self, **kwargs):
            self.timeout = kwargs["timeout"]
            return b"fallback-captcha"

    image = Image()
    content = await CampusLoginCoordinator()._capture_captcha(image)

    assert content == b"fallback-captcha"
    assert image.timeout == 5_000


@pytest.mark.asyncio
async def test_login_bootstrap_waits_for_commit_and_visible_username():
    class First:
        state = ""
        timeout = 0

        async def wait_for(self, state, timeout):
            self.state = state
            self.timeout = timeout

    class Locator:
        first = First()

    class Page:
        goto_args = None
        selector = ""
        locator_result = Locator()

        async def goto(self, url, **kwargs):
            self.goto_args = (url, kwargs)
            return "response"

        def locator(self, selector):
            self.selector = selector
            return self.locator_result

    page = Page()
    result = await CampusLoginCoordinator()._open_login_page(
        page,
        "https://mahasiswa.unair.ac.id",
        30_000,
    )

    assert result == "response"
    assert page.goto_args[1]["wait_until"] == "commit"
    assert page.locator_result.first.state == "visible"
    assert page.locator_result.first.timeout == 30_000


@pytest.mark.asyncio
async def test_find_captcha_optional_returns_none_when_absent():
    class Locator:
        def __init__(self, count, visible):
            self._count = count
            self._visible = visible

        async def count(self):
            return self._count

        async def is_visible(self):
            return self._visible

    class Page:
        def __init__(self):
            self.selectors = []

        def locator(self, selector):
            self.selectors.append(selector)
            return Locator(0, False)

    page = Page()
    result = await CampusLoginCoordinator()._find_captcha_optional(page)
    assert result is None
    assert any("captcha" in selector for selector in page.selectors)


@pytest.mark.asyncio
async def test_find_captcha_optional_returns_image_when_present():
    class Locator:
        def __init__(self, count, visible):
            self._count = count
            self._visible = visible

        async def count(self):
            return self._count

        async def is_visible(self):
            return self._visible

    class Page:
        def locator(self, selector):
            if "captcha" in selector:
                return Locator(1, True)
            return Locator(0, False)

    result = await CampusLoginCoordinator()._find_captcha_optional(Page())
    assert result is not None


@pytest.mark.asyncio
async def test_try_direct_login_saves_session_on_success(monkeypatch):
    coordinator = CampusLoginCoordinator()
    saved = {}

    class Button:
        clicked = False

        async def click(self):
            self.clicked = True

    class Page:
        url = "https://uacc.unair.ac.id/mhs"

        async def title(self):
            return "Dashboard"

        async def content(self):
            return "<html>dashboard</html>"

        async def wait_for_load_state(self, state, timeout):
            pass

    class Context:
        async def storage_state(self):
            return {"cookies": []}

    class FakeSessionManager:
        def save_storage_state(self, site_slug, storage_state, landing_url=None):
            saved["site_slug"] = site_slug
            saved["storage_state"] = storage_state
            saved["landing_url"] = landing_url

    button = Button()

    async def fake_first_visible(page, selectors):
        return button

    monkeypatch.setattr(coordinator, "_first_visible", fake_first_visible)
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.login_coordinator.looks_like_login",
        lambda html, url: False,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.login_coordinator.is_allowed_url",
        lambda site, url: True,
    )
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.login_coordinator.SessionManager",
        FakeSessionManager,
    )

    site = get_site("uacc")
    config = type("Config", (), {"label": "UACC", "timeout_ms": 30_000})()
    result = await coordinator._try_direct_login(Page(), Context(), site, config)

    assert button.clicked is True
    assert result["authenticated"] is True
    assert saved["site_slug"] == "uacc"
    assert saved["landing_url"] == "https://uacc.unair.ac.id/mhs"


@pytest.mark.asyncio
async def test_try_direct_login_returns_none_when_still_login_page(monkeypatch):
    coordinator = CampusLoginCoordinator()

    class Button:
        async def click(self):
            pass

    class Page:
        url = "https://uacc.unair.ac.id/mhs"

        async def content(self):
            return "<html>login form</html>"

        async def wait_for_load_state(self, state, timeout):
            pass

    class Context:
        async def storage_state(self):
            return {"cookies": []}

    async def fake_first_visible(page, selectors):
        return Button()

    monkeypatch.setattr(coordinator, "_first_visible", fake_first_visible)
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.login_coordinator.looks_like_login",
        lambda html, url: True,
    )

    site = get_site("uacc")
    config = type("Config", (), {"label": "UACC", "timeout_ms": 30_000})()
    result = await coordinator._try_direct_login(Page(), Context(), site, config)
    assert result is None


def _uacc_settings(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "UACC_ENABLED", True)
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.login_coordinator.get_settings",
        lambda: settings,
    )
    return settings


def _fake_playwright():
    class FakeContext:
        async def new_page(self):
            return type("Page", (), {"url": "https://uacc.unair.ac.id/mhs"})()

        async def close(self):
            pass

    class FakeBrowser:
        async def new_context(self, **kwargs):
            return FakeContext()

        async def close(self):
            pass

    async def _launch(**kwargs):
        return FakeBrowser()

    class FakePlaywright:
        chromium = type("Chromium", (), {"launch": staticmethod(_launch)})()

        async def start(self):
            return self

        async def stop(self):
            pass

    return FakePlaywright()


@pytest.mark.asyncio
async def test_start_direct_login_when_no_captcha(monkeypatch):
    _uacc_settings(monkeypatch)
    coordinator = CampusLoginCoordinator()

    async def fake_open(page, url, timeout):
        pass

    async def fake_fill(page, source):
        pass

    async def fake_no_captcha(page):
        return None

    async def fake_direct(page, context, site, config):
        return {
            "authenticated": True,
            "current_url": "https://uacc.unair.ac.id/mhs",
            "title": "Dashboard",
        }

    monkeypatch.setattr(coordinator, "_open_login_page", fake_open)
    monkeypatch.setattr(coordinator, "_fill_credentials", fake_fill)
    monkeypatch.setattr(coordinator, "_find_captcha_optional", fake_no_captcha)
    monkeypatch.setattr(coordinator, "_try_direct_login", fake_direct)
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.login_coordinator.SessionManager",
        type("SM", (), {}),
    )
    monkeypatch.setattr(
        "playwright.async_api.async_playwright", lambda: _fake_playwright()
    )

    result = await coordinator.start("owner", site_slug="uacc")

    assert result["authenticated"] is True
    assert result["current_url"] == "https://uacc.unair.ac.id/mhs"
    assert coordinator._challenges == {}


@pytest.mark.asyncio
async def test_start_keeps_captcha_challenge_when_captcha_present(monkeypatch):
    _uacc_settings(monkeypatch)
    coordinator = CampusLoginCoordinator()

    async def fake_open(page, url, timeout):
        pass

    async def fake_fill(page, source):
        pass

    async def fake_captcha(page):
        return object()

    async def fake_capture(image):
        return b"png"

    monkeypatch.setattr(coordinator, "_open_login_page", fake_open)
    monkeypatch.setattr(coordinator, "_fill_credentials", fake_fill)
    monkeypatch.setattr(coordinator, "_find_captcha_optional", fake_captcha)
    monkeypatch.setattr(coordinator, "_capture_captcha", fake_capture)
    monkeypatch.setattr(
        "app.xninetzy.os.academic.mahasiswa_portal.login_coordinator.SessionManager",
        type("SM", (), {}),
    )
    monkeypatch.setattr(
        "playwright.async_api.async_playwright", lambda: _fake_playwright()
    )

    result = await coordinator.start("owner", site_slug="uacc")

    assert "challenge_id" in result
    assert len(coordinator._challenges) == 1
    await coordinator.cancel(result["challenge_id"], "owner")
    assert coordinator._challenges == {}
