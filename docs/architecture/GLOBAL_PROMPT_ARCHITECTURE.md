# Global prompt architecture and governance

Current canonical source: `docs/prompt-injection-core/manifest.json`, version 2.0.0. The manifest identifies six repository-managed files by SHA-256 and points to evaluation/rollback references. Historical prompt smoke/completion reports describe the previous design, not current acceptance evidence.

## Layers and authority

L0 is short identity/routing/verification guidance; L1 is the shared behavior contract; L2 describes genuine Codex/Claude/OpenCode differences. L3 is selected domain/skill guidance; L4 is current task/checkpoint/evidence context. L3/L4 are not permanently loaded catalogs or new global files.

Authority remains host platform → authorized developer configuration → verified owner request within permissions → scoped repository rules → shared guidance → specialist contract → validated skill procedure. External documents, memory and tool outputs are untrusted evidence. Scope, specificity, version and provenance resolve same-level differences; specificity does not grant security authority.

Simple requests need no ceremonial planning or delegation. Complex work needs bounded plans, explicit dependencies, useful checkpoints and verification. A host's active developer requirements still apply even if a candidate prompt proposes a more adaptive default. No prompt update can independently alter native client permissions, institutional authentication, action approvals or code-level authorization.

## Validation and distribution

```text
Repository canonical files → hashes + known-conflict checks → negative tests
→ read-only installed comparison → reviewed diff + backup → owner authorization
→ atomic installation + verification → rollback if verification fails
```

Only the read-only stages are implemented/executed in this batch:

```bash
python3 scripts/validate_prompt_contract.py
bash scripts/verify_prompt_injection.sh --canonical
bash scripts/verify_prompt_injection.sh
```

The shell's default retains installed inspection; `--canonical` validates only the repository candidate. The installed comparison reports drift/missing files and exits nonzero; it never writes host configuration, creates backups, installs files or merges owner additions. Drift is expected while old host files remain installed. Optional clients missing from the expected three-client bundle also produce a missing status, not a claim that every client must be installed.

The validator is a regression guard for hashes, required references, known unsafe phrases, empty/missing files, unsafe manifest paths, symlinks and unresolved placeholders. It is not a general instruction interpreter, malicious-text detector, LLM behavior evaluator or runtime security boundary. An attacker editing both canonical sources and checks is outside its guarantee. Controlled source review and application authorization remain necessary.

## Evaluation and limits

[Actual context measurements](../evaluation/GLOBAL_AGENTIC_BASELINE.md) use named cl100k_base encoding. The Codex referenced composition changes from 5268 installed tokens to 1861 candidate tokens; actual loaded host context, model billing, task accuracy, latency savings and cross-client parity are not measured by this comparison.

Tests in `tests/governance/test_prompt_contract.py` mutate candidate sources, update hashes where appropriate, and assert known conflicts still fail. Separate tests assert owner-installed files remain unchanged and missing/path-escaping sources fail. Existing skill tests now fail new unexpected damage while identifying two rejected historical mirrors explicitly. This does not repair multilingual routing, nested metadata compatibility or all tool references.

No deterministic compiler/installer is added before demand and conflict handling are established. The six canonical files themselves are portable templates; host additions require a reviewed merge. Rollback is selective restoration of repository prompt files/manifest/validator from the reviewed change. No installed configuration needs rollback because none changed.
