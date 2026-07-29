from __future__ import annotations

import asyncio
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.identity import normalize_whatsapp_jid


class GradeChallengeError(RuntimeError):
    pass


@dataclass(slots=True)
class GradeChallenge:
    challenge_id: str
    owner_id: str
    academic_period: str
    expires_at: datetime
    attempts: int = 0


class GradeTokenCoordinator:
    def __init__(self) -> None:
        self._challenges: dict[str, GradeChallenge] = {}
        self._lock = asyncio.Lock()

    async def start(self, owner_id: str, academic_period: str = "latest") -> dict:
        normalized_owner = normalize_whatsapp_jid(owner_id)
        if not normalized_owner:
            raise GradeChallengeError("WhatsApp owner belum dikonfigurasi.")
        settings = get_settings()
        now = datetime.now(UTC)
        challenge = GradeChallenge(
            challenge_id=secrets.token_urlsafe(9),
            owner_id=normalized_owner,
            academic_period=academic_period.strip() or "latest",
            expires_at=now
            + timedelta(seconds=settings.CYBER_CAMPUS_GRADE_TOKEN_TTL_SECONDS),
        )
        async with self._lock:
            self._purge(now)
            for challenge_id, current in tuple(self._challenges.items()):
                if current.owner_id == normalized_owner:
                    self._challenges.pop(challenge_id, None)
            self._challenges[challenge.challenge_id] = challenge
        return {
            "challenge_id": challenge.challenge_id,
            "expires_at": challenge.expires_at.isoformat(),
            "academic_period": challenge.academic_period,
        }

    async def consume(
        self,
        challenge_id: str,
        owner_id: str,
        token: str,
    ) -> tuple[str, str]:
        now = datetime.now(UTC)
        normalized_owner = normalize_whatsapp_jid(owner_id)
        async with self._lock:
            self._purge(now)
            challenge = self._challenges.get(challenge_id)
            if challenge is None:
                raise GradeChallengeError("Challenge token nilai tidak ditemukan atau kedaluwarsa.")
            if challenge.owner_id != normalized_owner:
                raise PermissionError("Challenge token nilai bukan milik sender ini.")
            challenge.attempts += 1
            if not re.fullmatch(r"\d{4,10}", token.strip()):
                if challenge.attempts >= get_settings().CYBER_CAMPUS_GRADE_TOKEN_MAX_ATTEMPTS:
                    self._challenges.pop(challenge_id, None)
                raise GradeChallengeError("Format token nilai tidak valid.")
            self._challenges.pop(challenge_id, None)
            return token.strip(), challenge.academic_period

    async def cancel(self, challenge_id: str) -> None:
        async with self._lock:
            self._challenges.pop(challenge_id, None)

    def _purge(self, now: datetime) -> None:
        for challenge_id, challenge in tuple(self._challenges.items()):
            if challenge.expires_at <= now:
                self._challenges.pop(challenge_id, None)


GRADE_TOKEN_COORDINATOR = GradeTokenCoordinator()
