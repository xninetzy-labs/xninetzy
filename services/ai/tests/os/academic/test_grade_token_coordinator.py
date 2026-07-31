from datetime import UTC, datetime, timedelta

import pytest

from app.xninetzy.os.academic.mahasiswa_portal.grade_token import (
    GradeChallengeError,
    GradeTokenCoordinator,
)


@pytest.mark.asyncio
async def test_grade_token_is_owner_bound_and_single_use():
    coordinator = GradeTokenCoordinator()
    challenge = await coordinator.start("628123:7@s.whatsapp.net")

    token, period = await coordinator.consume(
        challenge["challenge_id"],
        "628123@s.whatsapp.net",
        "12345",
    )

    assert token == "12345"
    assert period == "latest"
    with pytest.raises(GradeChallengeError):
        await coordinator.consume(
            challenge["challenge_id"],
            "628123@s.whatsapp.net",
            "12345",
        )


@pytest.mark.asyncio
async def test_grade_token_rejects_cross_owner_input():
    coordinator = GradeTokenCoordinator()
    challenge = await coordinator.start("628123@s.whatsapp.net")

    with pytest.raises(PermissionError):
        await coordinator.consume(
            challenge["challenge_id"],
            "628999@s.whatsapp.net",
            "12345",
        )


@pytest.mark.asyncio
async def test_grade_token_expiry_fails_closed():
    coordinator = GradeTokenCoordinator()
    challenge = await coordinator.start("628123@s.whatsapp.net")
    coordinator._challenges[challenge["challenge_id"]].expires_at = (
        datetime.now(UTC) - timedelta(seconds=1)
    )

    with pytest.raises(GradeChallengeError):
        await coordinator.consume(
            challenge["challenge_id"],
            "628123@s.whatsapp.net",
            "12345",
        )


@pytest.mark.asyncio
async def test_grade_token_can_be_cancelled():
    coordinator = GradeTokenCoordinator()
    challenge = await coordinator.start("628123@s.whatsapp.net")

    await coordinator.cancel(challenge["challenge_id"])

    with pytest.raises(GradeChallengeError):
        await coordinator.consume(
            challenge["challenge_id"],
            "628123@s.whatsapp.net",
            "12345",
        )


@pytest.mark.asyncio
async def test_grade_token_consume_owner_token_resolves_single_active_challenge():
    coordinator = GradeTokenCoordinator()
    challenge = await coordinator.start("628123@s.whatsapp.net")

    challenge_id, token, period = await coordinator.consume_owner_token(
        "628123@s.whatsapp.net", "12345"
    )

    assert challenge_id == challenge["challenge_id"]
    assert token == "12345"
    assert period == "latest"
    with pytest.raises(GradeChallengeError):
        await coordinator.consume_owner_token("628123@s.whatsapp.net", "12345")


@pytest.mark.asyncio
async def test_grade_token_consume_owner_token_rejects_cross_owner():
    coordinator = GradeTokenCoordinator()
    await coordinator.start("628123@s.whatsapp.net")

    with pytest.raises(GradeChallengeError):
        await coordinator.consume_owner_token("628999@s.whatsapp.net", "12345")


@pytest.mark.asyncio
async def test_grade_token_consume_owner_token_fails_without_challenge():
    coordinator = GradeTokenCoordinator()

    with pytest.raises(GradeChallengeError):
        await coordinator.consume_owner_token("628123@s.whatsapp.net", "12345")
