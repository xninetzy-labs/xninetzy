from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

EXECUTION_PROVIDER_NAME: str = "flowable_rest"
EXECUTION_OPT_IN_ENV: str = "XNINETZY_FLOWABLE_BASE_URL"


@dataclass(frozen=True, slots=True)
class DeploymentRequest:
    deployment_key: str
    bpmn_xml: str
    tenant_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "deployment_key": self.deployment_key,
            "bpmn_xml_length": len(self.bpmn_xml),
            "tenant_id": self.tenant_id,
        }


@dataclass(frozen=True, slots=True)
class ProcessInstanceRequest:
    process_definition_key: str
    business_key: str
    variables: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_definition_key": self.process_definition_key,
            "business_key": self.business_key,
            "variables": dict(self.variables),
        }


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    deployment: DeploymentRequest
    instance: ProcessInstanceRequest
    base_url: str
    dry_run: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "deployment": self.deployment.to_dict(),
            "instance": self.instance.to_dict(),
            "base_url": self.base_url,
            "dry_run": self.dry_run,
        }


def get_flowable_base_url() -> str | None:
    value = os.environ.get(EXECUTION_OPT_IN_ENV, "").strip()
    return value or None


def is_flowable_enabled() -> bool:
    return get_flowable_base_url() is not None


def plan_execution(
    *,
    deployment_key: str,
    bpmn_xml: str,
    business_key: str,
    process_definition_key: str,
    variables: dict[str, Any] | None = None,
    tenant_id: str | None = None,
) -> ExecutionPlan:
    base_url = get_flowable_base_url()
    enabled = base_url is not None
    return ExecutionPlan(
        deployment=DeploymentRequest(
            deployment_key=deployment_key,
            bpmn_xml=bpmn_xml,
            tenant_id=tenant_id,
        ),
        instance=ProcessInstanceRequest(
            process_definition_key=process_definition_key,
            business_key=business_key,
            variables=dict(variables or {}),
        ),
        base_url=base_url or "",
        dry_run=not enabled,
    )
