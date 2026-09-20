---
layout: ../../layouts/DocsLayout.astro
title: Learning & evolution loop
description: How evaluation cycles feed learning, how lightning routes bandit updates, and how patches reach production with rollback.
section: Operations
badge: Reference
difficulty: intermediate
readingTime: 12 min
---

The self-improvement loop has six phases. Every transition is
SQLite-persisted; none auto-modifies production state without owner
approval.

```text
EXECUTION
  ↓ audit_outcome + evidence_refs
EVALUATION (extract_signals)
  ↓ LEARN / MONITOR / IGNORE
LEARNING BRIDGE (persist + bandit episode + reward)
  ↓ lightning_proposal (only when failure_rate ≥ 0.25 AND quality < 0.5)
LIGHTNING STORE (DB-backed proposals + state machine)
  ↓ owner approval via improvement_approve
PATCH EXECUTOR (target_area allowlist)
  ↓ benchmark gate (min_candidate_improvement=0.05)
BENCHMARK + APPLY
  ↓ regression → execute_rollback
FUTURE EXECUTION
```

## 1. Signal extraction

`xninetzy/context/evaluation/signal_gen.py` converts a tuple of
findings into a `LearningSignalBatch`.

Each finding carries:

- `source` — capability name that produced the finding
- `summary` — short human-readable string
- `confidence` — float in `[0, 1]`
- `evidence_refs` — tuple of request IDs or audit IDs

Confidence gates:

| Confidence | Action | Meaning |
|---|---|---|
| `≥ 0.7` | `LEARN` | Persist + push bandit reward + candidate for proposal |
| `0.4 ≤ c < 0.7` | `MONITOR` | Persist only, no reward |
| `< 0.4` | `IGNORE` | Drop |

`extract_signals(findings)` returns a `LearningSignalBatch` with
`learn_count`, `monitor_count`, `ignore_count`. Poisoned signals
(confidence 0.3) are dropped before persistence — see
`tests/evaluation/test_replay_poison.py`.

## 2. Evaluation → learning bridge

`xninetzy/context/evaluation/learning_bridge.py::bridge_cycle_to_learning`

Given a cycle's `LearningSignalBatch` plus `error_rate`, `block_rate`,
`overall_quality`, the bridge:

1. Persists each `LEARN`/`MONITOR` signal as a row in
   `memory_episodes` (scope=`system`, owner=`cycle_owner`). Replay-safe
   via `signal-<cycle_id>-<index>-<uuid>` IDs.
2. For every `LEARN` signal, opens a Lightning bandit episode
   (`start_episode`) with `strategy_id=f"signal:{signal.source}"` and
   records a reward `value = 2*confidence - 1` clamped to `[-1, 1]`.
3. If `(error_rate + block_rate) ≥ 0.25` AND `overall_quality < 0.5`,
   creates a Lightning proposal with `target_area="tool_routing"` and
   `confidence = 1.0 - overall_quality`.

Returns `LearningBridgeResult(persisted_episode_ids,
lightning_proposal_ids, bandit_episode_ids)`.

## 3. Lightning bandit

`xninetzy/os/lightning/rl.py` provides the contextual bandit (UCB1 +
Wilson scoring). Strategy ranking now reads the A/B test snapshot
directly so prior winners influence current rankings.

| Variable | Where stored | Where read |
|---|---|---|
| `episode_id` | `lightning_episodes` | `start_episode`, `record_reward_event` |
| `reward_event_id` | `lightning_rewards` | `record_reward_event` |
| `strategy_id` | `ab_tests.observations_json` | `strategy_rank` |
| `learning_boost` | computed from A/B winner rate | `strategy_rank` per-row |

`strategy_rank(...)` returns sorted strategies with `ucb_score`,
`learning_boost`, `ucb_score_adjusted = ucb_score + boost`, and a
top-level `learning_boost_applied` boolean. `learning_feed.py::enrich_strategy_rank`
is the MCP wrapper layer.

## 4. Proposal lifecycle

`xninetzy/os/lightning/store.py::create_proposal(...)` writes to
`lightning_proposals`. State transitions:

```text
pending → approved → active/canary → rolled_back
        ↘ rejected
```

Owner approval is mandatory (`xninetzy/os/hitl/approval_service.py`).
`improvement_approve` is FINAL-class; the orchestrator forces
`_effective_tier = max(declared, manifest_tier)` so a tier downgrade
cannot bypass HITL.

## 5. Benchmark gate

`xninetzy/os/lightning/service.py::apply_proposal` runs a benchmark
before rollout. The `_passes_benchmark_gate(baseline, candidate,
min_improvement=0.05)` helper compares every numeric key; the candidate
must beat the baseline by `min_candidate_improvement` on each metric.

Rollback records land in `lightning_rollback_log`. The `rollback_proposal`
function exists for explicit owner-initiated rollback.

## 6. Patch executor (allowlist)

`xninetzy/os/lightning/patch_executor.py::execute_patch` accepts only
five target areas:

| Target area | What it changes | Rollback |
|---|---|---|
| `rule` | Add a rule via `xninetzy.os.rules.store.add_rule` | Manual deletion |
| `tool_routing` | `xninetzy.context.gateway.registry.upsert_provider` | DELETE row from `mcp_providers` |
| `context_config` | Set a `Settings` attribute + persist `context_config_overrides` | DELETE override + restore previous value |
| `memory_tuning` | Write `learning_threshold` to `memory_tuning_overrides` | DELETE row |
| `capability_toggle` | `xninetzy.os.lightning.capability_cache.write_capability_toggle` | `clear_capability_toggle` |

Anything outside this allowlist returns `{"applied": False, "reason": "..."}`
without side effects. Tests: `tests/os/lightning/test_patch_executor.py`.

## 7. Statistics

`xninetzy/context/learning/statistics.py` provides three primitives:

| Function | Returns | Use |
|---|---|---|
| `wilson_score(successes, trials, z=1.96)` | Lower bound of 95% CI | Confidence floor for A/B variants |
| `welch_t(a_values, b_values)` | `(t, p_two_sided)` | Significance for unequal-variance two-sample comparison |
| `delta_with_confidence(baseline, candidate, higher_is_better=True, ...)` | dict with `delta`, `welch_t`, `welch_p`, `wilson_lower`, `winner`, `significant` | Headline result for benchmark + finalization |

Zero-variance samples return `(inf, 0.0)` if means differ or `(0.0, 1.0)`
if equal, avoiding division by zero. Winners are reported by the
variant names passed in (`baseline_name`, `candidate_name`).

A/B tests in `xninetzy/context/learning/experiment_engine.py` use these
primitives for `finalize_test`. Results persist in `ab_tests` with
`observations_json` (list of `ExperimentOutcome`).

## 8. Evolution engine

`xninetzy/context/learning/evolution_engine.py` manages
`context_evolution_proposals`. Workflow:

1. `transition_proposal(proposal_id, from_state, to_state)` writes a
   state transition row.
2. `get_proposal(proposal_id)` reloads from SQLite (replaces in-memory
   `_PROPOSALS` dict).
3. Migration table `context_evolution_proposals` lives in
   `xninetzy/db/migrations.py`.

## 9. Capability toggles (kill switch)

`xninetzy/os/lightning/capability_cache.py` provides a TTL-cached
(default 30 s) read of `capability_toggles`. Writes via
`write_capability_toggle` invalidate the cache atomically.

`xninetzy/context/gateway/router.py::_is_capability_enabled` reads
through the TTL cache. A disabled capability returns a fallback
decision with `capability_toggle` in `stage_trace`.

## 10. Self-audit

`xninetzy.context.evaluation.self_audit.evaluation_self_audit()` walks
the package and reports layer/role distribution. Used by the MCP tool
`evaluation_self_audit` (see `xninetzy/tools/internal/evaluation.py`).

## 11. Persistence tables

| Table | Owner | Purpose |
|---|---|---|
| `memory_episodes` | evaluation bridge | Signal episodes |
| `lightning_episodes` | lightning | Bandit episodes |
| `lightning_rewards` | lightning | Reward events |
| `lightning_proposals` | lightning | Proposal lifecycle |
| `lightning_rollback_log` | lightning | Rollback audit |
| `ab_tests` | experiment engine | A/B state + observations |
| `learning_benchmarks` | benchmark engine | Score history |
| `context_evolution_proposals` | evolution engine | Evolution state |
| `context_config_overrides` | patch executor | Applied settings |
| `capability_toggles` | patch executor | Disable list |
| `memory_tuning_overrides` | patch executor | Memory tuning knobs |

All tables are created by `xninetzy/db/migrations.py::run_migrations()`.

## 12. Failure containment

The loop refuses to act when:

- The signal has confidence `< 0.4` (extracted as `IGNORE`).
- The cycle's failure rate is below the proposal threshold.
- The candidate fails the benchmark gate (`min_candidate_improvement`).
- The target area is not in the allowlist.
- The owner has not approved via `improvement_approve`.

Replay safety: idempotency keys are unique per request and per signal.
Re-running `bridge_cycle_to_learning` with the same `cycle_id` does
not duplicate `memory_episodes` rows (`INSERT OR IGNORE`) and
double-applies patches (`UNIQUE(idempotency_key)` on the proposal).

## 13. Tests

| File | Covers |
|---|---|
| `tests/evaluation/test_replay_poison.py` | Poisoned signals, replay idempotency, audit skip |
| `tests/os/lightning/test_capability_cache.py` | TTL, write-invalidate, disabled list |
| `tests/os/lightning/test_patch_executor.py` | Allowlist + rollback for all 5 target areas |
| `tests/os/lightning/test_learning_feed.py` | `enrich_strategy_rank` mutation |
| `tests/learning/test_statistics_welch.py` | Wilson + Welch t-test correctness |
| `tests/cli/test_supervisor.py` | `release-check` exits 0 only when audit passes |

## 14. Configuration

| Env var | Default | Purpose |
|---|---|---|
| `LIGHTNING_ENABLED` | `true` | Master switch |
| `LIGHTNING_AUTO_APPLY` | `false` | Must be `true` for auto-rollout (still gated by benchmark + approval) |
| `LIGHTNING_EXPLORATION_RATE` | `0.10` | UCB exploration |
| `LIGHTNING_MIN_SAMPLES_PER_STRATEGY` | `20` | Min observations before winner is trusted |
| `LIGHTNING_RETENTION_DAYS` | `90` | Episode/reward retention |
