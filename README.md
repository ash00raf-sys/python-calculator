# python-calculator

A polished web calculator and small Python library for safely evaluating
**basic arithmetic expressions**. It accepts numbers, parentheses, and the
`+`, `-`, `*`, and `/` operators.

Unlike Python's `eval`, this package parses expressions and evaluates only an
explicit allow-list of arithmetic syntax. It will not execute function calls,
variable references, imports, or other Python code. The responsive Flask web
app adds live results, keyboard input, and private browser-local history.

## Install

For local development:

```bash
python -m pip install -e '.[dev]'
```

## Usage

```python
from python_calculator import CalculatorError, evaluate

print(evaluate("2 + 3 * 4"))      # 14
print(evaluate("(10 - 4) / 2"))   # 3.0
print(evaluate("-5 + 2"))         # -3

try:
    evaluate("10 / 0")
except CalculatorError as error:
    print(error)  # Cannot divide by zero.
```

## Supported expressions

| Supported | Not supported |
| --- | --- |
| Integer and decimal numeric literals | Variables and function calls |
| Parentheses | Exponentiation (`**`) and modulo (`%`) |
| Addition (`+`) and subtraction (`-`) | Lists, strings, booleans, and arbitrary Python code |
| Multiplication (`*`) and division (`/`) | |
| Unary plus and minus | |

## Web app

Start the calculator locally:

```bash
python -m pip install -e '.[dev]'
flask --app python_calculator.web run --debug
```

Then open <http://127.0.0.1:5000>. The JSON API accepts an expression at
`POST /api/calculate`:

```bash
curl -X POST http://127.0.0.1:5000/api/calculate \
  -H 'Content-Type: application/json' \
  -d '{"expression":"(8 + 4) / 3"}'
```

The included [`render.yaml`](render.yaml) Blueprint configures a free Render
web service with Gunicorn and a `/health` health check.

## Development

Run the tests:

```bash
python -m pytest
```

The GitHub Actions workflow runs the test suite on Python 3.9, 3.11, and 3.13.
