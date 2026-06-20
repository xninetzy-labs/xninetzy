from __future__ import annotations

import ast
import operator
import re
import statistics
from typing import Any

from langchain_core.tools import tool

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(expression: str) -> float:
    tree = ast.parse(expression, mode="eval")
    return float(_eval_node(tree.body))


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Ekspresi tidak aman atau tidak didukung")


@tool
def calculate(expression: str) -> str:
    """Hitung ekspresi matematika secara aman menggunakan AST evaluator.

    Gunakan untuk arithmetic, persentase, dan operasi numerik apapun.
    Contoh: "15 / 40 * 100", "2 ** 10", "(100 - 25) / 3"

    Args:
        expression: Ekspresi matematika valid (hanya angka dan operator +−×÷^%())
    """
    try:
        clean = expression.replace("%", "/100").replace("×", "*").replace("÷", "/").replace("^", "**")
        result = _safe_eval(clean)
        return f"{result:g}"
    except Exception as e:
        return f"Error menghitung '{expression}': {e}"


@tool
def calculate_percentage(part: float, whole: float) -> str:
    """Hitung persentase: berapa persen `part` dari `whole`.

    Args:
        part: Bagian (pembilang)
        whole: Keseluruhan (penyebut)
    """
    if whole == 0:
        return "Error: pembagi tidak boleh 0"
    result = part / whole * 100
    return f"{result:g}%\n\nCara hitung: `{part:g} / {whole:g} × 100 = {result:g}%`"
