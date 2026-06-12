"""Calculator skill: exact arithmetic the LLM can trust.

Their sandbox-exec idea, reduced to what is actually safe: a whitelisted
AST evaluator - numbers, arithmetic operators and a few math functions.
No names, no calls beyond the whitelist, no attribute access, no state.
"""
import ast
import math
import operator
from . import skill

OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}
FUNCTIONS = {"sqrt": math.sqrt, "abs": abs, "round": round,
             "sin": math.sin, "cos": math.cos, "tan": math.tan,
             "log": math.log, "log10": math.log10, "exp": math.exp}
CONSTANTS = {"pi": math.pi, "e": math.e}
MAX_POW = 10_000


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name) and node.id in CONSTANTS:
        return CONSTANTS[node.id]
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 64:
            raise ValueError("exponent too large")
        result = OPERATORS[type(node.op)](left, right)
        if isinstance(result, (int, float)) and abs(result) > 10 ** MAX_POW:
            raise ValueError("result too large")
        return result
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
            and node.func.id in FUNCTIONS and not node.keywords:
        return FUNCTIONS[node.func.id](*[_eval(a) for a in node.args])
    raise ValueError(f"unsupported expression: {ast.dump(node)[:40]}")


@skill("calculate",
       "Evaluate an arithmetic expression exactly (e.g. '12.5 * 6 / sqrt(2)'). "
       "Use for any math you cannot do reliably in your head.",
       {"type": "object", "properties": {"expression": {"type": "string"}},
        "required": ["expression"]})
def calculate(ctx, expression):
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        value = _eval(tree)
    except (ValueError, SyntaxError, ZeroDivisionError, OverflowError) as e:
        return f"error: {e}"
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return f"{expression.strip()} = {value}"
