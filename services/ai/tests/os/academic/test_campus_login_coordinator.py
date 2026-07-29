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
