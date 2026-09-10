import pytest

from app.xninetzy.os.academic.mahasiswa_portal.reader import (
    AcademicPeriod,
    AcademicPortalReader,
    AcademicPortalReadError,
    GRADE_FETCH_SCRIPT,
    GradeTokenRejected,
    PreparedGradeRequest,
    parse_academic_profile_html,
    parse_academic_status_html,
    parse_current_krs_html,
    parse_grade_html,
    parse_schedule_html,
    select_academic_period,
    validate_grade_token_page,
)


SCHEDULE_HTML = """
<h3>Jadwal Kuliah Semester Genap 2025/2026</h3>
<table>
  <tr><th>Mata Ajar</th><th>Sks</th><th>Kelas</th><th>Jadwal</th><th>Ruang</th><th>Petugas</th></tr>
  <tr><td>Pembelajaran Mesin</td><td>3</td><td>A</td><td>Senin 08:00</td><td>R-101</td><td>Dosen Satu</td></tr>
  <tr><td>Data Analytics</td><td>3</td><td>B</td><td>Rabu 10:00</td><td>R-202</td><td>Dosen Dua</td></tr>
</table>
"""


GRADE_HTML = """
<table>
  <tr><th>No</th><th>Mata Kuliah</th><th>SKS</th><th>Nilai</th></tr>
  <tr><td>1</td><td>Pembelajaran Mesin</td><td>3</td><td>AB</td></tr>
</table>
"""


GRADE_HTML_WITH_TITLE = """
<table>
  <tr><td colspan="5">Kartu Hasil Studi</td></tr>
  <tr><th>No</th><th>Kode</th><th>Nama Mata Ajar</th><th>SKS</th><th>Nilai Huruf</th></tr>
  <tr><td>1</td><td>SI301</td><td>Pembelajaran Mesin</td><td>3</td><td>AB</td></tr>
</table>
"""


PROFILE_HTML = """
<table>
  <tr><td>Nama</td><td><input value="Mahasiswa Contoh"></td></tr>
  <tr><td>NIM</td><td>123456789</td></tr>
  <tr><td>Fakultas</td><td><select><option selected>Fakultas Teknologi Maju</option></select></td></tr>
  <tr><td>Program Studi</td><td><input value="Sistem Informasi"></td></tr>
  <tr><td>Alamat</td><td>Data privat lain tidak diekspos</td></tr>
</table>
"""


PROFILE_FORM_HTML = """
<div class="form-group"><label for="student_name">Nama Mahasiswa</label><input id="student_name" value="Mahasiswa Form"></div>
<div class="form-group"><label for="student_id">Nomor Induk Mahasiswa</label><input id="student_id" value="987654321"></div>
<div class="form-group"><label for="faculty">Fakultas / Sekolah</label><input id="faculty" value="Fakultas Baru"></div>
<div class="form-group"><label for="program">Program Studi / Prodi</label><input id="program" value="Sistem Informasi"></div>
"""


ACADEMIC_STATUS_MULTI_TABLE_HTML = """
<table><tr><th>Semester</th><th>Status</th><th>No SK</th><th>Tanggal SK</th><th>Keterangan</th></tr>
<tr><td>2024/2025 Ganjil</td><td>AKTIF</td><td>-</td><td>-</td><td>Registrasi</td></tr></table>
<table><tr><th>Periode</th><th>Status Akademik</th><th>Nomor SK</th><th>Tgl SK</th><th>Catatan</th></tr>
<tr><td>2024/2025 Genap</td><td>AKTIF</td><td>SK-2</td><td>2025-01-01</td><td>Registrasi ulang</td></tr></table>
"""


ACADEMIC_STATUS_HTML = """
<table>
  <tr><th>Semester</th><th>Status</th><th>No. SK.</th><th>Tgl SK.</th><th>Keterangan</th></tr>
  <tr><td>2025/2026 Genap</td><td>AKTIF</td><td>-</td><td>-</td><td>Registrasi</td></tr>
</table>
"""


CURRENT_KRS_HTML = """
<table>
  <tr><th>No..</th><th>KODE MK</th><th>NAMA MATA KULIAH</th><th>SKS MATA KULIAH</th><th>KELAS</th><th>STATUS</th></tr>
  <tr><td>1</td><td>SI301</td><td>Pembelajaran Mesin</td><td>3 SKS</td><td>A</td><td>Terambil</td></tr>
  <tr><td>2</td><td>SI302</td><td>Data Analytics</td><td>2</td><td>B</td><td>Terambil</td></tr>
  <tr><td colspan="6">Total data</td></tr>
</table>
"""


def test_parse_academic_profile_exposes_only_minimal_allowlist():
    result = parse_academic_profile_html(PROFILE_HTML)

    assert result.name == "Mahasiswa Contoh"
    assert result.student_id == "123456789"
    assert result.faculty == "Fakultas Teknologi Maju"
    assert result.study_program == "Sistem Informasi"
    assert not hasattr(result, "address")


def test_parse_academic_profile_requires_identity_fields():
    with pytest.raises(AcademicPortalReadError):
        parse_academic_profile_html("<table><tr><td>Fakultas</td><td>FTM</td></tr></table>")


def test_parse_academic_status_matches_live_headers():
    entries = parse_academic_status_html(ACADEMIC_STATUS_HTML)

    assert len(entries) == 1
    assert entries[0].semester == "2025/2026 Genap"
    assert entries[0].status == "AKTIF"


def test_parse_current_krs_sums_credits_and_ignores_summary_rows():
    result = parse_current_krs_html(CURRENT_KRS_HTML)

    assert len(result.entries) == 2
    assert result.entries[0].course_code == "SI301"
    assert result.total_credits == 5


def test_academic_tables_fail_closed_when_headers_change():
    with pytest.raises(AcademicPortalReadError):
        parse_academic_status_html("<table><tr><th>Status Baru</th></tr></table>")
    with pytest.raises(AcademicPortalReadError):
        parse_current_krs_html("<table><tr><th>KRS Baru</th></tr></table>")


def test_parse_schedule_matches_live_cyber_campus_headers():
    result = parse_schedule_html(SCHEDULE_HTML)

    assert result.period == "Jadwal Kuliah Semester Genap 2025/2026"
    assert len(result.entries) == 2
    assert result.entries[0].course == "Pembelajaran Mesin"
    assert result.entries[1].room == "R-202"


def test_parse_schedule_fails_closed_when_structure_changes():
    with pytest.raises(AcademicPortalReadError):
        parse_schedule_html("<table><tr><th>Unknown</th></tr></table>")


def test_parse_grade_returns_header_bound_values():
    result = parse_grade_html(GRADE_HTML, "2025/2026 Genap")

    assert result.period == "2025/2026 Genap"
    assert dict(result.entries[0].values)["Nilai"] == "AB"


def test_parse_grade_finds_header_after_report_title():
    result = parse_grade_html(GRADE_HTML_WITH_TITLE, "2025/2026 Genap")

    assert dict(result.entries[0].values)["Nama Mata Ajar"] == "Pembelajaran Mesin"
    assert dict(result.entries[0].values)["Nilai Huruf"] == "AB"


def test_parse_grade_rejects_non_grade_response():
    with pytest.raises(GradeTokenRejected, match="Token tidak valid"):
        parse_grade_html("<div>Token tidak valid</div>", "latest")


def test_parse_grade_surfaces_redacted_portal_alert():
    with pytest.raises(GradeTokenRejected, match=r"Token \[angka\] salah"):
        parse_grade_html("<script>alert('Token 12345 salah')</script>", "latest")


def test_validate_grade_token_page_requires_portal_instruction():
    validate_grade_token_page(
        '<label>Token</label><input name="token">'
        '<p>Token dikirim ke akun Telegram anda</p>'
    )
    with pytest.raises(AcademicPortalReadError):
        validate_grade_token_page('<input name="token">')


def test_select_academic_period_supports_latest_code_and_label():
    options = [
        {"value": "0", "label": "Pilih periode"},
        {"value": "291", "label": "2025/2026 - Genap - Genap"},
        {"value": "287", "label": "2025/2026 - Ganjil - Ganjil"},
    ]

    assert select_academic_period(options, "latest").value == "291"
    assert select_academic_period(options, "287").label.endswith("Ganjil")
    assert select_academic_period(options, "Genap - Genap").value == "291"
    with pytest.raises(AcademicPortalReadError):
        select_academic_period(options, "2020")


def test_select_academic_period_maps_student_semester_after_entry_year():
    options = [
        {"value": "291", "label": "2025/2026 - Genap - Genap"},
        {"value": "287", "label": "2025/2026 - Ganjil - Ganjil"},
        {"value": "283", "label": "2024/2025 - Genap - Genap"},
        {"value": "279", "label": "2024/2025 - Ganjil - Ganjil"},
    ]

    assert select_academic_period(options, "semester 1", 2024).value == "279"
    assert select_academic_period(options, "semester 2", 2024).value == "283"
    assert select_academic_period(options, "semester 3", 2024).value == "287"
    assert select_academic_period(options, "semester 4", 2024).value == "291"


@pytest.mark.asyncio
async def test_read_grades_reuses_prepared_page_and_posts_selected_period():
    calls = []

    class Context:
        async def close(self):
            return None

    class Closeable:
        async def close(self):
            return None

    class Stoppable:
        async def stop(self):
            return None

    class Page:
        url = "https://mahasiswa.unair.ac.id/modul/mhs/akademik-khs.php"

        class TokenInput:
            async def fill(self, value):
                calls.append(("fill", value))

        class PeriodInput:
            async def evaluate(self, script, value):
                calls.append((script, value))

        def locator(self, selector):
            if selector == "input[name=token]":
                return self.TokenInput()
            assert selector == "select[name=thn_akademik]"
            return self.PeriodInput()

        async def evaluate(self, script, payload):
            calls.append((script, payload))
            return GRADE_HTML

    reader = AcademicPortalReader()
    reader._prepared_grade_requests["grade-1"] = PreparedGradeRequest(
        challenge_id="grade-1",
        period=AcademicPeriod("291", "2025/2026 - Genap - Genap"),
        playwright=Stoppable(),
        browser=Closeable(),
        context=Context(),
        page=Page(),
    )

    result = await reader.read_grades("12345", "semester 1", "grade-1")

    assert result.period == "2025/2026 - Genap - Genap"
    assert calls[0] == ("fill", "12345")
    assert calls[1][1] == "291"
    assert calls[2][1] == {
        "period": "291",
        "token": "12345",
    }
    assert "fetch(" in calls[2][0]
    assert "$(" not in GRADE_FETCH_SCRIPT
    assert reader._prepared_grade_requests == {}

def test_parse_academic_profile_supports_label_for_fields():
    result = parse_academic_profile_html(PROFILE_FORM_HTML)

    assert result.name == "Mahasiswa Form"
    assert result.student_id == "987654321"
    assert result.faculty == "Fakultas Baru"
    assert result.study_program == "Sistem Informasi"


def test_parse_academic_status_aggregates_repeated_tables():
    entries = parse_academic_status_html(ACADEMIC_STATUS_MULTI_TABLE_HTML)

    assert [entry.semester for entry in entries] == [
        "2024/2025 Ganjil",
        "2024/2025 Genap",
    ]
