from __future__ import annotations

from app.xninetzy.tools.internal.calculation import calculate, calculate_percentage


def test_calculate_arithmetic():
    assert calculate.invoke({"expression": "2 + 3 * 4"}) == "14"


def test_calculate_parentheses_and_division():
    assert calculate.invoke({"expression": "(100 - 25) / 3"}) == "25"


def test_calculate_percent_operator():
    assert calculate.invoke({"expression": "50%"}) == "0.5"


def test_calculate_percentage_expression():
    assert calculate.invoke({"expression": "15 / 40 * 100"}) == "37.5"


def test_calculate_unicode_operators():
    assert calculate.invoke({"expression": "2 × 3"}) == "6"
    assert calculate.invoke({"expression": "2 ÷ 4"}) == "0.5"
    assert calculate.invoke({"expression": "2 ^ 3"}) == "8"


def test_calculate_power():
    assert calculate.invoke({"expression": "2 ** 10"}) == "1024"


def test_calculate_invalid_expression_returns_error():
    result = calculate.invoke({"expression": "abc"})
    assert result.startswith("Error menghitung")


def test_calculate_empty_input_returns_error():
    result = calculate.invoke({"expression": ""})
    assert result.startswith("Error menghitung")


def test_calculate_incomplete_expression_returns_error():
    result = calculate.invoke({"expression": "1 +"})
    assert result.startswith("Error menghitung")


def test_calculate_division_by_zero_returns_error():
    result = calculate.invoke({"expression": "1 / 0"})
    assert result.startswith("Error menghitung")


def test_calculate_unsafe_expression_rejected():
    result = calculate.invoke({"expression": "__import__('os')"})
    assert result.startswith("Error menghitung")


def test_calculate_unsupported_operator_rejected():
    result = calculate.invoke({"expression": "1 == 1"})
    assert result.startswith("Error menghitung")


def test_calculate_percentage_basic():
    result = calculate_percentage.invoke({"part": 15, "whole": 40})
    assert "37.5%" in result
    assert "15 / 40" in result


def test_calculate_percentage_round_number():
    result = calculate_percentage.invoke({"part": 50, "whole": 200})
    assert "25%" in result


def test_calculate_percentage_whole_zero_returns_error():
    result = calculate_percentage.invoke({"part": 10, "whole": 0})
    assert result == "Error: pembagi tidak boleh 0"


def test_calculate_percentage_part_zero():
    result = calculate_percentage.invoke({"part": 0, "whole": 100})
    assert result.startswith("0%")
