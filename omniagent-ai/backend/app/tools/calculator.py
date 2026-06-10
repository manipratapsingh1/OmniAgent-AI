import ast
import operator as op
from typing import Dict, Any

_OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
    ast.Pow: op.pow, ast.Mod: op.mod, ast.USub: op.neg, ast.FloorDiv: op.floordiv,
}


def _eval(node):
    if isinstance(node, ast.Num):
        return node.n
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