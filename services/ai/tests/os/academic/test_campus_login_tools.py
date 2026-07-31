import pytest
from types import SimpleNamespace

from app.xninetzy.os.academic.mahasiswa_portal import tools as portal_tools
from app.xninetzy.os.academic.mahasiswa_portal.reader import (
    AcademicProfile,
    AcademicStatusEntry,
    CurrentKrsEntry,
    CurrentKrsResult,
    GradeEntry,
    GradeResult,
)


def test_owner_id_normalizes_whatsapp_device_suffix():
    assert (
        portal_tools._owner_id("628123:7@s.whatsapp.net", "unused")
        == "628123@s.whatsapp.net"
    )


@pytest.mark.asyncio
async def test_cyber_login_denies_non_admin_before_browser_start(monkeypatch):
    started = False

    async def fake_start(owner_id):
        nonlocal started
        started = True
        return {}

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda sender_id, sender_name: False)
    monkeypatch.setattr(portal_tools.LOGIN_COORDINATOR, "start", fake_start)

    result = await portal_tools.portal_login_start.ainvoke(
        {"chat_id": "chat", "sender_id": "stranger@s.whatsapp.net"}
    )

    assert result == "Login Cyber Campus hanya dapat dimulai oleh admin."
    assert started is False


@pytest.mark.asyncio
async def test_captcha_submit_denies_non_admin_before_challenge_access(monkeypatch):
    submitted = False

    async def fake_submit(challenge_id, owner_id, answer):
        nonlocal submitted
        submitted = True
        return {}

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda sender_id, sender_name: False)
    monkeypatch.setattr(portal_tools.LOGIN_COORDINATOR, "submit", fake_submit)

    result = await portal_tools.portal_login_submit_captcha.ainvoke(
        {
            "challenge_id": "challenge",
            "captcha_answer": "ABC9",
            "chat_id": "chat",
            "sender_id": "stranger@s.whatsapp.net",
        }
    )

    assert result == "Jawaban CAPTCHA hanya dapat dikirim oleh admin."
    assert submitted is False


@pytest.mark.asyncio
async def test_grade_submit_maps_allowed_owner_alias_to_admin_jid(monkeypatch):
    consumed_owner = ""

    async def fake_consume(challenge_id, owner_id, token):
        nonlocal consumed_owner
        consumed_owner = owner_id
        raise RuntimeError("stop after identity check")

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda sender_id, sender_name: True)
    monkeypatch.setattr(portal_tools, "_notification_jid", lambda: "628123@s.whatsapp.net")
    monkeypatch.setattr(portal_tools.GRADE_TOKEN_COORDINATOR, "consume", fake_consume)

    await portal_tools.submit_grade_token(
        "challenge",
        "12345",
        "145300000000000@lid",
    )

    assert consumed_owner == "628123@s.whatsapp.net"


@pytest.mark.asyncio
async def test_grade_submit_persists_snapshot_after_success(monkeypatch):
    saved = []

    async def fake_consume(challenge_id, owner_id, token):
        return token, "semester 1"

    async def fake_read_grades(token, academic_period, challenge_id):
        return GradeResult(
            period="2024/2025 - Ganjil",
            entries=(
                GradeEntry(
                    values=(
                        ("Kode MK", "SI101"),
                        ("Mata Kuliah", "Dasar Sistem Informasi"),
                        ("Nilai", "AB"),
                    )
                ),
            ),
        )

    def fake_save(result):
        saved.append(result)
        return SimpleNamespace(snapshot_id=7, changes=(), created=True)

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda sender_id, sender_name: True)
    monkeypatch.setattr(portal_tools, "_notification_jid", lambda: "628123@s.whatsapp.net")
    monkeypatch.setattr(portal_tools.GRADE_TOKEN_COORDINATOR, "consume", fake_consume)
    monkeypatch.setattr(portal_tools.ACADEMIC_PORTAL_READER, "read_grades", fake_read_grades)
    monkeypatch.setattr(portal_tools.GRADE_SNAPSHOT_REPOSITORY, "save", fake_save)

    result = await portal_tools.submit_grade_token(
        "challenge",
        "12345",
        "628123@s.whatsapp.net",
    )

    assert len(saved) == 1
    assert "Snapshot lokal: #7" in result


@pytest.mark.asyncio
async def test_shared_academic_read_tools_format_typed_results(monkeypatch):
    async def fake_profile():
        return AcademicProfile(
            name="Mahasiswa Contoh",
            student_id="123456789",
            faculty="Fakultas Teknologi Maju",
            study_program="Sistem Informasi",
        )

    async def fake_status():
        return (
            AcademicStatusEntry(
                semester="2025/2026 Genap",
                status="AKTIF",
                decree_number="-",
                decree_date="-",
                description="Registrasi",
            ),
        )

    async def fake_krs():
        return CurrentKrsResult(
            entries=(
                CurrentKrsEntry(
                    course_code="SI301",
                    course_name="Pembelajaran Mesin",
                    credits=3,
                    class_code="A",
                    status="Terambil",
                ),
            ),
            total_credits=3,
        )

    monkeypatch.setattr(portal_tools.ACADEMIC_PORTAL_READER, "read_profile", fake_profile)
    monkeypatch.setattr(
        portal_tools.ACADEMIC_PORTAL_READER,
        "read_academic_status",
        fake_status,
    )
    monkeypatch.setattr(
        portal_tools.ACADEMIC_PORTAL_READER,
        "read_current_krs",
        fake_krs,
    )

    profile = await portal_tools.portal_profile.ainvoke({})
    status = await portal_tools.portal_academic_status.ainvoke({})
    current_krs = await portal_tools.portal_current_krs.ainvoke({})

    assert "Program studi: Sistem Informasi" in profile
    assert "2025/2026 Genap: AKTIF — Registrasi" in status
    assert "Total SKS: 3" in current_krs


@pytest.mark.asyncio
async def test_grade_token_submit_mcp_denies_non_admin(monkeypatch):
    consumed = False

    async def fake_consume(challenge_id, owner_id, token):
        nonlocal consumed
        consumed = True
        return token, "semester 1"

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda sender_id, sender_name: False)
    monkeypatch.setattr(portal_tools.GRADE_TOKEN_COORDINATOR, "consume", fake_consume)

    result = await portal_tools.portal_grade_token_submit.ainvoke(
        {
            "challenge_id": "challenge",
            "token": "12345",
            "sender_id": "stranger@s.whatsapp.net",
        }
    )

    assert result == "Token nilai hanya dapat dikirim oleh WhatsApp admin."
    assert consumed is False


@pytest.mark.asyncio
async def test_grade_token_submit_mcp_owner_persists_snapshot(monkeypatch):
    saved = []

    async def fake_consume(challenge_id, owner_id, token):
        return token, "semester 1"

    async def fake_read_grades(token, academic_period, challenge_id):
        return GradeResult(
            period="2024/2025 - Ganjil",
            entries=(
                GradeEntry(
                    values=(
                        ("Kode MK", "SI101"),
                        ("Mata Kuliah", "Dasar Sistem Informasi"),
                        ("Nilai", "AB"),
                    )
                ),
            ),
        )

    def fake_save(result):
        saved.append(result)
        return SimpleNamespace(snapshot_id=7, changes=(), created=True)

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda sender_id, sender_name: True)
    monkeypatch.setattr(portal_tools, "_notification_jid", lambda: "628123@s.whatsapp.net")
    monkeypatch.setattr(portal_tools.GRADE_TOKEN_COORDINATOR, "consume", fake_consume)
    monkeypatch.setattr(portal_tools.ACADEMIC_PORTAL_READER, "read_grades", fake_read_grades)
    monkeypatch.setattr(portal_tools.GRADE_SNAPSHOT_REPOSITORY, "save", fake_save)

    result = await portal_tools.portal_grade_token_submit.ainvoke(
        {
            "challenge_id": "challenge",
            "token": "12345",
            "sender_id": "628123@s.whatsapp.net",
        }
    )

    assert len(saved) == 1
    assert "Snapshot lokal: #7" in result


@pytest.mark.asyncio
async def test_grade_token_submit_token_only_resolves_owner(monkeypatch):
    consume_calls = []
    read_challenge_ids = []

    async def fake_consume_owner_token(owner_id, token):
        consume_calls.append((owner_id, token))
        return "challenge-resolved", token, "2024/2025 - Ganjil"

    async def fake_read_grades(token, academic_period, challenge_id):
        read_challenge_ids.append(challenge_id)
        return GradeResult(
            period="2024/2025 - Ganjil",
            entries=(
                GradeEntry(
                    values=(
                        ("Kode MK", "SI101"),
                        ("Mata Kuliah", "Dasar SI"),
                        ("Nilai", "A"),
                    )
                ),
            ),
        )

    def fake_save(result):
        return SimpleNamespace(snapshot_id=7, changes=(), created=True)

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda sender_id, sender_name: True)
    monkeypatch.setattr(portal_tools, "_notification_jid", lambda: "628123@s.whatsapp.net")
    monkeypatch.setattr(
        portal_tools.GRADE_TOKEN_COORDINATOR,
        "consume_owner_token",
        fake_consume_owner_token,
    )
    monkeypatch.setattr(portal_tools.ACADEMIC_PORTAL_READER, "read_grades", fake_read_grades)
    monkeypatch.setattr(portal_tools.GRADE_SNAPSHOT_REPOSITORY, "save", fake_save)

    result = await portal_tools.submit_grade_token(
        "", "12345", "628123@s.whatsapp.net"
    )

    assert read_challenge_ids == ["challenge-resolved"]
    assert "Snapshot lokal: #7" in result
    assert consume_calls == [("628123@s.whatsapp.net", "12345")]


@pytest.mark.asyncio
async def test_grade_token_submit_token_only_denies_non_admin(monkeypatch):
    async def unexpected_consume_owner_token(owner_id, token):
        raise AssertionError("consume_owner_token must not be called for non-admin")

    monkeypatch.setattr(portal_tools, "is_owner_admin", lambda sender_id, sender_name: False)
    monkeypatch.setattr(
        portal_tools.GRADE_TOKEN_COORDINATOR,
        "consume_owner_token",
        unexpected_consume_owner_token,
    )

    result = await portal_tools.submit_grade_token(
        "", "12345", "stranger@s.whatsapp.net"
    )

    assert result == "Token nilai hanya dapat dikirim oleh WhatsApp admin."
