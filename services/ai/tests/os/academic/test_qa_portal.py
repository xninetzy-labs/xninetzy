from __future__ import annotations

import pytest

from app.xninetzy.os.academic.qa_portal.automation import _fresh_captcha_token


@pytest.mark.asyncio
async def test_qa_captcha_waits_for_stable_page_token():
    calls = []

    class Page:
        async def evaluate(self, script, *args):
            calls.append((script, args))
            return {"tokenLength": 1337, "action": "validate_captcha"}

        async def wait_for_timeout(self, _milliseconds):
            return None

    await _fresh_captcha_token(Page())

    assert len(calls) == 2
    assert all("grecaptcha.execute" not in call[0] for call in calls)


@pytest.mark.asyncio
async def test_qa_captcha_failure_requires_human_verification():
    from app.xninetzy.os.academic.qa_portal.automation import (
        QaHumanVerificationRequired,
    )

    class Page:
        async def evaluate(self, script, *args):
            return False

        async def wait_for_timeout(self, _milliseconds):
            return None

    with pytest.raises(QaHumanVerificationRequired, match="verifikasi manusia"):
        await _fresh_captcha_token(Page())
