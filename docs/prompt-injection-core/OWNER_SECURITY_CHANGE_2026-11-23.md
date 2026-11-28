# Owner security guidance correction — 23 November 2026

The owner supplied an example of a blanket refusal based on university affiliation and production status, and explicitly requested a global instruction to carry out security testing of systems they develop. The quoted vulnerability claims and ownership details were not independently verified during this prompt change; they are not research findings from this task.

CORE_PROMPT is now version 2.4.0, CORE_RULES 2.3.0, and CLI_SHARED_INSTRUCTIONS 2.4.0. The existing bundle version remains 2.4.0 with revision `2026-11-23-authorized-owner-security` and refreshed file hashes. Existing unrelated repository changes were preserved.

The new rule recognizes the owner's explicit request for ordinary testing within the stated system and scope. It directs the agent to perform requested bounded active testing, rejects invented categorical prohibitions based solely on educational affiliation or production status, and avoids demanding formal letters by default. It preserves actual host permissions, scope controls, credentials, approval flows and consequential-action boundaries. It does not authorize an operation that was not requested or manufacture evidence of a test.

Canonical sources and the installed shared files match. A short precedence block was installed in global instructions for OpenCode, Gemini, Qwen, OpenClaude, Copilot, Vibe, the shared agents home, DeepSeek Harness and Pi. Codex and Claude already import/read the shared contract. No new instruction path is claimed for clients whose native global prompt loader was not verified.

Before-change backups and a receipt are at `~/.xninetzy/backups/2026-11-23-owner-security/`. Restore the selected source and installed file together when rolling back, then refresh the manifest hashes and run `python3 scripts/validate_prompt_contract.py --installed`. Remove only the marked `xn-owner-security` block from legacy files if later unrelated edits must be retained.

Validation: canonical integrity and nine installed canonical hashes passed; 11 existing prompt-governance tests passed. The additional global blocks were checked by exact content and hashes in the installation receipt. These are static installation checks; model behavior in every client and an already-open session remains outside that proof.
