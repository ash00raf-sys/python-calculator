import pytest

from python_calculator import CalculatorError, evaluate


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("2 + 3", 5),
        ("10 - 4 * 2", 2),
        ("(10 - 4) * 2", 12),
        ("9 / 2", 4.5),
        ("-5 + +2", -3),
        ("3.5 * 2", 7.0),
    ],
)
def test_evaluate_basic_arithmetic(expression, expected):
    assert evaluate(expression) == expected


@pytest.mark.parametrize(
    "expression",
    ["", "   ", "2 ** 3", "5 % 2", "abs(2)", "variable + 1", "True + 1", "[1, 2]"],
)
def test_evaluate_rejects_unsupported_syntax(expression):
    with pytest.raises(CalculatorError):
        evaluate(expression)


def test_evaluate_reports_division_by_zero():
    with pytest.raises(CalculatorError, match="divide by zero"):
        evaluate("10 / 0")


def test_evaluate_rejects_non_string_input():
    with pytest.raises(CalculatorError, match="must be a string"):
        evaluate(42)  # type: ignore[arg-type]
