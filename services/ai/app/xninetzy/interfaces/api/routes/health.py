from fastapi import APIRouter

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


def _faiss_backend() -> str:
    """Non-secret FAISS backend label. CPU-only is expected."""
    try:
        import faiss

        return "gpu" if hasattr(faiss, "StandardGpuResources") else "cpu"
    except Exception:  # pragma: no cover - faiss optional
        return "unavailable"


def _ai_runtime() -> dict[str, object]:
    """Non-secret snapshot of the AI runtime for /health.

    Best-effort — never raises, never leaks credentials or a full env dump.
    """
    s = get_settings()
    info: dict[str, object] = {
        "device": s.XNINETZY_DEVICE,
        "embedding_device": s.EMBEDDING_DEVICE,
        "embedding_model": s.EMBEDDING_MODEL,
        "embedding_backend": s.EMBEDDING_BACKEND,
    }
    try:
        import torch

        info["torch_version"] = torch.__version__
        info["torch_cuda_version"] = torch.version.cuda
        info["torch_cuda_available"] = torch.cuda.is_available()
        info["torch_threads"] = torch.get_num_threads()
    except Exception:  # pragma: no cover - torch optional
        info["torch_version"] = None
        info["torch_cuda_version"] = None
        info["torch_cuda_available"] = False
    info["faiss_backend"] = _faiss_backend()
    return info


@router.get("/health")
async def health_check() -> dict[str, object]:
    payload: dict[str, object] = {"status": "ok", "service": "xninetzy-ai"}
    try:
        payload["ai_runtime"] = _ai_runtime()
    except Exception as e:  # pragma: no cover - health must never 500
        logger.warning("Failed to assemble ai_runtime health block: %s", e)
    return payload
