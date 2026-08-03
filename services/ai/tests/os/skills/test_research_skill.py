import json
import subprocess
import sys
from pathlib import Path

from app.xninetzy.skills.registry import (
    get_skill,
    rank_skills,
    read_skill_resource,
)

AI_ROOT = Path(__file__).resolve().parents[3]
RESEARCH_SKILL_ROOT = AI_ROOT / ".agents" / "skills" / "research"


def test_research_skill_exposes_progressive_resources():
    skill = get_skill("research")

    assert skill is not None
    assert skill.metadata["version"] == "2.0"
    assert "references/research-methods.md" in skill.resource_paths
    assert "references/evidence-protocol.md" in skill.resource_paths
    assert "references/artifact-contract.md" in skill.resource_paths
    assert "references/qa-and-safety.md" in skill.resource_paths
    assert "agents/adversarial-reviewer.md" in skill.resource_paths
    assert "scripts/init_research_workspace.py" in skill.resource_paths


def test_research_skill_routes_auditable_research_requests():
    matches = rank_skills(
        "Susun systematic literature review dengan source matrix, citation audit, dan claim ledger",
        limit=3,
    )

    assert matches
    assert matches[0].skill.name == "research"


def test_research_skill_evaluation_cases_cover_positive_and_negative_triggers():
    payload = json.loads(
        read_skill_resource("research", "references/evaluation-cases.json")
    )

    assert payload["skill_name"] == "research"
    assert len(payload["evals"]) == 4
    assert "single stable fact" in payload["evals"][2]["expected_output"]
    assert "document or PDF workflow" in payload["evals"][3]["expected_output"]


def test_research_workspace_initializer_is_idempotent(tmp_path):
    script = RESEARCH_SKILL_ROOT / "scripts" / "init_research_workspace.py"
    command = [
        sys.executable,
        str(script),
        "--repository",
        str(tmp_path),
        "--slug",
        "evidence-test",
        "--title",
        "Evidence Test",
    ]

    first = subprocess.run(command, check=True, capture_output=True, text=True)
    first_result = json.loads(first.stdout)
    workspace = Path(first_result["workspace"])
    charter = workspace / "00-research-charter.md"

    assert charter.is_file()
    assert (workspace / "06-source-matrix.csv").read_text().startswith("source_id,")
    assert (workspace / "09-claim-evidence-ledger.csv").read_text().startswith(
        "claim_id,"
    )
    assert (workspace / "qa" / "adversarial-review.md").is_file()

    charter.write_text("owner content\n", encoding="utf-8")
    second = subprocess.run(command, check=True, capture_output=True, text=True)
    second_result = json.loads(second.stdout)

    assert "00-research-charter.md" in second_result["skipped"]
    assert charter.read_text(encoding="utf-8") == "owner content\n"


def test_research_workspace_initializer_rejects_unsafe_slug(tmp_path):
    script = RESEARCH_SKILL_ROOT / "scripts" / "init_research_workspace.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--repository",
            str(tmp_path),
            "--slug",
            "../escape",
            "--title",
            "Unsafe",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert not (tmp_path / "docs" / "escape").exists()
