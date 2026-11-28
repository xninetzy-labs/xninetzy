from __future__ import annotations

from xninetzy.integrations.kaggle.services import kernels, pipeline
from xninetzy.integrations.kaggle.services.base import KaggleOperationResult
from xninetzy.integrations.kaggle.services.datasets import (
    OPERATIONS,
    auth_status,
    capabilities,
    download,
    get,
    register,
    reset_cache,
    search,
    validate,
)

kernel_push = kernels.push
kernel_status = kernels.status
kernel_output = kernels.output
pipeline_plan = pipeline.plan
pipeline_status = pipeline.status
pipeline_tick = pipeline.tick

__all__ = [
    "KaggleOperationResult",
    "OPERATIONS",
    "auth_status",
    "capabilities",
    "download",
    "get",
    "kernel_output",
    "kernel_push",
    "kernel_status",
    "kernels",
    "pipeline",
    "pipeline_plan",
    "pipeline_status",
    "pipeline_tick",
    "register",
    "reset_cache",
    "search",
    "validate",
]
