from app.xninetzy.os.academic.mahasiswa_portal.runtime_analyzer import (
    classify_navigation,
    extract_php_targets,
)


def test_extract_php_targets_discards_javascript_body():
    value = "load('akademik-krs-2.php'); $.post('proses/_akademik-krs_dilihat.php')"
    assert extract_php_targets(value) == [
        "akademik-krs-2.php",
        "proses/_akademik-krs_dilihat.php",
    ]


def test_navigation_policy_blocks_process_targets_and_guards_krs():
    assert classify_navigation("/modul/mhs/akademik-krs.php", "KRS") == "krs_guarded"
    assert (
        classify_navigation("/modul/mhs/proses/_akademik-krs.php", "Simpan")
        == "blocked_write"
    )
    assert classify_navigation("/modul/mhs/akademik-jadwal.php", "Jadwal") == "read_only"
    assert classify_navigation("/logout.php", "Logout") == "blocked_write"
