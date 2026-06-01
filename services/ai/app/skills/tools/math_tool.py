from __future__ import annotations

import ast
import operator
import statistics
from typing import Any

OPS = {
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


class MathTool:
    def safe_eval(self, expression: str) -> float:
        tree = ast.parse(expression, mode="eval")
        return float(self._eval_node(tree.body))

    def percentage(self, part: float, whole: float) -> dict[str, Any]:
        if whole == 0:
            raise ValueError("Pembagi tidak boleh 0")
        result = part / whole * 100
        return {"result": result, "steps": f"{part:g} / {whole:g} × 100 = {result:g}%"}

    def summary_stats(self, values: list[float]) -> dict[str, Any]:
        if not values:
            raise ValueError("Data kosong")
        return {
            "average": statistics.fmean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "count": len(values),
        }

    def _eval_node(self, node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            return OPS[type(node.op)](self._eval_node(node.left), self._eval_node(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](self._eval_node(node.operand))
        raise ValueError("Ekspresi matematika tidak aman atau tidak didukung")
