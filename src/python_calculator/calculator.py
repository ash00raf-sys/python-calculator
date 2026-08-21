"""A deliberately small evaluator for basic arithmetic expressions.

Expressions are parsed with :mod:`ast`, then evaluated from an allow-list of
node types. This avoids executing arbitrary Python code via ``eval``.
"""

from __future__ import annotations

import ast
import operator
from numbers import Real
from typing import Callable, Dict, Union

Number = Union[int, float]

# Safety limits to prevent DoS via extremely large / deeply nested input.
MAX_EXPRESSION_LENGTH = 10_000
MAX_AST_DEPTH = 200
MAX_AST_NODES = 1_000


class CalculatorError(ValueError):
    """Raised when an expression cannot be evaluated safely."""

    def __str__(self) -> str:
        # Keep message clean even when chained from other exceptions
        return super().__str__() or "Invalid arithmetic expression."


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

# Human-readable names for operators we explicitly reject, to give better errors.
_UNSUPPORTED_BIN_OPS: Dict[type[ast.operator], str] = {
    ast.Pow: "** (exponentiation)",
    ast.Mod: "% (modulo)",
    ast.FloorDiv: "// (floor division)",
    ast.MatMult: "@ (matrix multiplication)",
    ast.BitAnd: "& (bitwise and)",
    ast.BitOr: "| (bitwise or)",
    ast.BitXor: "^ (bitwise xor)",
    ast.LShift: "<< (left shift)",
    ast.RShift: ">> (right shift)",
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

    stripped = expression.strip()
    if not stripped:
        raise CalculatorError("Expression cannot be empty.")

    if len(stripped) > MAX_EXPRESSION_LENGTH:
        raise CalculatorError(
            f"Expression too long ({len(stripped)} chars). "
            f"Maximum allowed is {MAX_EXPRESSION_LENGTH}."
        )

    try:
        # Strip leading/trailing whitespace before parsing.
        # ast.parse with mode='eval' treats leading spaces as indentation
        # and raises IndentationError otherwise (e.g. "  2 + 3").
        tree = ast.parse(stripped, mode="eval")
    except (SyntaxError, ValueError, IndentationError) as error:
        raise CalculatorError("Invalid arithmetic expression.") from error

    # Quick safety check: limit total number of AST nodes
    node_count = 0
    for _ in ast.walk(tree):
        node_count += 1
        if node_count > MAX_AST_NODES:
            raise CalculatorError(
                f"Expression too complex (>{MAX_AST_NODES} nodes)."
            )

    try:
        return _evaluate_node(tree.body, depth=0)
    except ZeroDivisionError as error:
        raise CalculatorError("Cannot divide by zero.") from error
    except RecursionError as error:
        raise CalculatorError("Expression is too deeply nested.") from error


def _evaluate_node(node: ast.AST, depth: int) -> Number:
    if depth > MAX_AST_DEPTH:
        raise CalculatorError("Expression is too deeply nested.")

    # Numeric literals: handle both new (Constant) and legacy (Num) AST nodes
    if isinstance(node, ast.Constant):
        # bool is an int subclass but should never be treated as a number here.
        if isinstance(node.value, bool):
            raise CalculatorError("Boolean values are not supported.")
        if isinstance(node.value, Real):
            return node.value
        if node.value is None:
            raise CalculatorError("Only numeric literals are supported.")
        raise CalculatorError(
            f"Unsupported literal {node.value!r}. Only numbers are allowed."
        )

    # Compatibility for Python <3.8 where numbers are ast.Num
    if isinstance(node, ast.Num):  # pragma: no cover - legacy path
        if isinstance(node.n, bool):
            raise CalculatorError("Boolean values are not supported.")
        if isinstance(node.n, Real):
            return node.n
        raise CalculatorError("Only numeric literals are supported.")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in _BINARY_OPERATORS:
            left = _evaluate_node(node.left, depth + 1)
            right = _evaluate_node(node.right, depth + 1)
            # operator.truediv will raise ZeroDivisionError for zero divisor
            return _BINARY_OPERATORS[op_type](left, right)

        # Give a specific message for known but unsupported operators
        if op_type in _UNSUPPORTED_BIN_OPS:
            raise CalculatorError(
                f"Operator {_UNSUPPORTED_BIN_OPS[op_type]} is not supported. "
                "Use +, -, *, and /."
            )

        raise CalculatorError(
            "Unsupported operator. Use +, -, *, and /."
        )

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in _UNARY_OPERATORS:
            operand = _evaluate_node(node.operand, depth + 1)
            return _UNARY_OPERATORS[op_type](operand)

        if isinstance(node.op, ast.Not):
            raise CalculatorError("Logical operators are not supported.")
        if isinstance(node.op, ast.Invert):
            raise CalculatorError("Bitwise operators are not supported.")

        raise CalculatorError("Unsupported unary operator. Use + and -.")

    # More helpful errors for common disallowed syntax
    if isinstance(node, ast.Call):
        raise CalculatorError("Function calls are not supported.")
    if isinstance(node, ast.Name):
        raise CalculatorError(f"Variables are not supported (found '{node.id}').")
    if isinstance(node, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
        raise CalculatorError("Collections are not supported. Use numbers only.")
    if isinstance(node, ast.Subscript):
        raise CalculatorError("Subscripts are not supported.")
    if isinstance(node, ast.Attribute):
        raise CalculatorError("Attribute access is not supported.")
    if isinstance(node, ast.Compare):
        raise CalculatorError("Comparisons are not supported.")
    if isinstance(node, ast.BoolOp):
        raise CalculatorError("Logical operators are not supported.")
    if isinstance(node, ast.IfExp):
        raise CalculatorError("Conditional expressions are not supported.")
    if isinstance(node, ast.Lambda):
        raise CalculatorError("Lambdas are not supported.")

    raise CalculatorError(
        "Unsupported syntax. Use numbers, parentheses, +, -, *, and /."
    )
