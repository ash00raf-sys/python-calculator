"""A deliberately small evaluator for basic arithmetic expressions.

Expressions are parsed with :mod:`ast`, then evaluated from an allow-list of
node types. This avoids executing arbitrary Python code via ``eval``.
"""

from __future__ import annotations

import ast
import operator
from numbers import Real
from typing import Any, Callable, Dict, Union

Number = Union[int, float]


class CalculatorError(ValueError):
    """Raised when an expression cannot be evaluated safely."""


_BINARY_OPERATORS: Dict[type[ast.operator], Callable[[Number, Number], Number]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}

_UNARY_OPERATORS: Dict[type[ast.unaryop], Callable[[Number], Number]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def evaluate(expression: str) -> Number:
    """Evaluate a basic arithmetic *expression* safely.

    Supported syntax is numeric literals, parentheses, and ``+``, ``-``,
    ``*``, and ``/`` operators. The result is an ``int`` where possible and a
    ``float`` for division or expressions containing decimal literals.

    Args:
        expression: The arithmetic expression to evaluate.

    Raises:
        CalculatorError: If the input is empty, malformed, or uses unsupported
            Python syntax. Division by zero is also reported as this error.
    """
    if not isinstance(expression, str):
        raise CalculatorError("Expression must be a string.")
    if not expression.strip():
        raise CalculatorError("Expression cannot be empty.")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise CalculatorError("Invalid arithmetic expression.") from error

    try:
        return _evaluate_node(tree.body)
    except ZeroDivisionError as error:
        raise CalculatorError("Cannot divide by zero.") from error


def _evaluate_node(node: ast.AST) -> Number:
    if isinstance(node, ast.Constant):
        # bool is an int subclass but should never be treated as a number here.
        if isinstance(node.value, Real) and not isinstance(node.value, bool):
            return node.value
        raise CalculatorError("Only numeric literals are supported.")

    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        return _BINARY_OPERATORS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate_node(node.operand))

    raise CalculatorError("Unsupported syntax. Use numbers, parentheses, +, -, *, and /.")
