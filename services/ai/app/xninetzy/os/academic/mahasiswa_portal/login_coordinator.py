from __future__ import annotations

import asyncio
import re
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.academic.mahasiswa_portal.credential_provider import (
    resolve_campus_credentials,
)
from app.xninetzy.os.web_analysis.security import looks_like_login
from app.xninetzy.os.web_analysis.session_manager import SessionManager
from app.xninetzy.os.web_analysis.sites import get_site, is_allowed_url

logger = logging.getLogger(__name__)


class CampusLoginError(RuntimeError):
    pass


class CampusChallengeNotFound(CampusLoginError):
    pass


class CampusChallengeExpired(CampusLoginError):
    pass


@dataclass(slots=True)
class LoginChallenge:
    challenge_id: str
    owner_id: str
    playwright: Any
    browser: Any
    context: Any
    page: Any
    captcha_png: bytes
    created_at: datetime
    expires_at: datetime
    attempts: int = 0
    expiry_task: asyncio.Task | None = field(default=None, repr=False)


class CampusLoginCoordinator:
    def __init__(self) -> None:
        self._challenges: dict[str, LoginChallenge] = {}
        self._lock = asyncio.Lock()

    async def _first_visible(self, page: Any, selectors: tuple[str, ...]) -> Any:
        for selector in selectors:
            locator = page.locator(selector)
            count = await locator.count()
            if count == 1 and await locator.is_visible():
                return locator
        raise CampusLoginError(f"Elemen login tidak ditemukan secara unik: {selectors}")

    async def _captcha_image(self, page: Any) -> Any:
        for selector in (
            "img[src*='captcha' i]",
            "img[alt*='captcha' i]",
        ):
            locator = page.locator(selector)
            count = await locator.count()
            if count == 1 and await locator.is_visible():
                return locator
        captcha_input = await self._first_visible(
            page,
            (
                "input[name='captcha']",
                "input[name*='captcha' i]",
                "input[placeholder*='captcha' i]",
            ),
        )
        image = captcha_input.locator("xpath=preceding::img[1]")
        if await image.count() == 1 and await image.is_visible():
            return image
        raise CampusLoginError("Gambar CAPTCHA tidak ditemukan secara unik.")

    async def _fill_credentials(self, page: Any) -> None:
        source = get_settings().CYBER_CAMPUS_CREDENTIAL_SOURCE
        credentials = resolve_campus_credentials(source)
        username = await self._first_visible(
            page,
            ("input[name='username']", "input[name='nim']"),
        )
        password = await self._first_visible(
            page,
            ("input[name='password']", "input[type='password']"),
        )
        await username.fill(credentials.username)
        await password.fill(credentials.password.get_secret_value())

    async def _open_login_page(self, page: Any, url: str, timeout: int) -> Any:
        response = await page.goto(
            url,
            wait_until="commit",
            timeout=timeout,
        )
        await page.locator(
            "input[name='username'],input[name='nim']"
        ).first.wait_for(
            state="visible",
            timeout=timeout,
        )
        return response

    async def _capture_captcha(self, image: Any) -> bytes:
        try:
            payload = await image.evaluate(
                """
                async element => {
                  const source = element.currentSrc || element.src;
                  if (!source) throw new Error("CAPTCHA source missing");
                  const response = await fetch(source, {
                    credentials: "same-origin",
                    cache: "no-store"
                  });
                  if (!response.ok) throw new Error(`CAPTCHA image ${response.status}`);
                  return Array.from(new Uint8Array(await response.arrayBuffer()));
                }
                """
            )
            content = bytes(payload)
            if not 16 <= len(content) <= 2_000_000:
                raise CampusLoginError("Ukuran gambar CAPTCHA tidak valid.")
            return content
        except CampusLoginError:
            raise
        except Exception:
            return await image.screenshot(type="png", timeout=5_000)

    async def start(self, owner_id: str) -> dict[str, Any]:
        settings = get_settings()
        if not settings.CYBER_CAMPUS_ENABLED:
            raise CampusLoginError("CYBER_CAMPUS_ENABLED=false")
        SessionManager()
        async with self._lock:
            await self._cancel_owner_locked(owner_id)
            from playwright.async_api import async_playwright

            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=settings.CYBER_CAMPUS_BROWSER_HEADLESS
            )
            context = await browser.new_context(viewport={"width": 1280, "height": 900})
            page = await context.new_page()
            try:
                site = get_site("mahasiswa")
                await self._open_login_page(
                    page,
                    settings.CYBER_CAMPUS_BASE_URL,
                    settings.CYBER_CAMPUS_LOGIN_TIMEOUT_MS,
                )
                if not is_allowed_url(site, page.url):
                    raise CampusLoginError("Login keluar dari origin Cyber Campus.")
                await self._fill_credentials(page)
                captcha = await self._captcha_image(page)
                captcha_png = await self._capture_captcha(captcha)
                now = datetime.now(UTC)
                challenge_id = secrets.token_urlsafe(12)
                challenge = LoginChallenge(
                    challenge_id=challenge_id,
                    owner_id=owner_id,
                    playwright=playwright,
                    browser=browser,
                    context=context,
                    page=page,
                    captcha_png=captcha_png,
                    created_at=now,
                    expires_at=now
                    + timedelta(
                        seconds=settings.CYBER_CAMPUS_LOGIN_CHALLENGE_TTL_SECONDS
                    ),
                )
                self._challenges[challenge_id] = challenge
                challenge.expiry_task = asyncio.create_task(
                    self._expire(challenge_id)
                )
                challenge.expiry_task.add_done_callback(self._observe_expiry_task)
                return self._public_challenge(challenge)
            except Exception:
                await context.close()
                await browser.close()
                await playwright.stop()
                raise

    async def submit(
        self, challenge_id: str, owner_id: str, captcha_answer: str
    ) -> dict[str, Any]:
        answer = self.validate_captcha_answer(captcha_answer)
        async with self._lock:
            challenge = self._owned_challenge(challenge_id, owner_id)
            if datetime.now(UTC) > challenge.expires_at:
                await self._cancel_locked(challenge_id)
                raise CampusChallengeExpired("Challenge CAPTCHA sudah kedaluwarsa.")
            settings = get_settings()
            challenge.attempts += 1
            if challenge.attempts > settings.CYBER_CAMPUS_LOGIN_MAX_ATTEMPTS:
                await self._cancel_locked(challenge_id)
                raise CampusLoginError("Batas percobaan login tercapai.")
            captcha_input = await self._first_visible(
                challenge.page,
                (
                    "input[name='captcha']",
                    "input[name*='captcha' i]",
                    "input[placeholder*='captcha' i]",
                ),
            )
            login_button = await self._first_visible(
                challenge.page,
                (
                    "button[type='submit']",
                    "button:has-text('Login')",
                    "input[type='submit']",
                ),
            )
            await captcha_input.fill(answer)
            await login_button.click()
            try:
                await challenge.page.wait_for_load_state(
                    "domcontentloaded", timeout=settings.CYBER_CAMPUS_LOGIN_TIMEOUT_MS
                )
            except TimeoutError:
                logger.info("Cyber Campus login navigation timed out; validating DOM")
            html = await challenge.page.content()
            site = get_site("mahasiswa")
            authenticated = not looks_like_login(
                html, challenge.page.url
            ) and is_allowed_url(site, challenge.page.url)
            if not authenticated:
                await self._fill_credentials(challenge.page)
                captcha = await self._captcha_image(challenge.page)
                challenge.captcha_png = await self._capture_captcha(captcha)
                challenge.expires_at = datetime.now(UTC) + timedelta(
                    seconds=settings.CYBER_CAMPUS_LOGIN_CHALLENGE_TTL_SECONDS
                )
                return {
                    **self._public_challenge(challenge),
                    "authenticated": False,
                    "retry_required": True,
                    "remaining_attempts": settings.CYBER_CAMPUS_LOGIN_MAX_ATTEMPTS
                    - challenge.attempts,
                }
            storage_state = await challenge.context.storage_state()
            manager = SessionManager()
            manager.save_storage_state(
                "mahasiswa",
                storage_state,
                landing_url=challenge.page.url,
            )
            result = {
                "authenticated": True,
                "current_url": challenge.page.url,
                "title": await challenge.page.title(),
            }
            await self._cancel_locked(challenge_id)
            return result

    async def cancel(self, challenge_id: str, owner_id: str) -> bool:
        async with self._lock:
            self._owned_challenge(challenge_id, owner_id)
            return await self._cancel_locked(challenge_id)

    async def captcha_png(self, challenge_id: str, owner_id: str) -> bytes:
        async with self._lock:
            return bytes(self._owned_challenge(challenge_id, owner_id).captcha_png)

    async def _expire(self, challenge_id: str) -> None:
        while True:
            async with self._lock:
                challenge = self._challenges.get(challenge_id)
                if not challenge:
                    return
                delay = (
                    challenge.expires_at - datetime.now(UTC)
                ).total_seconds()
                if delay <= 0:
                    await self._cancel_locked(challenge_id, cancel_expiry=False)
                    return
            await asyncio.sleep(delay)

    def _observe_expiry_task(self, task: asyncio.Task) -> None:
        if task.cancelled():
            return
        error = task.exception()
        if error:
            logger.error("Campus login expiry task failed: %s", error)

    def _owned_challenge(self, challenge_id: str, owner_id: str) -> LoginChallenge:
        challenge = self._challenges.get(challenge_id)
        if not challenge:
            raise CampusChallengeNotFound("Challenge login tidak ditemukan.")
        if challenge.owner_id != owner_id:
            raise PermissionError("Challenge login bukan milik owner ini.")
        return challenge

    async def _cancel_owner_locked(self, owner_id: str) -> None:
        challenge_ids = [
            challenge_id
            for challenge_id, challenge in self._challenges.items()
            if challenge.owner_id == owner_id
        ]
        for challenge_id in challenge_ids:
            await self._cancel_locked(challenge_id)

    async def _cancel_locked(
        self, challenge_id: str, cancel_expiry: bool = True
    ) -> bool:
        challenge = self._challenges.pop(challenge_id, None)
        if not challenge:
            return False
        current_task = asyncio.current_task()
        if (
            cancel_expiry
            and challenge.expiry_task
            and challenge.expiry_task is not current_task
        ):
            challenge.expiry_task.cancel()
        try:
            await challenge.context.close()
        finally:
            try:
                await challenge.browser.close()
            finally:
                await challenge.playwright.stop()
        challenge.captcha_png = b""
        return True

    @staticmethod
    def validate_captcha_answer(answer: str) -> str:
        normalized = answer.strip()
        if not 1 <= len(normalized) <= 32:
            raise ValueError("Format jawaban CAPTCHA tidak valid.")
        if not re.fullmatch(r"[A-Za-z0-9+*/=_-]+", normalized):
            raise ValueError("Format jawaban CAPTCHA tidak valid.")
        return normalized

    @staticmethod
    def _public_challenge(challenge: LoginChallenge) -> dict[str, Any]:
        return {
            "challenge_id": challenge.challenge_id,
            "expires_at": challenge.expires_at.isoformat(),
            "attempts": challenge.attempts,
        }


LOGIN_COORDINATOR = CampusLoginCoordinator()
