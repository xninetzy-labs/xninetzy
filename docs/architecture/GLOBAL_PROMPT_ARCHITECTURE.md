# Global prompt architecture and governance

Current canonical bundle: `docs/prompt-injection-core/manifest.json`, version2.3.0.
The manifest pins six shared/client files plus three conditional domain references.
After explicit owner approval, all nine installed hashes match v2.3. Five files
changed (L0/shared plus three references); L1 and all three client adapters were
already matching and remain unchanged. Private backups and recovery instructions
are recorded in Phase2. Native session loading remains a separate verification.
Historical v2.0 measurements below remain dated evidence, not current deployment.

The latest candidate removes repeated tool-map text and loads artifact/design,
shipped-artifact and product-video details only for their domains. The hot shared
file still requires the appropriate reference before dependent work and retains
boundary reminders. Missing or untracked references fail validation; missing
guidance holds that domain's actions. Original deck brief, design source, dynamic
capture and final-render approval rules remain in the hash-pinned references.
CORE_RULES.md is unchanged. Native instruction authority is never downgraded.

The common Codex composition is2653→2109 cl100k_base tokens. All three conditional
references add730 when needed; loading everything can cost more than the baseline.
See [current measurements](../evaluation/CONTEXT_COST_RESULTS.json). This measures
text disclosure, not model task success, actual host injection or billed tokens.

Existing `tool_catalog` and `skill_list` now support filtered/paged opt-in compact
metadata while retaining legacy defaults and full MCP tool enumeration. No
protocol upgrade, client-specific tool removal or new infrastructure is needed.
Full registry schema text increases149 tokens for the optional arguments; savings
are in explicit discovery responses. A fresh isolated source/installed MCP smoke
checks schemas, pagination, selected skill/reference loading and policy denial.
No discovery output grants authorization.

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

The repository validator remains read-only. The approved v2.3 rollout was executed
separately through a private fixed-destination installer, with per-file atomic
publication, backup, intent journal and tested rollback. Recheck installed state:

```bash
python3 scripts/validate_prompt_contract.py
bash scripts/verify_prompt_injection.sh --canonical
bash scripts/verify_prompt_injection.sh
```

The shell's default retains installed inspection; `--canonical` validates only
repository sources. On this owner host the installed comparison now exits0 with
nine matches. Future drift/missing files cause a nonzero result. The validator
never writes host configuration, creates backups, installs files or merges owner
additions. Optional absent client adapters are reported as missing rather than
being silently installed or treated as a requirement to install every client.

The validator is a regression guard for hashes, required references, known unsafe phrases, empty/missing files, unsafe manifest paths, symlinks and unresolved placeholders. It is not a general instruction interpreter, malicious-text detector, LLM behavior evaluator or runtime security boundary. An attacker editing both canonical sources and checks is outside its guarantee. Controlled source review and application authorization remain necessary.

## Evaluation and limits

[Actual context measurements](../evaluation/GLOBAL_AGENTIC_BASELINE.md) use
cl100k_base. The current approved v2.2→v2.3 Codex referenced composition is
2653→2109 tokens, verified again from installed files. The earlier5268→1861
comparison described v2.0 only. Actual host context, model billing, task accuracy,
latency and cross-client behavior are not measured by file token comparison.

Tests in `tests/governance/test_prompt_contract.py` mutate candidate sources, update hashes where appropriate, and assert known conflicts still fail. Separate tests assert owner-installed files remain unchanged and missing/path-escaping sources fail. Existing skill tests now fail new unexpected damage while identifying two rejected historical mirrors explicitly. This does not repair multilingual routing, nested metadata compatibility or all tool references.

No application framework or permanent deployment service is added. The nine
canonical files remain portable; owner additions require review. The approved
rollout uses a private fixed-destination helper, archived with original files,
the reviewed source and a receipt. Phase2 documents the exact private backup,
rollback preview/apply commands and the five isolated installer checks. Rollback
holds later local modifications, restores original bytes/modes and removes only
unchanged new references. No owner database or runtime permission is rolled back.
