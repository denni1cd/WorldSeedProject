import ast
import math
from typing import Any, Dict

# Allowed built-in functions
ALLOWED_FUNCTIONS = {
    "floor": math.floor,
}

# Allowed AST node types
ALLOWED_NODE_TYPES = {
    ast.Expression,
    ast.BinOp,
    ast.Name,
    ast.Constant,
    ast.Load,
    ast.Call,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.UAdd,
    ast.USub,
}


def _eval_node(node: ast.AST, context: Dict[str, Any]) -> float:
    """Recursively evaluate an AST node."""
    node_type = type(node)

    if node_type not in ALLOWED_NODE_TYPES:
        raise ValueError(f"Unsafe node type found: {node_type.__name__}")

    if isinstance(node, ast.Expression):
        return _eval_node(node.body, context)

    elif isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise ValueError(f"Only numeric constants are allowed, not {type(node.value).__name__}")
        return node.value

    elif isinstance(node, ast.Name):
        if node.id in context:
            return context[node.id]
        raise NameError(f"The name '{node.id}' is not defined in the provided context.")

    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left, context)
        right = _eval_node(node.right, context)
        op_map = {
            ast.Add: lambda a, b: a + b,
            ast.Sub: lambda a, b: a - b,
            ast.Mult: lambda a, b: a * b,
            ast.Div: lambda a, b: a / b,
            ast.FloorDiv: lambda a, b: a // b,
        }
        if type(node.op) in op_map:
            return op_map[type(node.op)](left, right)
        raise TypeError(f"Unsupported binary operator: {type(node.op).__name__}")

    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in ALLOWED_FUNCTIONS:
            func = ALLOWED_FUNCTIONS[node.func.id]
            args = [_eval_node(arg, context) for arg in node.args]
            return func(*args)
        func_name = node.func.id if isinstance(node.func, ast.Name) else "[complex expression]"
        raise ValueError(f"Unsupported function call: '{func_name}'")

    elif isinstance(node, ast.UAdd):
        return +_eval_node(node.operand, context)

    elif isinstance(node, ast.USub):
        return -_eval_node(node.operand, context)

    # This line should not be reachable given the initial check
    raise TypeError(f"Evaluation failed for node type: {node_type.__name__}")


def evaluate(expr: str, context: Dict[str, Any]) -> float:
    """
    Safely evaluates a mathematical expression string using a restricted AST evaluator.

    Args:
        expr: The mathematical expression to evaluate.
        context: A dictionary of variable names and their values.

    Returns:
        The result of the evaluation.

    Raises:
        ValueError: If the expression contains unsafe operations or is malformed.
        NameError: If the expression uses a variable not in the context.
        TypeError: If an operation is used on an unsupported type.
    """
    if not isinstance(expr, str):
        raise TypeError("Expression must be a string.")

    try:
        # Using mode='eval' ensures we get a single expression
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Invalid syntax in expression: '{expr}'") from e

    result = _eval_node(tree, context)
    if not isinstance(result, (int, float)):
        raise TypeError(f"Evaluation resulted in a non-numeric type: {type(result).__name__}")

    return float(result)
