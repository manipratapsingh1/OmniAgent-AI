import ast
import math
import operator as op
from typing import Dict, Any

_OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
    ast.Pow: op.pow, ast.Mod: op.mod, ast.USub: op.neg, ast.FloorDiv: op.floordiv,
}

_FUNCS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "log": math.log,
    "ln": math.log,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "pow": math.pow,
}

_CONSTS = {
    "pi": math.pi,
    "e": math.e,
}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in _CONSTS:
            return _CONSTS[node.id]
        raise ValueError(f"Unknown variable: {node.id}")
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in _FUNCS:
            args = [_eval(arg) for arg in node.args]
            return _FUNCS[node.func.id](*args)
        raise ValueError("Unsupported function call")
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Unsupported expression")


async def calculator(args: Dict[str, Any]) -> str:
    expr = str(args.get("expression", "")).strip()
    if not expr:
        return "No expression provided."
    try:
        tree = ast.parse(expr, mode="eval")
        result = _eval(tree.body)
        return f"{expr} = {result}"
    except Exception as e:
        return f"Error: {e}"