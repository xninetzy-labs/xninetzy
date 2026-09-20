from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class SelfAuditSnapshot:
    total_tools: int
    total_groups: int
    evaluation_layers: tuple[str, ...]
    learning_engines: tuple[str, ...]
    reasoning_modules: tuple[str, ...]
    evaluation_files: tuple[str, ...]
    learning_files: tuple[str, ...]
    process_engineering_providers: tuple[str, ...]
    exam_qa_artifacts: tuple[str, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_tools": self.total_tools,
            "total_groups": self.total_groups,
            "evaluation_layers": list(self.evaluation_layers),
            "learning_engines": list(self.learning_engines),
            "reasoning_modules": list(self.reasoning_modules),
            "evaluation_files": list(self.evaluation_files),
            "learning_files": list(self.learning_files),
            "process_engineering_providers": list(self.process_engineering_providers),
            "exam_qa_artifacts": list(self.exam_qa_artifacts),
            "notes": list(self.notes),
        }


def _list_module_files(package: str) -> tuple[str, ...]:
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    package_root = os.path.normpath(os.path.join(here, "..", ".."))
    target = os.path.normpath(os.path.join(package_root, package.replace(".", os.sep)))
    if not os.path.isdir(target):
        return ()
    return tuple(
        sorted(
            os.path.relpath(os.path.join(root, name), package_root)
            for root, _dirs, files in os.walk(target)
            for name in files
            if name.endswith(".py")
        )
    )


def build_self_audit() -> SelfAuditSnapshot:
    from xninetzy.context.evaluation import __all__ as eval_all
    from xninetzy.context.learning import __all__ as learn_all
    from xninetzy.context.reasoning import __all__ as reason_all
    from xninetzy.tools.registry import get_tool_groups

    groups = get_tool_groups()
    total_tools = sum(len(names) for names in groups.values())
    eval_modules = {
        "outcome",
        "context_eval",
        "memory_eval",
        "routing_eval",
        "skill_eval",
        "tool_eval",
        "security_eval",
        "hallucination",
        "root_cause",
        "benchmark",
        "scoring",
        "signal_gen",
        "audit",
        "catalog_audit",
        "integration",
        "self_audit",
    }
    learning_modules = {
        "pattern_engine",
        "experiment_engine",
        "benchmark_engine",
        "evolution_engine",
        "statistics",
    }
    reasoning_modules = {"depth", "critic", "stop"}
    provider_constants = (
        "PROVIDER_NATIVE",
        "PROVIDER_BPMN_JS",
        "PROVIDER_PM4PY",
        "PROVIDER_FLOWABLE",
        "PROVIDER_SIMPY",
        "PROVIDER_BIZAGI_COMPAT",
        "PROVIDER_CAMUNDA_COMPAT",
    )
    notes: list[str] = []
    eval_present = sum(1 for name in eval_modules if name in eval_all)
    learn_present = sum(1 for name in learning_modules if name in learn_all)
    reason_present = sum(1 for name in reasoning_modules if name in reason_all)
    notes.append(
        f"evaluation modules exposed: {eval_present}/{len(eval_modules)}"
    )
    notes.append(
        f"learning engines exposed: {learn_present}/{len(learning_modules)}"
    )
    notes.append(
        f"reasoning modules exposed: {reason_present}/{len(reasoning_modules)}"
    )
    return SelfAuditSnapshot(
        total_tools=total_tools,
        total_groups=len(groups),
        evaluation_layers=tuple(sorted(eval_modules)),
        learning_engines=tuple(sorted(learning_modules)),
        reasoning_modules=tuple(sorted(reasoning_modules)),
        evaluation_files=_list_module_files("context/evaluation"),
        learning_files=_list_module_files("context/learning"),
        process_engineering_providers=provider_constants,
        exam_qa_artifacts=(
            "fixture",
            "scenario",
            "state_machine",
            "selector",
            "provider",
            "assertions",
        ),
        notes=tuple(notes),
    )
