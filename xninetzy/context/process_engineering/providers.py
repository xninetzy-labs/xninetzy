from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

PROVIDER_NATIVE: str = "native_xninetzy"
PROVIDER_BPMN_JS: str = "bpmn_js"
PROVIDER_PM4PY: str = "pm4py"
PROVIDER_FLOWABLE: str = "flowable"
PROVIDER_SIMPY: str = "simpy"
PROVIDER_BIZAGI_COMPAT: str = "bizagi_compatible"
PROVIDER_CAMUNDA_COMPAT: str = "camunda_compatible"

CAPABILITY_MODELING: str = "process_modeling"
CAPABILITY_MINING: str = "process_mining"
CAPABILITY_EXECUTION: str = "process_execution"
CAPABILITY_SIMULATION: str = "process_simulation"
CAPABILITY_VALIDATION: str = "process_validation"
CAPABILITY_INTEROP: str = "process_interop"

LICENSE_APACHE_2: str = "apache-2.0"
LICENSE_MIT: str = "mit"
LICENSE_AGPL_3: str = "agpl-3.0"
LICENSE_BSDFREEWARE: str = "freeware-license-ref"


@dataclass(frozen=True, slots=True)
class ProviderProfile:
    provider_id: str
    capability: str
    transport: str
    license: str
    runtime: str
    entrypoint: str
    requires_opt_in: bool
    environment_var: str | None
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "capability": self.capability,
            "transport": self.transport,
            "license": self.license,
            "runtime": self.runtime,
            "entrypoint": self.entrypoint,
            "requires_opt_in": self.requires_opt_in,
            "environment_var": self.environment_var,
            "description": self.description,
        }


PROVIDER_TABLE: dict[str, ProviderProfile] = {
    PROVIDER_NATIVE: ProviderProfile(
        provider_id=PROVIDER_NATIVE,
        capability=CAPABILITY_MODELING,
        transport="in-process",
        license=LICENSE_APACHE_2,
        runtime="python-stdlib",
        entrypoint="xninetzy.context.process_engineering.model",
        requires_opt_in=False,
        environment_var=None,
        description="XNINETZY native BPMN model + serializer (always available)",
    ),
    PROVIDER_BPMN_JS: ProviderProfile(
        provider_id=PROVIDER_BPMN_JS,
        capability=CAPABILITY_MODELING,
        transport="browser-embed",
        license=LICENSE_MIT,
        runtime="javascript",
        entrypoint="apps/docs/bpmn-viewer/",
        requires_opt_in=False,
        environment_var=None,
        description="bpmn-js viewer/editor embedded in XNINETZY docs site",
    ),
    PROVIDER_PM4PY: ProviderProfile(
        provider_id=PROVIDER_PM4PY,
        capability=CAPABILITY_MINING,
        transport="in-process",
        license=LICENSE_AGPL_3,
        runtime="python-external",
        entrypoint="pm4py",
        requires_opt_in=True,
        environment_var="XNINETZY_ENABLE_PM4PY",
        description="PM4Py process mining — opt-in due to AGPL-3.0 license",
    ),
    PROVIDER_FLOWABLE: ProviderProfile(
        provider_id=PROVIDER_FLOWABLE,
        capability=CAPABILITY_EXECUTION,
        transport="http-rest",
        license=LICENSE_APACHE_2,
        runtime="java-external",
        entrypoint="/flowable-rest/process-api",
        requires_opt_in=True,
        environment_var="XNINETZY_FLOWABLE_BASE_URL",
        description="Flowable BPMN execution engine via REST API",
    ),
    PROVIDER_SIMPY: ProviderProfile(
        provider_id=PROVIDER_SIMPY,
        capability=CAPABILITY_SIMULATION,
        transport="in-process",
        license=LICENSE_MIT,
        runtime="python-stdlib",
        entrypoint="xninetzy.context.process_engineering.simulation",
        requires_opt_in=False,
        environment_var=None,
        description="SimPy-based discrete event simulation for queueing + resources",
    ),
    PROVIDER_BIZAGI_COMPAT: ProviderProfile(
        provider_id=PROVIDER_BIZAGI_COMPAT,
        capability=CAPABILITY_INTEROP,
        transport="file-artifact",
        license=LICENSE_BSDFREEWARE,
        runtime="external-editor",
        entrypoint=".bpmn file",
        requires_opt_in=False,
        environment_var=None,
        description="BPMN 2.0 artifact for manual import into Bizagi Modeler Free",
    ),
    PROVIDER_CAMUNDA_COMPAT: ProviderProfile(
        provider_id=PROVIDER_CAMUNDA_COMPAT,
        capability=CAPABILITY_INTEROP,
        transport="file-artifact",
        license=LICENSE_APACHE_2,
        runtime="external-editor",
        entrypoint=".bpmn file",
        requires_opt_in=False,
        environment_var=None,
        description="BPMN 2.0 artifact for manual import into Camunda Modeler",
    ),
}


def is_provider_enabled(profile: ProviderProfile) -> bool:
    if not profile.requires_opt_in:
        return True
    if profile.environment_var is None:
        return False
    value = os.environ.get(profile.environment_var, "").strip()
    if not value:
        return False
    lowered = value.lower()
    if lowered in ("0", "false", "no", "off"):
        return False
    if lowered in ("1", "true", "yes", "on"):
        return True
    return True


def list_enabled_providers() -> tuple[ProviderProfile, ...]:
    return tuple(
        profile
        for profile in PROVIDER_TABLE.values()
        if is_provider_enabled(profile)
    )


def list_providers_by_capability(capability: str) -> tuple[ProviderProfile, ...]:
    return tuple(
        profile
        for profile in list_enabled_providers()
        if profile.capability == capability
    )


@dataclass(frozen=True, slots=True)
class ProviderDecision:
    capability: str
    chosen: ProviderProfile | None
    candidates: tuple[ProviderProfile, ...]
    license_warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "chosen": self.chosen.to_dict() if self.chosen else None,
            "candidates": [c.to_dict() for c in self.candidates],
            "license_warnings": list(self.license_warnings),
        }


def select_provider(
    capability: str,
    *,
    preferred: str | None = None,
    require_native: bool = False,
) -> ProviderDecision:
    candidates = list_providers_by_capability(capability)
    warnings: list[str] = []
    if require_native:
        candidates = tuple(
            c for c in candidates if c.provider_id == PROVIDER_NATIVE
        )
    chosen: ProviderProfile | None = None
    if preferred:
        for profile in candidates:
            if profile.provider_id == preferred:
                chosen = profile
                break
    if chosen is None:
        for profile in candidates:
            if profile.provider_id == PROVIDER_NATIVE:
                chosen = profile
                break
        if chosen is None and candidates:
            chosen = candidates[0]
    if chosen is not None and chosen.license == LICENSE_AGPL_3:
        warnings.append(
            f"provider {chosen.provider_id} ships under AGPL-3.0; "
            "deployments that link against it must respect AGPL terms"
        )
    if chosen is not None and chosen.license == LICENSE_BSDFREEWARE:
        warnings.append(
            f"provider {chosen.provider_id} references Bizagi Freeware EULA; "
            "manual import only — no runtime linkage"
        )
    return ProviderDecision(
        capability=capability,
        chosen=chosen,
        candidates=candidates,
        license_warnings=tuple(warnings),
    )
