import pytest

from app.xninetzy.os.academic.mahasiswa_portal.login_coordinator import (
    CampusLoginCoordinator,
)


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
