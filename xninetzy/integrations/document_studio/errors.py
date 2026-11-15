from __future__ import annotations


class DocumentStudioError(RuntimeError):
    pass


class MissingDependencyError(DocumentStudioError):
    pass


def require(module: str, extra: str = "documents"):
    try:
        return __import__(module, fromlist=["_"])
    except ImportError as exc:
        raise MissingDependencyError(
            f"{module} is not installed; install it with `uv pip install 'xninetzy-mcp[{extra}]'`."
        ) from exc
