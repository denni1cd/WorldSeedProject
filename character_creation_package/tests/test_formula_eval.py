import pytest
from character_creation.services.formula_eval import evaluate


def test_evaluate_simple_expression():
    """Tests a simple expression with context variables."""
    context = {"STA": 10, "INT": 5, "level": 1}
    expr = "10 + STA * 2"
    assert evaluate(expr, context) == 30


def test_evaluate_with_floor_function():
    """Tests the allowed 'floor' function."""
    context = {"level": 4.8}
    expr = "floor(level / 2)"
    assert evaluate(expr, context) == 2


def test_evaluate_complex_expression():
    """Tests a more complex, nested expression."""
    context = {"STA": 5, "INT": 3, "level": 4}
    expression = "20 + STA * 5 + floor(level / 2)"
    expected = 20 + (5 * 5) + (4 // 2)
    assert evaluate(expression, context) == expected


def test_evaluate_raises_on_undefined_variable():
    """Tests that a NameError is raised for variables not in the context."""
    context = {"STA": 5}
    expr = "STA + AGI"
    with pytest.raises(NameError, match="'AGI' is not defined"):
        evaluate(expr, context)


def test_evaluate_raises_on_unsafe_node_attribute():
    """Tests that accessing attributes is blocked."""
    context = {}
    expr = "''.__class__"
    with pytest.raises(ValueError, match="Unsafe node type found: Attribute"):
        evaluate(expr, context)


def test_evaluate_raises_on_unsafe_node_import():
    """Tests that imports are blocked."""
    context = {}
    expr = "__import__('os')"
    # This will fail at the parsing stage before our custom eval, which is fine.
    with pytest.raises(ValueError, match="Unsupported function call: '__import__'"):
        evaluate(expr, context)


def test_evaluate_raises_on_disallowed_function_call():
    """Tests that calling a function not in the allow-list is blocked."""
    context = {}
    expr = "open('secrets.txt')"
    with pytest.raises(ValueError, match="Unsupported function call: 'open'"):
        evaluate(expr, context)


def test_evaluate_handles_floats_and_integers():
    """Tests that the evaluator correctly handles numeric types."""
    context = {"a": 1.5, "b": 2}
    expr = "a * b"
    assert evaluate(expr, context) == 3.0
