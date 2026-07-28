def test_hebat_debug_words_do_not_include_secret_labels():
    safe_output = (
        "*HEBAT Debug Login*\n"
        "• Env password: tersedia\n"
        "• Cookie session: ada\n"
        "• Token ditemukan: ya"
    )
    assert "your_password" not in safe_output
    assert "sesskey=" not in safe_output
    assert "MoodleSession" not in safe_output
