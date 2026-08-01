from __future__ import annotations

import pytest

from app.xninetzy.os.academic.qa_portal.automation import _fresh_captcha_token


@pytest.mark.asyncio
async def test_qa_captcha_preserves_expected_form_action():
    calls = []

    class Page:
        async def evaluate(self, script, *args):
            calls.append((script, args))
            if "grecaptcha" in script:
                return True
            return None

        async def wait_for_timeout(self, _milliseconds):
            return None

    await _fresh_captcha_token(Page())

    assert len(calls) == 2
    assert calls[1][1] == ("validate_captcha",)
