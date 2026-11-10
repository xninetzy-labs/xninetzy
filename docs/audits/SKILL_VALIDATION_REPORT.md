# Skill Inventory and Validation Report

Audit date: 2026-11-10. Repository baseline: `main` at `2d0f13f`, with preexisting user changes preserved. This report records the baseline before candidate prompt changes. Evidence labels: `VERIFIED_CODE` for inspected files; `VERIFIED_RUNTIME` for local execution; `VERIFIED_TEST` for passing tests; `DOCUMENTED_ONLY` for unexecuted intended behavior; `UNKNOWN` for unavailable evidence.

This inventory recursively inspects SKILL.md text, YAML and hashes. It never executes bundled scripts. Per-root traversal follows installed directory symlinks, de-duplicates repeated resolved directories within that root to prevent loops, and excludes .git/node_modules/__pycache__/.venv. Plugin cache scope is the installed Codex curated cache and Claude cache; marketplace catalogs and inactive temporary plugin repositories are not treated as installed skills. Skill presence does not prove runtime availability or provenance trust.

## Scope and actual counts

| Root | Recursive files | Strict YAML/required-field errors | Backup/disabled paths | cl100k tokens |
|---|---|---|---|---|
| repo | 166 | 2 | 0 | 239423 |
| codex | 160 | 1 | 0 | 244304 |
| claude | 226 | 1 | 0 | 431383 |
| opencode | 192 | 12 | 12 | 337953 |
| shared | 194 | 1 | 0 | 346804 |
| codex_plugins | 52 | 0 | 0 | 84089 |
| claude_plugins | 0 | 0 | 0 | 0 |

`repo` = .agents/skills; `codex` = ~/.codex/skills; `claude` = ~/.claude/skills; `opencode` = ~/.config/opencode/skills; `shared` = ~/.agents/skills; `codex_plugins` = ~/.codex/plugins/cache/openai-curated-remote; `claude_plugins` = ~/.claude/plugins/cache. Tokens are individual full file counts, not automatic per-request injection cost.

`VERIFIED_CODE`: builtin_skill_dir() points to repository .agents/skills; _load_directory() only uses glob("*/SKILL.md"). Direct built-in scope therefore has **125 files:123 eligible,2 rejected legacy underscore mirrors**. Recursive scope has166 files; root SKILL.md is a catalog document,36 career/self-improvement subskills plus4 bundled PPTX subskills are outside direct discovery. This is a discovery/compatibility boundary, not evidence that domain tools are absent.

`VERIFIED_RUNTIME`: all125 direct files have strict YAML; the only two runtime failures there are exam_qa/process_engineering name validation. Canonical exam-qa/process-engineering files already exist. Recursive inspection finds invalid YAML in career/interview-prep and string-to-string metadata incompatibility in35 other career/self-improvement definitions. Four bundled PPTX subskills have unsupported top-level triggers fields. Do not fix discovery by indiscriminately recursing hidden dependencies or silently accepting arbitrary metadata.

`VERIFIED_CODE`: list_skills/get_skill rediscover and reparse files on every call; built-in override defaults disabled; automatic user injection defaults disabled; resources are listed progressively and read with path/byte limits. Current trust labels are assigned from source location, not cryptographic verification. Ranking uses names/descriptions/topic hints/metadata triggers, without required tool availability filtering; top relative score is rendered confidence but is not a calibrated probability.

## Repo skill contract inventory

Fields not declared in source remain UNKNOWN; descriptions are searchable routing metadata, not grants of authorization. Trust for eligible repository files is trusted-builtin by implementation; third-party provenance is unverified merely from location.

| Skill / path | Version / scope | Tokens | Runtime compatibility | Dependencies / tools metadata | SHA-256 |
|---|---|---|---|---|---|
| .agents/skills/SKILL.md | UNKNOWN / UNKNOWN | 1155 | SKILL.md harus diawali YAML frontmatter yang valid. | {} | 4cd5ff9065c74bd3c1d2cf212d47e7a5fb226ea86f7aaf61205e0d3e0647f159 |
| .agents/skills/academic-editor/SKILL.md | UNKNOWN / editing | 388 | valid; 0 resources | {} | 635f73179fcbb3d6636bc1dc519695550e822e0875717ae50eb11582f9ac33ff |
| .agents/skills/academic-writer/SKILL.md | UNKNOWN / writing | 404 | valid; 0 resources | {} | 161a3dcd84f25ea63252764a3faa7c82c5e1c89556b9336fa217953d314aaa13 |
| .agents/skills/anti-slop/SKILL.md | UNKNOWN / guardrail | 426 | valid; 0 resources | {} | a5137a98751d747285cf8728ed7af6969eae676a1cea07009405e9ee5a841361 |
| .agents/skills/api-security/SKILL.md | UNKNOWN / UNKNOWN | 5764 | valid; 0 resources | {} | 1203063191b9b69c04760429adb7a4c7f6f28cdb0f01c0a4c947c570f7d531c9 |
| .agents/skills/architecture-analysis/SKILL.md | UNKNOWN / UNKNOWN | 5446 | valid; 0 resources | {} | 17244f125e7e9004004352d32c2282141aa2ba4c0db35085434ad149b5e69a62 |
| .agents/skills/argument-coherence/SKILL.md | UNKNOWN / UNKNOWN | 970 | valid; 0 resources | {} | c2c2eef4a2b1188e65f3fff3f5ae721e498d59be6641b4b06c20b965e226148a |
| .agents/skills/benchmark-analysis/SKILL.md | UNKNOWN / UNKNOWN | 539 | valid; 0 resources | {} | aca8329463885331581fbfc26face5d4b342e41c67d77cf8898a622a7c631b32 |
| .agents/skills/business-writer/SKILL.md | UNKNOWN / writing | 398 | valid; 0 resources | {} | b09b31698d699599837beebc4c07382eca4f05f466ce9bffb5e31358d8215904 |
| .agents/skills/career/alternative-titles/SKILL.md | UNKNOWN / UNKNOWN | 288 | metadata harus berupa mapping string ke string. | {} | c2a60507cdd95a5aa4d196fbcbd70fb42b1a03dc270b9bba1a753d0baf12baf8 |
| .agents/skills/career/application-tracking/SKILL.md | UNKNOWN / UNKNOWN | 314 | metadata harus berupa mapping string ke string. | {} | 07566e6753d4586d4a2626290228a21d6a03258e41a1d015239b0e60389121b1 |
| .agents/skills/career/company-research/SKILL.md | UNKNOWN / UNKNOWN | 382 | metadata harus berupa mapping string ke string. | {} | e86e906d82b6376eb87c85ee3100f82ea5b163e0314719284773997c810fef91 |
| .agents/skills/career/company-search/SKILL.md | UNKNOWN / UNKNOWN | 312 | metadata harus berupa mapping string ke string. | {} | f0012d6fffafd7d554d196b9506c121497c5d311c6f991e6bcadd809bb980354 |
| .agents/skills/career/cv-analysis/SKILL.md | UNKNOWN / UNKNOWN | 393 | metadata harus berupa mapping string ke string. | {} | 14b129e35c78b117f8722ae2e94f5d17912dc57bd353341ce299d6cde97a8edd |
| .agents/skills/career/extract-requirements/SKILL.md | UNKNOWN / UNKNOWN | 291 | metadata harus berupa mapping string ke string. | {} | cb57c75aa69097ef688bd913b923de16fa0dfb6ce576bf10fd45fec1176fd7b4 |
| .agents/skills/career/hidden-jobs/SKILL.md | UNKNOWN / UNKNOWN | 325 | metadata harus berupa mapping string ke string. | {} | c0f91e7cf101e79dc44d46af004828bcf8e93801c58ba981e4d9c6ece3d2c91b |
| .agents/skills/career/internship-discovery/SKILL.md | UNKNOWN / UNKNOWN | 405 | metadata harus berupa mapping string ke string. | {} | 77f18c4d791b4aa5cf34e699486e1a4406782a4ba997fa3d4c690a041ce01699 |
| .agents/skills/career/interview-prep/SKILL.md | UNKNOWN / UNKNOWN | 386 | YAML frontmatter tidak valid | {} | 66485ca3ef5f7761c39f0123bf1cbc75ae605a8c01e87a8817682756510860bf |
| .agents/skills/career/job-discovery/SKILL.md | UNKNOWN / UNKNOWN | 477 | metadata harus berupa mapping string ke string. | {} | cc29eaac41ca80ca92f85d6fb7124e2835a9194a75e29acd585cc0c286d4e701 |
| .agents/skills/career/job-matching/SKILL.md | UNKNOWN / UNKNOWN | 405 | metadata harus berupa mapping string ke string. | {} | b1549fdef652bae132d8cf55c139c744de5f1570c9f51ed36ef9a769fae408ed |
| .agents/skills/career/job-monitoring/SKILL.md | UNKNOWN / UNKNOWN | 344 | metadata harus berupa mapping string ke string. | {} | f3c2d90125b9682d7c9d17241bed4489ee8411b5f36efece629283a0dfa594e1 |
| .agents/skills/career/job-risk-analysis/SKILL.md | UNKNOWN / UNKNOWN | 372 | metadata harus berupa mapping string ke string. | {} | e02ab3bbdf7b58a216ba00322b445cb53759174de905179b929322f38de5a260 |
| .agents/skills/career/job-search/SKILL.md | UNKNOWN / UNKNOWN | 438 | metadata harus berupa mapping string ke string. | {} | 719a1c086bef4702fe3738ce612d20282e4740e12da2db344652546526a50263 |
| .agents/skills/career/market-skill-trend/SKILL.md | UNKNOWN / UNKNOWN | 408 | metadata harus berupa mapping string ke string. | {} | 65fdc6acdf13e80033f271d249383b27588b654d465b9518097c4bd25c50eb6a |
| .agents/skills/career/resume-tailoring/SKILL.md | UNKNOWN / UNKNOWN | 374 | metadata harus berupa mapping string ke string. | {} | 68237fe3762724f959b8e33a0fc061d3901d6328603905ca8a76a7163fd47228 |
| .agents/skills/career/salary-analysis/SKILL.md | UNKNOWN / UNKNOWN | 386 | metadata harus berupa mapping string ke string. | {} | 927f1db77aa1174279fc4a486fcc1b951dc63dd7f0f05daf49fa9c47557292ef |
| .agents/skills/career/similar-jobs/SKILL.md | UNKNOWN / UNKNOWN | 302 | metadata harus berupa mapping string ke string. | {} | 9c1f579ef6130d492f2b91bf0b5fda2c3ceb43979fa3cd26601cff3041815627 |
| .agents/skills/career/skill-gap/SKILL.md | UNKNOWN / UNKNOWN | 428 | metadata harus berupa mapping string ke string. | {} | 1d9477eab81534aae106d8af9bbd5461b9fbcaad3c006f1ef6cb5273631cccc7 |
| .agents/skills/citation-validation/SKILL.md | UNKNOWN / review | 941 | valid; 0 resources | {} | 0af168b02c3e0ded78271854eb7c062b08751a5c1cf2718a53cee9b46c64ed6f |
| .agents/skills/claim-lattice/SKILL.md | UNKNOWN / project | 1544 | valid; 0 resources | {} | 8d73475d60e26163f8d6e07dd49fbd26ecacce1c0586dd61b590e5fc6f0cdec2 |
| .agents/skills/cli-creator/SKILL.md | UNKNOWN / UNKNOWN | 7186 | valid; 2 resources | {} | f37263afb9a0c66d6d85e316fbf258e1e248965b10de1edfe6fe747b4ef3f249 |
| .agents/skills/code-review/SKILL.md | UNKNOWN / UNKNOWN | 7082 | valid; 0 resources | {} | 0e5958e3571783a8cce19cef8a12df25c7db082d76cbf9cae5f59678ece446d0 |
| .agents/skills/competition-proposal/SKILL.md | UNKNOWN / writing | 402 | valid; 0 resources | {} | 58cfa8fc400ffd527a52b364d04a4b607b1eb10e93a5bfb1f0bb172a9aafc3a4 |
| .agents/skills/consultant-challenge/SKILL.md | UNKNOWN / review | 392 | valid; 0 resources | {} | 8257e6a72604473201a131081ce520661fe3a5fa65e67238fe9f650963472acd |
| .agents/skills/consultant/SKILL.md | UNKNOWN / analysis | 417 | valid; 0 resources | {} | 38a1ec7e0f8b8d42307160bd4d9488f912dcf7c14c205f7ae1386631fea37604 |
| .agents/skills/consulting-pptx-skill/SKILL.md | UNKNOWN / UNKNOWN | 3232 | valid; 9 resources | {} | 973c838db1e44f364f6695ef86e8f90a74504aee1ba10914f96b0d1a84295a5b |
| .agents/skills/consulting-pptx/SKILL.md | UNKNOWN / UNKNOWN | 1013 | valid; 0 resources | {} | 913fa711c0349746d5cb69f3f4bcfb16e53a8679e5fb3abecc952a0551904c05 |
| .agents/skills/context-engineering/SKILL.md | UNKNOWN / UNKNOWN | 7177 | valid; 0 resources | {} | c1a810f0796bbfbefeba3b119a54f7581ccfdeb74a7c80eb256933528f8dfc92 |
| .agents/skills/contradiction-hunter/SKILL.md | UNKNOWN / UNKNOWN | 468 | valid; 0 resources | {} | 0675c5460eaf7233141035c55fd28f9962f648f75590e1da17a805c8c0cd2820 |
| .agents/skills/cyber-campus/SKILL.md | UNKNOWN / UNKNOWN | 5777 | valid; 4 resources | {} | 2f9baf88354828c1fabdc1c7fc1b052c3be60c1aed17b9a0dd02a25b9a95b287 |
| .agents/skills/data-analysis/SKILL.md | 1.0.0 / UNKNOWN | 610 | valid; 0 resources | {} | 788437361517076801a2be07f4b059bf5d1bd21b6f2175b17153c2a32c71b1ac |
| .agents/skills/debugging/SKILL.md | UNKNOWN / UNKNOWN | 6561 | valid; 0 resources | {} | 2d22d97f0e5d8b1c4e699582ac2f66cfdfe81b4bae6f79346ec9b3f4e4f8bea8 |
| .agents/skills/define-goal/SKILL.md | UNKNOWN / UNKNOWN | 7059 | valid; 3 resources | {} | 68531b47ba2806e2be94c76850516d413681981c9d9097092c5f94b6f13e3d60 |
| .agents/skills/dependency-audit/SKILL.md | UNKNOWN / UNKNOWN | 8361 | valid; 0 resources | {} | 24ae5c89d692de565643aa79f72e1723dafb627fe38ce301a95510700a763821 |
| .agents/skills/evidence-grader/SKILL.md | UNKNOWN / UNKNOWN | 463 | valid; 0 resources | {} | 02fdf8320773cfd6d05fb52e0aa9aa6b6a7e0a98370b152bb48a8e0a910a5394 |
| .agents/skills/evidence-synthesis/SKILL.md | UNKNOWN / research | 752 | valid; 0 resources | {} | 57e0f526fea50430d3faf7ff82b395837cd776c0403922473ac2e31c1ccaeb18 |
| .agents/skills/exam-qa/SKILL.md | 0.1.0 / general | 435 | valid; 3 resources | {} | d19a9ac7ea8475e77a66c29872539b73cbe14405a3ee74f11f1acd0e0463e84b |
| .agents/skills/exam_qa/SKILL.md | 0.1.0 / general | 435 | name harus lowercase kebab-case, 1-64 karakter, tanpa hyphen ganda. | {} | 4b73517232d23453550801daf41eff49ddd217512094a193344dffdd12b3199b |
| .agents/skills/executive-writer/SKILL.md | UNKNOWN / writing | 411 | valid; 0 resources | {} | 10b2aab99ef39184f446f8356508f6d5e584688e65642e727c2b0dea26411a12 |
| .agents/skills/gh-fix-ci/SKILL.md | UNKNOWN / UNKNOWN | 892 | valid; 4 resources | {} | 66ffd7fd69abc96527d8cde3920490eaff1b686ce29152ab97e0f577c47f11a6 |
| .agents/skills/grant-proposal/SKILL.md | UNKNOWN / writing | 402 | valid; 0 resources | {} | 5b796c40ab5b92481bf2956d74bf58fb5e0bc206cb48d4cbb5cfca663b8e3eac |
| .agents/skills/graph-rag/SKILL.md | UNKNOWN / UNKNOWN | 8913 | valid; 4 resources | {} | fd294179bdad92ad091af0a082add852b2d27186c413f3809e26c6dbe22b184a |
| .agents/skills/hebat-academic/SKILL.md | UNKNOWN / UNKNOWN | 4028 | valid; 4 resources | {} | b0d3c305b9e05cfebaf91fcb265bb0346a4e15f0a0a668a6ead6773e3d440ffd |
| .agents/skills/hebat-assignment/SKILL.md | UNKNOWN / UNKNOWN | 5080 | valid; 3 resources | {} | de2b27b3fd35d7e334186d6700d6df13e9cfccf6523db1b2b1d8db167955ccaf |
| .agents/skills/it-learning/SKILL.md | UNKNOWN / UNKNOWN | 1534 | valid; 4 resources | {} | c24d46654a7742ed263102be08fdb3047d87a5d49a5ad407c081608a2039806b |
| .agents/skills/jupyter-notebook/SKILL.md | UNKNOWN / UNKNOWN | 934 | valid; 10 resources | {} | 735c09068509503cffd764e6d32be58e734cc9e7c6f14aab1c26c394c7d6c7d1 |
| .agents/skills/kaggle/SKILL.md | 1.0.0 / general | 593 | valid; 0 resources | {} | fe10dcdc9dc2afd0520761fcaac36176612761ea711df1b69b40f4085a2bbd55 |
| .agents/skills/life-management/SKILL.md | UNKNOWN / UNKNOWN | 1648 | valid; 5 resources | {} | 7bc57608409c31342cfc45808b23ba3f5454dabd147a082b100604326b59d8be |
| .agents/skills/literature-review-writer/SKILL.md | UNKNOWN / writing | 411 | valid; 0 resources | {} | f6e66ff67f10024908902aae063a44de4446cafeb7c8f1f641888702bcf5a083 |
| .agents/skills/literature-review/SKILL.md | UNKNOWN / UNKNOWN | 653 | valid; 0 resources | {} | 61b457849ad8f32c32ab71cac908a419db82efc68c6012550612ae22043d6abb |
| .agents/skills/mcp-development/SKILL.md | 1.0.0 / domain | 1848 | valid; 0 resources | {"required_tools": "[\"tool_catalog\",\"skill_list\",\"grep_search\",\"read_file\",\"write_file\",\"bash_run\",\"pytest_run\",\"manifest_for\",\"meta_for\"]", "prerequisites": "[\"target tool name (or \\\"all\\\")\",\"explicit git branch\"]"} | 26a3e1e376efd2012197f0322020bdf1f3acc3ad1f9a86688cf74c6622cb3601 |
| .agents/skills/mcp-discovery/SKILL.md | UNKNOWN / UNKNOWN | 584 | valid; 0 resources | {} | b3c02d2151a328628fba78015d17142509d66fa50a663a4338694e604d0418fb |
| .agents/skills/media-video-capture/SKILL.md | UNKNOWN / media | 962 | valid; 0 resources | {} | bb2600cdef72761727b14a40608c0cc85dfc554e37c113c8830eb2a2a818d91e |
| .agents/skills/media-video-development/SKILL.md | UNKNOWN / media | 771 | valid; 0 resources | {} | 93676b4984b7233c0a65f463a97f4b72189a6abd033cfa2c7901a4c3c6df9b2a |
| .agents/skills/media-video-edit/SKILL.md | UNKNOWN / media | 725 | valid; 0 resources | {} | 16bfb94147c627c0c0351cd3b9f05d6cb67b62292febe0e7e266d9be7b06e105 |
| .agents/skills/media-video-motion/SKILL.md | UNKNOWN / media | 806 | valid; 0 resources | {} | 044043eaa13adece2766e21c6e71d344de68c1d8e2868ed55f2861b47d3ea467 |
| .agents/skills/media-video-project-demo/SKILL.md | UNKNOWN / media | 908 | valid; 0 resources | {} | 8dc62ba42dfd4b92e3d966db43720dcd01a27c6a7c237f7aa546cadeea93df2d |
| .agents/skills/media-video-render/SKILL.md | UNKNOWN / media | 947 | valid; 0 resources | {} | 6e4c8cb42466951051036d863b2ac97289ca483e98827e1c8a5e0311d1b68878 |
| .agents/skills/media-video-root/SKILL.md | UNKNOWN / media | 1094 | valid; 0 resources | {} | fe6e1de4e4fdad75fae0d7e24460f564c5716be888972fb35e5c010497e6f974 |
| .agents/skills/media-video-tutorial/SKILL.md | UNKNOWN / media | 726 | valid; 0 resources | {} | 9b5b5a4c9abe2dae8214b0d170d698349e969b65cc868c7e6008aaa260615ae2 |
| .agents/skills/memory-chat/SKILL.md | UNKNOWN / UNKNOWN | 1753 | valid; 3 resources | {} | b7bbfabb0be019fbbc8ce5e7c078589725c47c3d6f540fd3a1ee27e2dda1cb1f |
| .agents/skills/memory-management/SKILL.md | 1.0.0 / harness | 1552 | valid; 0 resources | {"required_tools": "'[\"memory_add\",\"memory_search\",\"memory_forget\",\"memory_list\",\"memory_update_tool\",\"lightning_record_action\",\"lightning_record_outcome\",\"lightning_episode_finish\"]'", "prerequisites": "'[\"storage layer is identified\",\"policy table for memory scoping"} | 620a86e9039bf2445b632b07a263698ba1dab2353c9610a2ffd024bc7dc27daf |
| .agents/skills/methodology-rater/SKILL.md | UNKNOWN / paper-analysis | 1772 | valid; 0 resources | {} | b0f99aadd4f3d3346691824c99e78ebd55464d6da339b11480de3ff55afeda4e |
| .agents/skills/multi-agent-orchestration/SKILL.md | 1.0.0 / harness | 1556 | valid; 0 resources | {"required_tools": "[\"lightning_episode_start\",\"lightning_episode_finish\",\"lightning_record_action\",\"lightning_record_outcome\",\"todo_tool\",\"hitl_request_approval\"]", "prerequisites": "[\"project plan exists (use `structured-project-execution`)\",\"sub-agents declared with non-overlapping responsibilities\",\"merge strategy stated before execution begins\"]"} | 101ef2b7e5951f717ce19a15899b90a13e8da00b723578d3efe6a2065effdf7f |
| .agents/skills/obsidian-knowledge/SKILL.md | UNKNOWN / UNKNOWN | 350 | valid; 1 resources | {} | a6b9c662d9c715b6958c8441001e10497647b876c964788dcbdafdab6a1f157d |
| .agents/skills/obsidian-ops/SKILL.md | 1.0.0 / UNKNOWN | 417 | valid; 0 resources | {} | 4d50723d3ad14fdcebd4bda81f57964895f9d75a19ce229d5bd60c500f8cfd1f |
| .agents/skills/outline-builder/SKILL.md | UNKNOWN / skill | 1664 | valid; 0 resources | {} | 532830f1a9d223ca116ab84646251b9c355518b70702e9788c2abce9216236c0 |
| .agents/skills/paper-analysis/SKILL.md | UNKNOWN / UNKNOWN | 759 | valid; 0 resources | {} | 829c8cb275d335108ef7cec63ef2a035e254ddcec49ee2a9579ed3c82eb86277 |
| .agents/skills/paper-review/SKILL.md | UNKNOWN / review | 398 | valid; 0 resources | {} | e875f7550fba9a6d26bd788c0398a32b14edc87c3c15e2cf08787ca4895d6920 |
| .agents/skills/pdf/SKILL.md | UNKNOWN / UNKNOWN | 3125 | valid; 10 resources | {} | 51cde8bdc880d44e9e13e629d618462be4563e4803219a2ed189ffe39635c3f2 |
| .agents/skills/personal-os/SKILL.md | 1.0.0 / UNKNOWN | 520 | valid; 0 resources | {} | 29a76589da05e4162a439ad14d45f32cb229ec9d7b17b2812fe192a08ac31571 |
| .agents/skills/playwright-interactive/SKILL.md | UNKNOWN / UNKNOWN | 6801 | valid; 3 resources | {} | 2529dd902005f12c89b65aed648cd22af4d4e7ba7e991159f73e2db740c48ff5 |
| .agents/skills/playwright-mcp-workflows/SKILL.md | 1.0.0 / domain | 1116 | valid; 0 resources | {"required_tools": "'[\"web_discover\",\"web_fetch\",\"web_analysis_refresh\",\"image_inspect\",\"image_preprocess\",\"image_ocr\",\"image_compare\",\"web_source_ledger\"]'", "prerequisites": "'[\"explicit authorized target (use `security_scope`)\",\"Playwright"} | 66410f6a3a31664ba7d4318ada23a8632adffe79a67cce9b6d1e5d3e9e59ae0f |
| .agents/skills/playwright/SKILL.md | UNKNOWN / UNKNOWN | 946 | valid; 6 resources | {} | d5693079440907bd2d8dde943ee096212dc276c90437512ce4ed802aa2b0f976 |
| .agents/skills/pptx-skills/.claude/skills/markitdown/SKILL.md | 1.0.0 / UNKNOWN | 1035 | Frontmatter tidak dikenal: triggers | {} | cf2e206be8baf949216a70b321d8b124b9ca534d36cf6a10c1cc47c9a95749a9 |
| .agents/skills/pptx-skills/.claude/skills/slide-analyze/SKILL.md | 1.0.0 / UNKNOWN | 1399 | Frontmatter tidak dikenal: triggers | {} | 32d4cdadce4d654673c07516b2f8d8cb979231840926d2cb495bc991c024d734 |
| .agents/skills/pptx-skills/.claude/skills/slide-edit/SKILL.md | 1.0.0 / UNKNOWN | 1348 | Frontmatter tidak dikenal: triggers | {} | b2847845e2819ff84a7c045ed07ee4c60aef73845166622592e79214b10bef6a |
| .agents/skills/pptx-skills/.claude/skills/slide-generate/SKILL.md | 1.0.0 / UNKNOWN | 1724 | Frontmatter tidak dikenal: triggers | {} | ad87f1a97a1645a0daa223358f79bdbfbb9c4dad0459cb04146fc34cf189143b |
| .agents/skills/pptx-skills/SKILL.md | UNKNOWN / UNKNOWN | 559 | valid; 0 resources | {} | 9ca9e518127ee10a6db771b51b3aa007f8a93230ee85e1626006b9e7126bb34d |
| .agents/skills/process-engineering-providers/SKILL.md | UNKNOWN / UNKNOWN | 685 | valid; 0 resources | {} | f512f27a4b69425ffd9b06e331a4e02c7aad05e62226aae057e2c1e5d7b750be |
| .agents/skills/process-engineering/SKILL.md | 0.1.0 / general | 601 | valid; 3 resources | {} | 2fe81dccdf6bbed79105a7ed68ff858a6fee35d55bf49ee384d34d75bd977d9c |
| .agents/skills/process_engineering/SKILL.md | 0.1.0 / general | 404 | name harus lowercase kebab-case, 1-64 karakter, tanpa hyphen ganda. | {} | 0ce5856b9c39cc200d95006c350f2d2b3e32af58a8a762057f8934439c18fe4b |
| .agents/skills/professional-editor/SKILL.md | UNKNOWN / editing | 412 | valid; 0 resources | {} | 91dadc5ef8e9dad1ea7b6c59cef392dc5d46d7a90fc21a85d1f9d2f759c3c7bc |
| .agents/skills/professional-writer/SKILL.md | UNKNOWN / writing | 518 | valid; 0 resources | {} | 0cef09ebe9890e2889f8f45abdb426ac589881f4568cde0e9931a740a3390c87 |
| .agents/skills/proposal-red-team/SKILL.md | UNKNOWN / review | 401 | valid; 0 resources | {} | 5ecd43d84f83af62bca442f3a3257ec9c9e762f73d467df641d5461fbc147f88 |
| .agents/skills/proposal-writer/SKILL.md | UNKNOWN / writing | 405 | valid; 0 resources | {} | f1c2cd635efbaecde5323f7d40fe5153a70eb12eb9fea52dad00871afedacd4d |
| .agents/skills/reasoning-critic/SKILL.md | UNKNOWN / UNKNOWN | 448 | valid; 0 resources | {} | 996ce829eb0a203333b9a380be8619b3dc5072f9cad407c2a5cac53f719cd8b2 |
| .agents/skills/reasoning-orchestrator/SKILL.md | UNKNOWN / UNKNOWN | 853 | valid; 0 resources | {} | 9a3cc386c644131aba52d69da0061c3b307e2d9dd54097236208b7a50949d4e6 |
| .agents/skills/reasoning-strategy-learner/SKILL.md | UNKNOWN / UNKNOWN | 399 | valid; 0 resources | {} | e0fd1c7a44c7ee5c13cb5d969f83e00a8ba1cb432e7ae5a27b379985e489fbb8 |
| .agents/skills/regression-analysis/SKILL.md | 1.0.0 / domain | 511 | valid; 0 resources | {"required_tools": "'[\"repo_diff\",\"repo_search\",\"repo_symbol\",\"repo_test\",\"repo_risk\"]'", "prerequisites": "'[\"failing test or metric trace reachable\",\"pre-regression baseline"} | fcfceb0b2f2f7bd9fa285be712bbf66e6ebbdf08df4387dbe7d2cdd6642d1df6 |
| .agents/skills/repo-context-packaging/SKILL.md | 1.0.0 / domain | 1363 | valid; 0 resources | {"required_tools": "'[\"read_file\",\"grep_search\",\"glob_files\",\"repo_search\",\"repo_symbol\",\"repo_dependency\",\"repo_architecture\",\"repo_test\"]'", "prerequisites": "'[\"repository root\",\"target intent\"]'"} | 9a3ed45936de1f4f5ad2538001df05142c96b39a2f1e9fedfb1dceb79cf8cd2d |
| .agents/skills/requirement-coverage/SKILL.md | UNKNOWN / UNKNOWN | 830 | valid; 0 resources | {} | 449f78b8aa67903f106bb1aea1f80014cd2ae2aafe26c3fddbc94657d922dc95 |
| .agents/skills/research-critic/SKILL.md | UNKNOWN / UNKNOWN | 578 | valid; 0 resources | {} | a7d6bb1b788696de37ade981a008c3cbfd79c6c5384e5d20357ffbda074ef7fa |
| .agents/skills/research-paper-writer/SKILL.md | UNKNOWN / writing | 404 | valid; 0 resources | {} | e6b5af989654d9833aec12e8665e04332b2b61fd4f13ba8df36359bc1fa0f9bf |
| .agents/skills/research-planner/SKILL.md | UNKNOWN / UNKNOWN | 616 | valid; 0 resources | {} | e6888e8bf01b3643076263088752f32708337f65bc37ada73fc7fc2f54a9f542 |
| .agents/skills/research-proposal/SKILL.md | UNKNOWN / writing | 401 | valid; 0 resources | {} | 291ba454e45c1724c366884f1a9e5d482408276c1617ab551babeb052813b99e |
| .agents/skills/research/SKILL.md | UNKNOWN / UNKNOWN | 2637 | valid; 8 resources | {} | 3d8afc8a7fd31151ba4c34aa94b127c0aea4b514ab923c95e66e4429c4cec7cf |
| .agents/skills/scientific-paper-writer/SKILL.md | UNKNOWN / writing | 400 | valid; 0 resources | {} | bb7903316aca315ffc7bf2ce745e6323ce8dcc38d2ca274ea492499f444c9080 |
| .agents/skills/scoring-rubric/SKILL.md | UNKNOWN / xninetzy | 1617 | valid; 0 resources | {} | c452e27b3f276b244604de9b4bd2f2690f214b06ee1da657601128004bb62eb8 |
| .agents/skills/screenshot/SKILL.md | UNKNOWN / UNKNOWN | 1915 | valid; 9 resources | {} | e54300fdc7c9c6a683263dabb4cf5a4967ec77d343faed439bc6586caea87c36 |
| .agents/skills/secret-audit/SKILL.md | 1.0.0 / domain | 637 | valid; 0 resources | {"required_tools": "'[\"repo_search\",\"repo_symbol\",\"security_scope\",\"security_sast\",\"security_validate_finding\",\"lightning_record_action\"]'", "prerequisites": "'[\"explicit authorized scope (via `security_scope`)\",\"target repo"} | 2d1b5df0f753154a7efc3a01a36b932196cf6d1ff5ed24a5346236a8f1ba5bb9 |
| .agents/skills/security-best-practices/SKILL.md | UNKNOWN / UNKNOWN | 1663 | valid; 11 resources | {} | 2e52ba9dfd39bb0988ac01642177e0441aeedbcb1f5ca85e88ad3764cb6ac7c4 |
| .agents/skills/security-ownership-map/SKILL.md | UNKNOWN / UNKNOWN | 2083 | valid; 6 resources | {} | 7dc70ffb10bd9de513ad329d6acccccf3e262175affcf9f73e307bb7bc7449f7 |
| .agents/skills/security-research/SKILL.md | UNKNOWN / UNKNOWN | 588 | valid; 0 resources | {} | 82cf566002604da2d2ff4ea63b71ed6975171985009c2a8978207f26adad6ffd |
| .agents/skills/security-review/SKILL.md | 1.0.0 / domain | 1459 | valid; 0 resources | {"required_tools": "'[\"repo_search\",\"repo_dependency\",\"grep_search\",\"read_file\",\"security_scope\",\"security_assets\",\"security_sast\",\"security_dependencies\",\"security_threat_model\",\"security_validate_finding\",\"security_regression\"]'", "prerequisites": "'[\"explicit authorized scope (via `security_scope`)\",\"target surface"} | 558471609233989414617ab4195568ffe41d2f86fd6e9db0d867faab722a37a6 |
| .agents/skills/security-threat-model/SKILL.md | UNKNOWN / UNKNOWN | 1112 | valid; 3 resources | {} | 6f891ea91133e99a4391e5edf1fbdbde59a4445efaf43a85d3c61b35be0797de |
| .agents/skills/self-improvement/analyze-failure/SKILL.md | UNKNOWN / UNKNOWN | 579 | metadata harus berupa mapping string ke string. | {} | 05c16aa3a0336ffd1cbc01ff26fec6945623d8a6896e96b8018ea698eb07a795 |
| .agents/skills/self-improvement/benchmark-model/SKILL.md | UNKNOWN / UNKNOWN | 466 | metadata harus berupa mapping string ke string. | {} | 420bbe8a2c9061f11625458c6774fdb642afb669f03b3b43e8d5b47c5d094fa0 |
| .agents/skills/self-improvement/compare-models/SKILL.md | UNKNOWN / UNKNOWN | 369 | metadata harus berupa mapping string ke string. | {} | 1ac7b84d79899518ee02218015321fffa445a5d76c9337192221ca967a902ec9 |
| .agents/skills/self-improvement/evaluate-agent/SKILL.md | UNKNOWN / UNKNOWN | 557 | metadata harus berupa mapping string ke string. | {} | f346651079f7334019bbf1c0444d827110fd019a03171abb9fdb43dec5e377e7 |
| .agents/skills/self-improvement/experience-mining/SKILL.md | UNKNOWN / UNKNOWN | 482 | metadata harus berupa mapping string ke string. | {} | 5c22654451e6753d8efc47acb2764514ef180f8245480ed8f9f0b3f7da83a7f4 |
| .agents/skills/self-improvement/generate-training-data/SKILL.md | UNKNOWN / UNKNOWN | 504 | metadata harus berupa mapping string ke string. | {} | d29442cdfcfa28487d19cc3fd7e2735c3d81a06642b284ff303de6870b680439 |
| .agents/skills/self-improvement/memory-consolidation/SKILL.md | UNKNOWN / UNKNOWN | 474 | metadata harus berupa mapping string ke string. | {} | e134b0b1581c9931d818ae4469bdbd7c368f8149d924f9e0ef4bec4429354816 |
| .agents/skills/self-improvement/optimize-agent-policy/SKILL.md | UNKNOWN / UNKNOWN | 458 | metadata harus berupa mapping string ke string. | {} | 81ad1ede449a82695a25d6df8121c0f0cee680e5f057ea3488f4b6162501decc |
| .agents/skills/self-improvement/optimize-prompt/SKILL.md | UNKNOWN / UNKNOWN | 570 | metadata harus berupa mapping string ke string. | {} | c724892b249e184edceebd33247bce9e7cb9e62b3ba6591d170e6b51fd3919e2 |
| .agents/skills/self-improvement/optimize-rag/SKILL.md | UNKNOWN / UNKNOWN | 456 | metadata harus berupa mapping string ke string. | {} | 65f46fb1ae87b62b2c7f90763cd1a286187b2b52f39a958977bb8c05d9d90b73 |
| .agents/skills/self-improvement/optimize-tool-routing/SKILL.md | UNKNOWN / UNKNOWN | 437 | metadata harus berupa mapping string ke string. | {} | b6dbdad1b278e692650240260a7bb6b5964190ec20bec9b2d48826e4c07befab |
| .agents/skills/self-improvement/promote-model/SKILL.md | UNKNOWN / UNKNOWN | 415 | metadata harus berupa mapping string ke string. | {} | 7d7a221f8cabc35609ab074d90448de3eca85bc351284c2a4526f20fbe562edb |
| .agents/skills/self-improvement/reflect-trajectory/SKILL.md | UNKNOWN / UNKNOWN | 413 | metadata harus berupa mapping string ke string. | {} | 9322fb7e70195c8c51f01c5bd92621d5504bf981b81e8e464fdd23b2680df072 |
| .agents/skills/self-improvement/rollback-model/SKILL.md | UNKNOWN / UNKNOWN | 365 | metadata harus berupa mapping string ke string. | {} | a4d20b81ed662fbbeaf56dd60decee0a04a985a407a022d7a588566fd8c62505 |
| .agents/skills/self-improvement/run-dpo/SKILL.md | UNKNOWN / UNKNOWN | 423 | metadata harus berupa mapping string ke string. | {} | e438734237b91f978c045e29d008e9fc0a8efcd5c50340a09bab3345a73a2f38 |
| .agents/skills/self-improvement/run-grpo/SKILL.md | UNKNOWN / UNKNOWN | 425 | metadata harus berupa mapping string ke string. | {} | 0c8671dae1f95838cc03438e2c4c40f955046951038766265594e1bf66b60108 |
| .agents/skills/self-improvement/run-sft/SKILL.md | UNKNOWN / UNKNOWN | 472 | metadata harus berupa mapping string ke string. | {} | 7b61bbab613d1ffbc43d666163de8832c8f513391245b17bc17cd11f1e5b8f54 |
| .agents/skills/skill-creator/SKILL.md | UNKNOWN | 1538 | valid; 14 resources | UNKNOWN | 62b1fc3025c889361a258b719abee551fe1e62478e96155a3a6c7a8a0c5d1081 |
| .agents/skills/skill-improvement-opportunity-logger/SKILL.md | 1.0.0 / process | 1367 | valid; 0 resources | {"required_tools": "[\"lightning_record_action\",\"lightning_record_outcome\",\"lightning_episode_finish\",\"lightning_propose_improvement\",\"lightning_list_proposals\",\"skill_list\",\"skill_get\"]", "prerequisites": "[\"Lightning trace store has ≥ 1 episode for the relevant task type\",\"target skill name or tool surface is known\"]"} | 11492b62b6ee9378656f7029af5bdb3523ea6788b7a7ec2944958c62703d3498 |
| .agents/skills/skill-security-review/SKILL.md | 1.0.0 / governance | 2308 | valid; 0 resources | {"required_tools": "'[\"read_file\",\"grep_search\",\"glob_files\",\"skill_validate\",\"skill_list\",\"action_policy_evaluate\"]'", "prerequisites": "'[\"target SKILL.md path OR skill name in `.agents/skills/`\",\"read"} | 6a49956a987021f607ef78329e8411f3803ab49ce2357507ed20d374d39fee38 |
| .agents/skills/source-evaluation/SKILL.md | UNKNOWN / research | 1160 | valid; 0 resources | {} | 2fbd99894bdc75a244575e131f9b874ed0c6d6b0b352ceab5b941d4d7c4233c0 |
| .agents/skills/source-selector/SKILL.md | UNKNOWN / UNKNOWN | 762 | valid; 0 resources | {} | a785130364164de43c66477ed8f224dd53c4b4339548c1441b15eb9c3054f49d |
| .agents/skills/structured-project-execution/SKILL.md | 1.0.0 / harness | 1418 | valid; 0 resources | {"required_tools": "[\"repo_search\",\"write_file\",\"read_file\",\"todo_tool\",\"lightning_episode_start\",\"lightning_episode_finish\",\"lightning_record_action\",\"hitl_request_approval\"]", "prerequisites": "[\"target project / goal\",\"target branch / working directory\",\"approval status (auto vs HITL-gated)\"]"} | 5ae09343de69ba97fc987d7ce4ba0709544af57dc72781b11df2566123913f30 |
| .agents/skills/submission-readiness/SKILL.md | UNKNOWN / review | 387 | valid; 0 resources | {} | ff725129fc7f5fe6628b16c25d12e38579b29dd6effea48ec78bccbd95044b91 |
| .agents/skills/tableau-workbook-builder/SKILL.md | UNKNOWN / UNKNOWN | 2993 | valid; 0 resources | {} | 181c454b0aed5e4793060c69494e46d80ec29c4d7a51215a2cd7ca77f99d18d1 |
| .agents/skills/tdd-workflow/SKILL.md | 1.0.0 / engineering | 1264 | valid; 0 resources | {"required_tools": "[\"read_file\",\"write_file\",\"grep_search\",\"glob_files\",\"bash_run\",\"ruff_check\",\"pytest_run\"]", "prerequisites": "[\"failing regression test that reproduces the issue OR a written red-test for the new behavior\",\"project root + test runner known\",\"lint available (`ruff`)\"]"} | 95aa311c529cd9eda0d50522db0b8d43850ef221fd31f146b68993c11af63863 |
| .agents/skills/technical-content-writer/SKILL.md | UNKNOWN / writing | 411 | valid; 0 resources | {} | 43032b121aba05b1a1c4b260bdb9513d2310af01a0df457109c3b7fa5fe23e75 |
| .agents/skills/terminology-bank/SKILL.md | UNKNOWN / editing | 1144 | valid; 0 resources | {} | 58e192f1600fa36e1c63d7a2d8e80394140eef2d1afe2e094d32fdbf1c70ce89 |
| .agents/skills/todolife-budget-tracker/SKILL.md | UNKNOWN / UNKNOWN | 385 | valid; 0 resources | {} | 42a20995c53baa6af4139f57ebc373d057498b007756db0123381e68d9fd8ade |
| .agents/skills/todolife-core-tracker/SKILL.md | UNKNOWN / UNKNOWN | 388 | valid; 0 resources | {} | fb4e09159db1e7d4235355c82b87ee157ef2d1c8392bd8af0365472238106205 |
| .agents/skills/todolife-daily-planner/SKILL.md | UNKNOWN / UNKNOWN | 1951 | valid; 0 resources | {} | fba2728546ae84832b7f700e5f59577a7b0613bc37645025d834284790aa6a3f |
| .agents/skills/todolife-project-router/SKILL.md | UNKNOWN / UNKNOWN | 437 | valid; 0 resources | {} | 5d1932ae095acf90fe5088c1f9111301fd7bd22115f7643aecaf2a21cafcf5e0 |
| .agents/skills/todolife-schedule-auditor/SKILL.md | UNKNOWN / UNKNOWN | 624 | valid; 0 resources | {} | 0b59973f40a7416e6f3276e87a596c6c11f57fde7fb0ca306ff30adea936d66a |
| .agents/skills/transcribe/SKILL.md | UNKNOWN / UNKNOWN | 711 | valid; 5 resources | {} | 96adbbf92d3aa150af94bb492cc159b903ad519872412ed68adcd287b74d5087 |
| .agents/skills/xninetzy-academic-safety/SKILL.md | UNKNOWN / UNKNOWN | 167 | valid; 0 resources | {} | 96f4ccb1922421efd581fde5e6ad362848221045fa2908f3f7d98275f0a03a13 |
| .agents/skills/xninetzy-artifact-orchestrator/SKILL.md | UNKNOWN / UNKNOWN | 4770 | valid; 2 resources | {} | 4c059137a0f329f6a141ec92ad564271ade05543e25cadb34bf7519131066b2e |
| .agents/skills/xninetzy-assignment-orchestrator/SKILL.md | UNKNOWN / UNKNOWN | 2324 | valid; 2 resources | {} | 0d8f60558d89d55953725c48e0f49f48cd566134e3891cd3f988f6ff5b7871ed |
| .agents/skills/xninetzy-cyber-campus/SKILL.md | UNKNOWN / UNKNOWN | 332 | valid; 0 resources | {} | 8727fa4ef27cbf07d47b9b74f4b5552284a95a64c5b8b6e7c35cffeaf6ab69c2 |
| .agents/skills/xninetzy-deep-research/SKILL.md | UNKNOWN / UNKNOWN | 2950 | valid; 3 resources | {} | 309e1e4c9f9b9ba118b420a5d0f475f7ad3514dfa841a398b1c84cdac76e0565 |
| .agents/skills/xninetzy-hebat/SKILL.md | UNKNOWN / UNKNOWN | 206 | valid; 0 resources | {} | 64ef561eb8d342d2353927ff293facc98e5483c1c4114427f2ffaa7f08931c95 |
| .agents/skills/xninetzy-krs/SKILL.md | UNKNOWN / UNKNOWN | 1107 | valid; 0 resources | {} | 4e66af0dbbb6574413feac817232d18b2b529ae16c52477d64a47a5b8982381b |
| .agents/skills/xninetzy-learning-coach/SKILL.md | UNKNOWN / UNKNOWN | 2950 | valid; 3 resources | {} | 8eeb680bc0c0cd0cd82398056f416558ff92bc46d5b56e786964e189a279381d |
| .agents/skills/xninetzy-mcp-lightning/SKILL.md | UNKNOWN / UNKNOWN | 3118 | valid; 2 resources | {} | 09434f191a4243a790b53e0903c2ece94b7735432acb55e93d265ed1c45b10bf |
| .agents/skills/xninetzy-memory/SKILL.md | UNKNOWN / UNKNOWN | 2314 | valid; 3 resources | {} | 67f3d1c7e98e0595f5a60784b54ee02618cb7a23d558b30d9c7113df574ced2f |
| .agents/skills/xninetzy-obsidian-orchestra/SKILL.md | UNKNOWN / UNKNOWN | 740 | valid; 3 resources | {} | d6aef8eb83eaef01931bf7b9e8ad04c1ded48ae4f65ebf50aa5157d9785ef81a |
| .agents/skills/xninetzy-os/SKILL.md | UNKNOWN / UNKNOWN | 2540 | valid; 2 resources | {} | e970b659487fb645993877ffcfe667170d64a515c2c2151d3538059757223dd8 |
| .agents/skills/xninetzy-research-memory/SKILL.md | UNKNOWN / UNKNOWN | 2744 | valid; 2 resources | {} | 28c43f838498c66ee2a34efe8583120f057a625cfb57bd0633e4b87324357fee |
| .agents/skills/xninetzy-security-testing/SKILL.md | UNKNOWN / UNKNOWN | 8235 | valid; 2 resources | {} | 6865264159a3e39202908113351aeff5b5697b21d674b413a7b3105973025a61 |
| .agents/skills/xninetzy-uacc/SKILL.md | UNKNOWN / UNKNOWN | 2687 | valid; 2 resources | {} | c11f65fca46863d827faacb4fe941f541e153dc6afaafb13ab60164b8b28214a |
| .agents/skills/xninetzy-web-analysis/SKILL.md | UNKNOWN / UNKNOWN | 4695 | valid; 2 resources | {} | cd086b5e085cd074ab5ec66bbe7a4ed46907b09a3c4813ad812a8cad4b1846f7 |

## Installed skill identities

Each row identifies the inspected location, content and token size. This is an audit snapshot, not a source-of-truth registry override. Disabled backup entries are recorded separately from valid active candidates.

### codex

| Path | Name | Tokens | Syntax status | SHA-256 |
|---|---|---|---|---|
| /home/misbahul45/.codex/skills/.system/imagegen/SKILL.md | imagegen | 4230 | strict YAML + required fields valid | 681ddb4ad6d06a2acc78a3535b583f8d0c1ea800ecda3d56370d3310fd2cd4ba |
| /home/misbahul45/.codex/skills/.system/openai-docs/SKILL.md | openai-docs | 1109 | strict YAML + required fields valid | aa6829e21df2223167c85d2e49b6337a7345c84c1033f1ec10182c7882b36d45 |
| /home/misbahul45/.codex/skills/.system/review-agent/SKILL.md | review-agent | 553 | strict YAML + required fields valid | 07079efd0dc76f05fade424e5dfb048dce1de2df7626e1a4f56292a4f3f92228 |
| /home/misbahul45/.codex/skills/.system/skill-creator/SKILL.md | skill-creator | 2860 | strict YAML + required fields valid | 6656e54755638e8efcf275a472b9672eaa8a9a1b9e59dc210e275b03b59e1e66 |
| /home/misbahul45/.codex/skills/.system/skill-installer/SKILL.md | skill-installer | 762 | strict YAML + required fields valid | d68b77e5bbb34dedab89d134da52855f140fc4b4299b80104f534e3b9e98f8ee |
| /home/misbahul45/.codex/skills/academic-editor/SKILL.md | academic-editor | 388 | strict YAML + required fields valid | 635f73179fcbb3d6636bc1dc519695550e822e0875717ae50eb11582f9ac33ff |
| /home/misbahul45/.codex/skills/academic-writer/SKILL.md | academic-writer | 404 | strict YAML + required fields valid | 161a3dcd84f25ea63252764a3faa7c82c5e1c89556b9336fa217953d314aaa13 |
| /home/misbahul45/.codex/skills/anti-slop/SKILL.md | anti-slop | 426 | strict YAML + required fields valid | a5137a98751d747285cf8728ed7af6969eae676a1cea07009405e9ee5a841361 |
| /home/misbahul45/.codex/skills/api-security/SKILL.md | api-security | 5764 | strict YAML + required fields valid | 1203063191b9b69c04760429adb7a4c7f6f28cdb0f01c0a4c947c570f7d531c9 |
| /home/misbahul45/.codex/skills/architecture-analysis/SKILL.md | architecture-analysis | 5446 | strict YAML + required fields valid | 17244f125e7e9004004352d32c2282141aa2ba4c0db35085434ad149b5e69a62 |
| /home/misbahul45/.codex/skills/argument-coherence/SKILL.md | argument-coherence | 970 | strict YAML + required fields valid | c2c2eef4a2b1188e65f3fff3f5ae721e498d59be6641b4b06c20b965e226148a |
| /home/misbahul45/.codex/skills/benchmark-analysis/SKILL.md | benchmark-analysis | 539 | strict YAML + required fields valid | aca8329463885331581fbfc26face5d4b342e41c67d77cf8898a622a7c631b32 |
| /home/misbahul45/.codex/skills/business-writer/SKILL.md | business-writer | 398 | strict YAML + required fields valid | b09b31698d699599837beebc4c07382eca4f05f466ce9bffb5e31358d8215904 |
| /home/misbahul45/.codex/skills/career/alternative-titles/SKILL.md | alternative-titles | 288 | strict YAML + required fields valid | c2a60507cdd95a5aa4d196fbcbd70fb42b1a03dc270b9bba1a753d0baf12baf8 |
| /home/misbahul45/.codex/skills/career/application-tracking/SKILL.md | application-tracking | 314 | strict YAML + required fields valid | 07566e6753d4586d4a2626290228a21d6a03258e41a1d015239b0e60389121b1 |
| /home/misbahul45/.codex/skills/career/company-research/SKILL.md | company-research | 382 | strict YAML + required fields valid | e86e906d82b6376eb87c85ee3100f82ea5b163e0314719284773997c810fef91 |
| /home/misbahul45/.codex/skills/career/company-search/SKILL.md | company-search | 312 | strict YAML + required fields valid | f0012d6fffafd7d554d196b9506c121497c5d311c6f991e6bcadd809bb980354 |
| /home/misbahul45/.codex/skills/career/cv-analysis/SKILL.md | cv-analysis | 393 | strict YAML + required fields valid | 14b129e35c78b117f8722ae2e94f5d17912dc57bd353341ce299d6cde97a8edd |
| /home/misbahul45/.codex/skills/career/extract-requirements/SKILL.md | extract-requirements | 291 | strict YAML + required fields valid | cb57c75aa69097ef688bd913b923de16fa0dfb6ce576bf10fd45fec1176fd7b4 |
| /home/misbahul45/.codex/skills/career/hidden-jobs/SKILL.md | hidden-jobs | 325 | strict YAML + required fields valid | c0f91e7cf101e79dc44d46af004828bcf8e93801c58ba981e4d9c6ece3d2c91b |
| /home/misbahul45/.codex/skills/career/internship-discovery/SKILL.md | internship-discovery | 405 | strict YAML + required fields valid | 77f18c4d791b4aa5cf34e699486e1a4406782a4ba997fa3d4c690a041ce01699 |
| /home/misbahul45/.codex/skills/career/interview-prep/SKILL.md | interview-prep | 386 | ScannerError | 66485ca3ef5f7761c39f0123bf1cbc75ae605a8c01e87a8817682756510860bf |
| /home/misbahul45/.codex/skills/career/job-discovery/SKILL.md | job-discovery | 477 | strict YAML + required fields valid | cc29eaac41ca80ca92f85d6fb7124e2835a9194a75e29acd585cc0c286d4e701 |
| /home/misbahul45/.codex/skills/career/job-matching/SKILL.md | job-matching | 405 | strict YAML + required fields valid | b1549fdef652bae132d8cf55c139c744de5f1570c9f51ed36ef9a769fae408ed |
| /home/misbahul45/.codex/skills/career/job-monitoring/SKILL.md | job-monitoring | 344 | strict YAML + required fields valid | f3c2d90125b9682d7c9d17241bed4489ee8411b5f36efece629283a0dfa594e1 |
| /home/misbahul45/.codex/skills/career/job-risk-analysis/SKILL.md | job-risk-analysis | 372 | strict YAML + required fields valid | e02ab3bbdf7b58a216ba00322b445cb53759174de905179b929322f38de5a260 |
| /home/misbahul45/.codex/skills/career/job-search/SKILL.md | job-search | 438 | strict YAML + required fields valid | 719a1c086bef4702fe3738ce612d20282e4740e12da2db344652546526a50263 |
| /home/misbahul45/.codex/skills/career/market-skill-trend/SKILL.md | market-skill-trend | 408 | strict YAML + required fields valid | 65fdc6acdf13e80033f271d249383b27588b654d465b9518097c4bd25c50eb6a |
| /home/misbahul45/.codex/skills/career/resume-tailoring/SKILL.md | resume-tailoring | 374 | strict YAML + required fields valid | 68237fe3762724f959b8e33a0fc061d3901d6328603905ca8a76a7163fd47228 |
| /home/misbahul45/.codex/skills/career/salary-analysis/SKILL.md | salary-analysis | 386 | strict YAML + required fields valid | 927f1db77aa1174279fc4a486fcc1b951dc63dd7f0f05daf49fa9c47557292ef |
| /home/misbahul45/.codex/skills/career/similar-jobs/SKILL.md | similar-jobs | 302 | strict YAML + required fields valid | 9c1f579ef6130d492f2b91bf0b5fda2c3ceb43979fa3cd26601cff3041815627 |
| /home/misbahul45/.codex/skills/career/skill-gap/SKILL.md | skill-gap | 428 | strict YAML + required fields valid | 1d9477eab81534aae106d8af9bbd5461b9fbcaad3c006f1ef6cb5273631cccc7 |
| /home/misbahul45/.codex/skills/citation-validation/SKILL.md | citation-validation | 941 | strict YAML + required fields valid | 0af168b02c3e0ded78271854eb7c062b08751a5c1cf2718a53cee9b46c64ed6f |
| /home/misbahul45/.codex/skills/claim-lattice/SKILL.md | claim-lattice | 1544 | strict YAML + required fields valid | 8d73475d60e26163f8d6e07dd49fbd26ecacce1c0586dd61b590e5fc6f0cdec2 |
| /home/misbahul45/.codex/skills/cli-creator/SKILL.md | cli-creator | 7186 | strict YAML + required fields valid | f37263afb9a0c66d6d85e316fbf258e1e248965b10de1edfe6fe747b4ef3f249 |
| /home/misbahul45/.codex/skills/code-review/SKILL.md | code-review | 7082 | strict YAML + required fields valid | 0e5958e3571783a8cce19cef8a12df25c7db082d76cbf9cae5f59678ece446d0 |
| /home/misbahul45/.codex/skills/competition-proposal/SKILL.md | competition-proposal | 402 | strict YAML + required fields valid | 58cfa8fc400ffd527a52b364d04a4b607b1eb10e93a5bfb1f0bb172a9aafc3a4 |
| /home/misbahul45/.codex/skills/consultant-challenge/SKILL.md | consultant-challenge | 392 | strict YAML + required fields valid | 8257e6a72604473201a131081ce520661fe3a5fa65e67238fe9f650963472acd |
| /home/misbahul45/.codex/skills/consultant/SKILL.md | consultant | 417 | strict YAML + required fields valid | 38a1ec7e0f8b8d42307160bd4d9488f912dcf7c14c205f7ae1386631fea37604 |
| /home/misbahul45/.codex/skills/consulting-pptx-skill/SKILL.md | consulting-pptx-skill | 3232 | strict YAML + required fields valid | 973c838db1e44f364f6695ef86e8f90a74504aee1ba10914f96b0d1a84295a5b |
| /home/misbahul45/.codex/skills/consulting-pptx/SKILL.md | consulting-pptx | 1013 | strict YAML + required fields valid | 913fa711c0349746d5cb69f3f4bcfb16e53a8679e5fb3abecc952a0551904c05 |
| /home/misbahul45/.codex/skills/context-engineering/SKILL.md | context-engineering | 7177 | strict YAML + required fields valid | c1a810f0796bbfbefeba3b119a54f7581ccfdeb74a7c80eb256933528f8dfc92 |
| /home/misbahul45/.codex/skills/contradiction-hunter/SKILL.md | contradiction-hunter | 468 | strict YAML + required fields valid | 0675c5460eaf7233141035c55fd28f9962f648f75590e1da17a805c8c0cd2820 |
| /home/misbahul45/.codex/skills/cyber-campus/SKILL.md | cyber-campus | 5777 | strict YAML + required fields valid | 2f9baf88354828c1fabdc1c7fc1b052c3be60c1aed17b9a0dd02a25b9a95b287 |
| /home/misbahul45/.codex/skills/data-analysis/SKILL.md | data-analysis | 610 | strict YAML + required fields valid | 788437361517076801a2be07f4b059bf5d1bd21b6f2175b17153c2a32c71b1ac |
| /home/misbahul45/.codex/skills/debugging/SKILL.md | debugging | 6561 | strict YAML + required fields valid | 2d22d97f0e5d8b1c4e699582ac2f66cfdfe81b4bae6f79346ec9b3f4e4f8bea8 |
| /home/misbahul45/.codex/skills/define-goal/SKILL.md | define-goal | 7059 | strict YAML + required fields valid | 68531b47ba2806e2be94c76850516d413681981c9d9097092c5f94b6f13e3d60 |
| /home/misbahul45/.codex/skills/dependency-audit/SKILL.md | dependency-audit | 8361 | strict YAML + required fields valid | 24ae5c89d692de565643aa79f72e1723dafb627fe38ce301a95510700a763821 |
| /home/misbahul45/.codex/skills/evidence-grader/SKILL.md | evidence-grader | 463 | strict YAML + required fields valid | 02fdf8320773cfd6d05fb52e0aa9aa6b6a7e0a98370b152bb48a8e0a910a5394 |
| /home/misbahul45/.codex/skills/evidence-synthesis/SKILL.md | evidence-synthesis | 752 | strict YAML + required fields valid | 57e0f526fea50430d3faf7ff82b395837cd776c0403922473ac2e31c1ccaeb18 |
| /home/misbahul45/.codex/skills/exam_qa/SKILL.md | exam_qa | 435 | strict YAML + required fields valid | 4b73517232d23453550801daf41eff49ddd217512094a193344dffdd12b3199b |
| /home/misbahul45/.codex/skills/executive-writer/SKILL.md | executive-writer | 411 | strict YAML + required fields valid | 10b2aab99ef39184f446f8356508f6d5e584688e65642e727c2b0dea26411a12 |
| /home/misbahul45/.codex/skills/gh-fix-ci/SKILL.md | gh-fix-ci | 892 | strict YAML + required fields valid | 66ffd7fd69abc96527d8cde3920490eaff1b686ce29152ab97e0f577c47f11a6 |
| /home/misbahul45/.codex/skills/grant-proposal/SKILL.md | grant-proposal | 402 | strict YAML + required fields valid | 5b796c40ab5b92481bf2956d74bf58fb5e0bc206cb48d4cbb5cfca663b8e3eac |
| /home/misbahul45/.codex/skills/graph-rag/SKILL.md | graph-rag | 8913 | strict YAML + required fields valid | fd294179bdad92ad091af0a082add852b2d27186c413f3809e26c6dbe22b184a |
| /home/misbahul45/.codex/skills/hebat-academic/SKILL.md | hebat-academic | 4028 | strict YAML + required fields valid | b0d3c305b9e05cfebaf91fcb265bb0346a4e15f0a0a668a6ead6773e3d440ffd |
| /home/misbahul45/.codex/skills/hebat-assignment/SKILL.md | hebat-assignment | 5080 | strict YAML + required fields valid | de2b27b3fd35d7e334186d6700d6df13e9cfccf6523db1b2b1d8db167955ccaf |
| /home/misbahul45/.codex/skills/it-learning/SKILL.md | it-learning | 1534 | strict YAML + required fields valid | c24d46654a7742ed263102be08fdb3047d87a5d49a5ad407c081608a2039806b |
| /home/misbahul45/.codex/skills/jupyter-notebook/SKILL.md | jupyter-notebook | 934 | strict YAML + required fields valid | 735c09068509503cffd764e6d32be58e734cc9e7c6f14aab1c26c394c7d6c7d1 |
| /home/misbahul45/.codex/skills/life-management/SKILL.md | life-management | 1648 | strict YAML + required fields valid | 7bc57608409c31342cfc45808b23ba3f5454dabd147a082b100604326b59d8be |
| /home/misbahul45/.codex/skills/literature-review-writer/SKILL.md | literature-review-writer | 411 | strict YAML + required fields valid | f6e66ff67f10024908902aae063a44de4446cafeb7c8f1f641888702bcf5a083 |
| /home/misbahul45/.codex/skills/literature-review/SKILL.md | literature-review | 653 | strict YAML + required fields valid | 61b457849ad8f32c32ab71cac908a419db82efc68c6012550612ae22043d6abb |
| /home/misbahul45/.codex/skills/mcp-development/SKILL.md | mcp-development | 1848 | strict YAML + required fields valid | 26a3e1e376efd2012197f0322020bdf1f3acc3ad1f9a86688cf74c6622cb3601 |
| /home/misbahul45/.codex/skills/mcp-discovery/SKILL.md | mcp-discovery | 584 | strict YAML + required fields valid | b3c02d2151a328628fba78015d17142509d66fa50a663a4338694e604d0418fb |
| /home/misbahul45/.codex/skills/memory-chat/SKILL.md | memory-chat | 1753 | strict YAML + required fields valid | b7bbfabb0be019fbbc8ce5e7c078589725c47c3d6f540fd3a1ee27e2dda1cb1f |
| /home/misbahul45/.codex/skills/memory-management/SKILL.md | memory-management | 1552 | strict YAML + required fields valid | 620a86e9039bf2445b632b07a263698ba1dab2353c9610a2ffd024bc7dc27daf |
| /home/misbahul45/.codex/skills/methodology-rater/SKILL.md | methodology-rater | 1772 | strict YAML + required fields valid | b0f99aadd4f3d3346691824c99e78ebd55464d6da339b11480de3ff55afeda4e |
| /home/misbahul45/.codex/skills/multi-agent-orchestration/SKILL.md | multi-agent-orchestration | 1556 | strict YAML + required fields valid | 101ef2b7e5951f717ce19a15899b90a13e8da00b723578d3efe6a2065effdf7f |
| /home/misbahul45/.codex/skills/obsidian-knowledge/SKILL.md | obsidian-knowledge | 350 | strict YAML + required fields valid | a6b9c662d9c715b6958c8441001e10497647b876c964788dcbdafdab6a1f157d |
| /home/misbahul45/.codex/skills/obsidian-ops/SKILL.md | obsidian-ops | 417 | strict YAML + required fields valid | 4d50723d3ad14fdcebd4bda81f57964895f9d75a19ce229d5bd60c500f8cfd1f |
| /home/misbahul45/.codex/skills/outline-builder/SKILL.md | outline-builder | 1664 | strict YAML + required fields valid | 532830f1a9d223ca116ab84646251b9c355518b70702e9788c2abce9216236c0 |
| /home/misbahul45/.codex/skills/paper-analysis/SKILL.md | paper-analysis | 759 | strict YAML + required fields valid | 829c8cb275d335108ef7cec63ef2a035e254ddcec49ee2a9579ed3c82eb86277 |
| /home/misbahul45/.codex/skills/paper-review/SKILL.md | paper-review | 398 | strict YAML + required fields valid | e875f7550fba9a6d26bd788c0398a32b14edc87c3c15e2cf08787ca4895d6920 |
| /home/misbahul45/.codex/skills/pdf/SKILL.md | pdf | 3125 | strict YAML + required fields valid | 51cde8bdc880d44e9e13e629d618462be4563e4803219a2ed189ffe39635c3f2 |
| /home/misbahul45/.codex/skills/personal-os/SKILL.md | personal-os | 520 | strict YAML + required fields valid | 29a76589da05e4162a439ad14d45f32cb229ec9d7b17b2812fe192a08ac31571 |
| /home/misbahul45/.codex/skills/playwright-interactive/SKILL.md | playwright-interactive | 6801 | strict YAML + required fields valid | 2529dd902005f12c89b65aed648cd22af4d4e7ba7e991159f73e2db740c48ff5 |
| /home/misbahul45/.codex/skills/playwright-mcp-workflows/SKILL.md | playwright-mcp-workflows | 1116 | strict YAML + required fields valid | 66410f6a3a31664ba7d4318ada23a8632adffe79a67cce9b6d1e5d3e9e59ae0f |
| /home/misbahul45/.codex/skills/playwright/SKILL.md | playwright | 946 | strict YAML + required fields valid | d5693079440907bd2d8dde943ee096212dc276c90437512ce4ed802aa2b0f976 |
| /home/misbahul45/.codex/skills/pptx-skills/.claude/skills/markitdown/SKILL.md | markitdown | 1035 | strict YAML + required fields valid | cf2e206be8baf949216a70b321d8b124b9ca534d36cf6a10c1cc47c9a95749a9 |
| /home/misbahul45/.codex/skills/pptx-skills/.claude/skills/slide-analyze/SKILL.md | slide-analyze | 1399 | strict YAML + required fields valid | 32d4cdadce4d654673c07516b2f8d8cb979231840926d2cb495bc991c024d734 |
| /home/misbahul45/.codex/skills/pptx-skills/.claude/skills/slide-edit/SKILL.md | slide-edit | 1348 | strict YAML + required fields valid | b2847845e2819ff84a7c045ed07ee4c60aef73845166622592e79214b10bef6a |
| /home/misbahul45/.codex/skills/pptx-skills/.claude/skills/slide-generate/SKILL.md | slide-generate | 1724 | strict YAML + required fields valid | ad87f1a97a1645a0daa223358f79bdbfbb9c4dad0459cb04146fc34cf189143b |
| /home/misbahul45/.codex/skills/pptx-skills/SKILL.md | pptx-skills | 559 | strict YAML + required fields valid | 9ca9e518127ee10a6db771b51b3aa007f8a93230ee85e1626006b9e7126bb34d |
| /home/misbahul45/.codex/skills/process-engineering-providers/SKILL.md | process-engineering-providers | 685 | strict YAML + required fields valid | f512f27a4b69425ffd9b06e331a4e02c7aad05e62226aae057e2c1e5d7b750be |
| /home/misbahul45/.codex/skills/process_engineering/SKILL.md | process_engineering | 404 | strict YAML + required fields valid | 0ce5856b9c39cc200d95006c350f2d2b3e32af58a8a762057f8934439c18fe4b |
| /home/misbahul45/.codex/skills/professional-editor/SKILL.md | professional-editor | 412 | strict YAML + required fields valid | 91dadc5ef8e9dad1ea7b6c59cef392dc5d46d7a90fc21a85d1f9d2f759c3c7bc |
| /home/misbahul45/.codex/skills/professional-writer/SKILL.md | professional-writer | 518 | strict YAML + required fields valid | 0cef09ebe9890e2889f8f45abdb426ac589881f4568cde0e9931a740a3390c87 |
| /home/misbahul45/.codex/skills/proposal-red-team/SKILL.md | proposal-red-team | 401 | strict YAML + required fields valid | 5ecd43d84f83af62bca442f3a3257ec9c9e762f73d467df641d5461fbc147f88 |
| /home/misbahul45/.codex/skills/proposal-writer/SKILL.md | proposal-writer | 405 | strict YAML + required fields valid | f1c2cd635efbaecde5323f7d40fe5153a70eb12eb9fea52dad00871afedacd4d |
| /home/misbahul45/.codex/skills/reasoning-critic/SKILL.md | reasoning-critic | 448 | strict YAML + required fields valid | 996ce829eb0a203333b9a380be8619b3dc5072f9cad407c2a5cac53f719cd8b2 |
| /home/misbahul45/.codex/skills/reasoning-orchestrator/SKILL.md | reasoning-orchestrator | 853 | strict YAML + required fields valid | 9a3cc386c644131aba52d69da0061c3b307e2d9dd54097236208b7a50949d4e6 |
| /home/misbahul45/.codex/skills/reasoning-strategy-learner/SKILL.md | reasoning-strategy-learner | 399 | strict YAML + required fields valid | e0fd1c7a44c7ee5c13cb5d969f83e00a8ba1cb432e7ae5a27b379985e489fbb8 |
| /home/misbahul45/.codex/skills/regression-analysis/SKILL.md | regression-analysis | 511 | strict YAML + required fields valid | fcfceb0b2f2f7bd9fa285be712bbf66e6ebbdf08df4387dbe7d2cdd6642d1df6 |
| /home/misbahul45/.codex/skills/repo-context-packaging/SKILL.md | repo-context-packaging | 1363 | strict YAML + required fields valid | 9a3ed45936de1f4f5ad2538001df05142c96b39a2f1e9fedfb1dceb79cf8cd2d |
| /home/misbahul45/.codex/skills/requirement-coverage/SKILL.md | requirement-coverage | 830 | strict YAML + required fields valid | 449f78b8aa67903f106bb1aea1f80014cd2ae2aafe26c3fddbc94657d922dc95 |
| /home/misbahul45/.codex/skills/research-critic/SKILL.md | research-critic | 578 | strict YAML + required fields valid | a7d6bb1b788696de37ade981a008c3cbfd79c6c5384e5d20357ffbda074ef7fa |
| /home/misbahul45/.codex/skills/research-paper-writer/SKILL.md | research-paper-writer | 404 | strict YAML + required fields valid | e6b5af989654d9833aec12e8665e04332b2b61fd4f13ba8df36359bc1fa0f9bf |
| /home/misbahul45/.codex/skills/research-planner/SKILL.md | research-planner | 616 | strict YAML + required fields valid | e6888e8bf01b3643076263088752f32708337f65bc37ada73fc7fc2f54a9f542 |
| /home/misbahul45/.codex/skills/research-proposal/SKILL.md | research-proposal | 401 | strict YAML + required fields valid | 291ba454e45c1724c366884f1a9e5d482408276c1617ab551babeb052813b99e |
| /home/misbahul45/.codex/skills/research/SKILL.md | research | 2637 | strict YAML + required fields valid | 3d8afc8a7fd31151ba4c34aa94b127c0aea4b514ab923c95e66e4429c4cec7cf |
| /home/misbahul45/.codex/skills/reverse-engineer-anything/SKILL.md | reverse-engineer-anything | 5090 | strict YAML + required fields valid | fbcd39d6abe803cf7aa49c1880815bc8e22ba2af87a23681944f687bb7629eb1 |
| /home/misbahul45/.codex/skills/scientific-paper-writer/SKILL.md | scientific-paper-writer | 400 | strict YAML + required fields valid | bb7903316aca315ffc7bf2ce745e6323ce8dcc38d2ca274ea492499f444c9080 |
| /home/misbahul45/.codex/skills/scoring-rubric/SKILL.md | scoring-rubric | 1617 | strict YAML + required fields valid | c452e27b3f276b244604de9b4bd2f2690f214b06ee1da657601128004bb62eb8 |
| /home/misbahul45/.codex/skills/screenshot/SKILL.md | screenshot | 1915 | strict YAML + required fields valid | e54300fdc7c9c6a683263dabb4cf5a4967ec77d343faed439bc6586caea87c36 |
| /home/misbahul45/.codex/skills/secret-audit/SKILL.md | secret-audit | 637 | strict YAML + required fields valid | 2d1b5df0f753154a7efc3a01a36b932196cf6d1ff5ed24a5346236a8f1ba5bb9 |
| /home/misbahul45/.codex/skills/security-best-practices/SKILL.md | security-best-practices | 1663 | strict YAML + required fields valid | 2e52ba9dfd39bb0988ac01642177e0441aeedbcb1f5ca85e88ad3764cb6ac7c4 |
| /home/misbahul45/.codex/skills/security-ownership-map/SKILL.md | security-ownership-map | 2083 | strict YAML + required fields valid | 7dc70ffb10bd9de513ad329d6acccccf3e262175affcf9f73e307bb7bc7449f7 |
| /home/misbahul45/.codex/skills/security-research/SKILL.md | security-research | 588 | strict YAML + required fields valid | 82cf566002604da2d2ff4ea63b71ed6975171985009c2a8978207f26adad6ffd |
| /home/misbahul45/.codex/skills/security-review/SKILL.md | security-review | 1459 | strict YAML + required fields valid | 558471609233989414617ab4195568ffe41d2f86fd6e9db0d867faab722a37a6 |
| /home/misbahul45/.codex/skills/security-threat-model/SKILL.md | security-threat-model | 1112 | strict YAML + required fields valid | 6f891ea91133e99a4391e5edf1fbdbde59a4445efaf43a85d3c61b35be0797de |
| /home/misbahul45/.codex/skills/self-improvement/analyze-failure/SKILL.md | analyze-failure | 579 | strict YAML + required fields valid | 05c16aa3a0336ffd1cbc01ff26fec6945623d8a6896e96b8018ea698eb07a795 |
| /home/misbahul45/.codex/skills/self-improvement/benchmark-model/SKILL.md | benchmark-model | 466 | strict YAML + required fields valid | 420bbe8a2c9061f11625458c6774fdb642afb669f03b3b43e8d5b47c5d094fa0 |
| /home/misbahul45/.codex/skills/self-improvement/compare-models/SKILL.md | compare-models | 369 | strict YAML + required fields valid | 1ac7b84d79899518ee02218015321fffa445a5d76c9337192221ca967a902ec9 |
| /home/misbahul45/.codex/skills/self-improvement/evaluate-agent/SKILL.md | evaluate-agent | 557 | strict YAML + required fields valid | f346651079f7334019bbf1c0444d827110fd019a03171abb9fdb43dec5e377e7 |
| /home/misbahul45/.codex/skills/self-improvement/experience-mining/SKILL.md | experience-mining | 482 | strict YAML + required fields valid | 5c22654451e6753d8efc47acb2764514ef180f8245480ed8f9f0b3f7da83a7f4 |
| /home/misbahul45/.codex/skills/self-improvement/generate-training-data/SKILL.md | generate-training-data | 504 | strict YAML + required fields valid | d29442cdfcfa28487d19cc3fd7e2735c3d81a06642b284ff303de6870b680439 |
| /home/misbahul45/.codex/skills/self-improvement/memory-consolidation/SKILL.md | memory-consolidation | 474 | strict YAML + required fields valid | e134b0b1581c9931d818ae4469bdbd7c368f8149d924f9e0ef4bec4429354816 |
| /home/misbahul45/.codex/skills/self-improvement/optimize-agent-policy/SKILL.md | optimize-agent-policy | 458 | strict YAML + required fields valid | 81ad1ede449a82695a25d6df8121c0f0cee680e5f057ea3488f4b6162501decc |
| /home/misbahul45/.codex/skills/self-improvement/optimize-prompt/SKILL.md | optimize-prompt | 570 | strict YAML + required fields valid | c724892b249e184edceebd33247bce9e7cb9e62b3ba6591d170e6b51fd3919e2 |
| /home/misbahul45/.codex/skills/self-improvement/optimize-rag/SKILL.md | optimize-rag | 456 | strict YAML + required fields valid | 65f46fb1ae87b62b2c7f90763cd1a286187b2b52f39a958977bb8c05d9d90b73 |
| /home/misbahul45/.codex/skills/self-improvement/optimize-tool-routing/SKILL.md | optimize-tool-routing | 437 | strict YAML + required fields valid | b6dbdad1b278e692650240260a7bb6b5964190ec20bec9b2d48826e4c07befab |
| /home/misbahul45/.codex/skills/self-improvement/promote-model/SKILL.md | promote-model | 415 | strict YAML + required fields valid | 7d7a221f8cabc35609ab074d90448de3eca85bc351284c2a4526f20fbe562edb |
| /home/misbahul45/.codex/skills/self-improvement/reflect-trajectory/SKILL.md | reflect-trajectory | 413 | strict YAML + required fields valid | 9322fb7e70195c8c51f01c5bd92621d5504bf981b81e8e464fdd23b2680df072 |
| /home/misbahul45/.codex/skills/self-improvement/rollback-model/SKILL.md | rollback-model | 365 | strict YAML + required fields valid | a4d20b81ed662fbbeaf56dd60decee0a04a985a407a022d7a588566fd8c62505 |
| /home/misbahul45/.codex/skills/self-improvement/run-dpo/SKILL.md | run-dpo | 423 | strict YAML + required fields valid | e438734237b91f978c045e29d008e9fc0a8efcd5c50340a09bab3345a73a2f38 |
| /home/misbahul45/.codex/skills/self-improvement/run-grpo/SKILL.md | run-grpo | 425 | strict YAML + required fields valid | 0c8671dae1f95838cc03438e2c4c40f955046951038766265594e1bf66b60108 |
| /home/misbahul45/.codex/skills/self-improvement/run-sft/SKILL.md | run-sft | 472 | strict YAML + required fields valid | 7b61bbab613d1ffbc43d666163de8832c8f513391245b17bc17cd11f1e5b8f54 |
| /home/misbahul45/.codex/skills/skill-creator/SKILL.md | skill-creator | 1538 | strict YAML + required fields valid | 62b1fc3025c889361a258b719abee551fe1e62478e96155a3a6c7a8a0c5d1081 |
| /home/misbahul45/.codex/skills/skill-improvement-opportunity-logger/SKILL.md | skill-improvement-opportunity-logger | 1367 | strict YAML + required fields valid | 11492b62b6ee9378656f7029af5bdb3523ea6788b7a7ec2944958c62703d3498 |
| /home/misbahul45/.codex/skills/skill-security-review/SKILL.md | skill-security-review | 2308 | strict YAML + required fields valid | 6a49956a987021f607ef78329e8411f3803ab49ce2357507ed20d374d39fee38 |
| /home/misbahul45/.codex/skills/source-evaluation/SKILL.md | source-evaluation | 1160 | strict YAML + required fields valid | 2fbd99894bdc75a244575e131f9b874ed0c6d6b0b352ceab5b941d4d7c4233c0 |
| /home/misbahul45/.codex/skills/source-selector/SKILL.md | source-selector | 762 | strict YAML + required fields valid | a785130364164de43c66477ed8f224dd53c4b4339548c1441b15eb9c3054f49d |
| /home/misbahul45/.codex/skills/structured-project-execution/SKILL.md | structured-project-execution | 1418 | strict YAML + required fields valid | 5ae09343de69ba97fc987d7ce4ba0709544af57dc72781b11df2566123913f30 |
| /home/misbahul45/.codex/skills/submission-readiness/SKILL.md | submission-readiness | 387 | strict YAML + required fields valid | ff725129fc7f5fe6628b16c25d12e38579b29dd6effea48ec78bccbd95044b91 |
| /home/misbahul45/.codex/skills/tableau-workbook-builder/SKILL.md | tableau-workbook-builder | 2993 | strict YAML + required fields valid | 181c454b0aed5e4793060c69494e46d80ec29c4d7a51215a2cd7ca77f99d18d1 |
| /home/misbahul45/.codex/skills/tdd-workflow/SKILL.md | tdd-workflow | 1264 | strict YAML + required fields valid | 95aa311c529cd9eda0d50522db0b8d43850ef221fd31f146b68993c11af63863 |
| /home/misbahul45/.codex/skills/technical-content-writer/SKILL.md | technical-content-writer | 411 | strict YAML + required fields valid | 43032b121aba05b1a1c4b260bdb9513d2310af01a0df457109c3b7fa5fe23e75 |
| /home/misbahul45/.codex/skills/terminology-bank/SKILL.md | terminology-bank | 1144 | strict YAML + required fields valid | 58e192f1600fa36e1c63d7a2d8e80394140eef2d1afe2e094d32fdbf1c70ce89 |
| /home/misbahul45/.codex/skills/todolife-budget-tracker/SKILL.md | todolife-budget-tracker | 385 | strict YAML + required fields valid | 42a20995c53baa6af4139f57ebc373d057498b007756db0123381e68d9fd8ade |
| /home/misbahul45/.codex/skills/todolife-core-tracker/SKILL.md | todolife-core-tracker | 388 | strict YAML + required fields valid | fb4e09159db1e7d4235355c82b87ee157ef2d1c8392bd8af0365472238106205 |
| /home/misbahul45/.codex/skills/todolife-daily-planner/SKILL.md | todolife-daily-planner | 1951 | strict YAML + required fields valid | fba2728546ae84832b7f700e5f59577a7b0613bc37645025d834284790aa6a3f |
| /home/misbahul45/.codex/skills/todolife-project-router/SKILL.md | todolife-project-router | 437 | strict YAML + required fields valid | 5d1932ae095acf90fe5088c1f9111301fd7bd22115f7643aecaf2a21cafcf5e0 |
| /home/misbahul45/.codex/skills/todolife-schedule-auditor/SKILL.md | todolife-schedule-auditor | 624 | strict YAML + required fields valid | 0b59973f40a7416e6f3276e87a596c6c11f57fde7fb0ca306ff30adea936d66a |
| /home/misbahul45/.codex/skills/transcribe/SKILL.md | transcribe | 711 | strict YAML + required fields valid | 96adbbf92d3aa150af94bb492cc159b903ad519872412ed68adcd287b74d5087 |
| /home/misbahul45/.codex/skills/xninetzy-academic-safety/SKILL.md | xninetzy-academic-safety | 167 | strict YAML + required fields valid | 96f4ccb1922421efd581fde5e6ad362848221045fa2908f3f7d98275f0a03a13 |
| /home/misbahul45/.codex/skills/xninetzy-artifact-orchestrator/SKILL.md | xninetzy-artifact-orchestrator | 4770 | strict YAML + required fields valid | 4c059137a0f329f6a141ec92ad564271ade05543e25cadb34bf7519131066b2e |
| /home/misbahul45/.codex/skills/xninetzy-assignment-orchestrator/SKILL.md | xninetzy-assignment-orchestrator | 2324 | strict YAML + required fields valid | 0d8f60558d89d55953725c48e0f49f48cd566134e3891cd3f988f6ff5b7871ed |
| /home/misbahul45/.codex/skills/xninetzy-cyber-campus/SKILL.md | xninetzy-cyber-campus | 332 | strict YAML + required fields valid | 8727fa4ef27cbf07d47b9b74f4b5552284a95a64c5b8b6e7c35cffeaf6ab69c2 |
| /home/misbahul45/.codex/skills/xninetzy-deep-research/SKILL.md | xninetzy-deep-research | 2950 | strict YAML + required fields valid | 309e1e4c9f9b9ba118b420a5d0f475f7ad3514dfa841a398b1c84cdac76e0565 |
| /home/misbahul45/.codex/skills/xninetzy-hebat/SKILL.md | xninetzy-hebat | 206 | strict YAML + required fields valid | 64ef561eb8d342d2353927ff293facc98e5483c1c4114427f2ffaa7f08931c95 |
| /home/misbahul45/.codex/skills/xninetzy-krs/SKILL.md | xninetzy-krs | 1107 | strict YAML + required fields valid | 4e66af0dbbb6574413feac817232d18b2b529ae16c52477d64a47a5b8982381b |
| /home/misbahul45/.codex/skills/xninetzy-learning-coach/SKILL.md | xninetzy-learning-coach | 2950 | strict YAML + required fields valid | 8eeb680bc0c0cd0cd82398056f416558ff92bc46d5b56e786964e189a279381d |
| /home/misbahul45/.codex/skills/xninetzy-mcp-lightning/SKILL.md | xninetzy-mcp-lightning | 3118 | strict YAML + required fields valid | 09434f191a4243a790b53e0903c2ece94b7735432acb55e93d265ed1c45b10bf |
| /home/misbahul45/.codex/skills/xninetzy-memory/SKILL.md | xninetzy-memory | 2314 | strict YAML + required fields valid | 67f3d1c7e98e0595f5a60784b54ee02618cb7a23d558b30d9c7113df574ced2f |
| /home/misbahul45/.codex/skills/xninetzy-obsidian-orchestra/SKILL.md | xninetzy-obsidian-orchestra | 740 | strict YAML + required fields valid | d6aef8eb83eaef01931bf7b9e8ad04c1ded48ae4f65ebf50aa5157d9785ef81a |
| /home/misbahul45/.codex/skills/xninetzy-os/SKILL.md | xninetzy-os | 2540 | strict YAML + required fields valid | e970b659487fb645993877ffcfe667170d64a515c2c2151d3538059757223dd8 |
| /home/misbahul45/.codex/skills/xninetzy-research-memory/SKILL.md | xninetzy-research-memory | 2744 | strict YAML + required fields valid | 28c43f838498c66ee2a34efe8583120f057a625cfb57bd0633e4b87324357fee |
| /home/misbahul45/.codex/skills/xninetzy-security-testing/SKILL.md | xninetzy-security-testing | 8235 | strict YAML + required fields valid | 6865264159a3e39202908113351aeff5b5697b21d674b413a7b3105973025a61 |
| /home/misbahul45/.codex/skills/xninetzy-uacc/SKILL.md | xninetzy-uacc | 2687 | strict YAML + required fields valid | c11f65fca46863d827faacb4fe941f541e153dc6afaafb13ab60164b8b28214a |
| /home/misbahul45/.codex/skills/xninetzy-web-analysis/SKILL.md | xninetzy-web-analysis | 4695 | strict YAML + required fields valid | cd086b5e085cd074ab5ec66bbe7a4ed46907b09a3c4813ad812a8cad4b1846f7 |
### claude

| Path | Name | Tokens | Syntax status | SHA-256 |
|---|---|---|---|---|
| /home/misbahul45/.claude/skills/academic-editor/SKILL.md | academic-editor | 388 | strict YAML + required fields valid | 635f73179fcbb3d6636bc1dc519695550e822e0875717ae50eb11582f9ac33ff |
| /home/misbahul45/.claude/skills/academic-writer/SKILL.md | academic-writer | 404 | strict YAML + required fields valid | 161a3dcd84f25ea63252764a3faa7c82c5e1c89556b9336fa217953d314aaa13 |
| /home/misbahul45/.claude/skills/anti-slop/SKILL.md | anti-slop | 426 | strict YAML + required fields valid | a5137a98751d747285cf8728ed7af6969eae676a1cea07009405e9ee5a841361 |
| /home/misbahul45/.claude/skills/api-security/SKILL.md | api-security | 5764 | strict YAML + required fields valid | 1203063191b9b69c04760429adb7a4c7f6f28cdb0f01c0a4c947c570f7d531c9 |
| /home/misbahul45/.claude/skills/architecture-analysis/SKILL.md | architecture-analysis | 5446 | strict YAML + required fields valid | 17244f125e7e9004004352d32c2282141aa2ba4c0db35085434ad149b5e69a62 |
| /home/misbahul45/.claude/skills/argument-coherence/SKILL.md | argument-coherence | 970 | strict YAML + required fields valid | c2c2eef4a2b1188e65f3fff3f5ae721e498d59be6641b4b06c20b965e226148a |
| /home/misbahul45/.claude/skills/arkcli-agent/SKILL.md | arkcli-agent | 2925 | strict YAML + required fields valid | 61d4f8a8d4972d7aad0077e23da95e85e4aa64e23d8ca8477f4f9341fe29268a |
| /home/misbahul45/.claude/skills/arkcli-api-explorer/SKILL.md | arkcli-api-explorer | 1650 | strict YAML + required fields valid | f98c55d64c6537e9d685ddb3f2cba8693e6f4a616e04350a0e94bb075fbf2f07 |
| /home/misbahul45/.claude/skills/arkcli-auth/SKILL.md | arkcli-auth | 1361 | strict YAML + required fields valid | 55438901d16b9db7602d6746a05a8ce93a68ad62f4217758bea79a4fd573e91b |
| /home/misbahul45/.claude/skills/arkcli-billing/SKILL.md | arkcli-billing | 2680 | strict YAML + required fields valid | 2a22e741820ae9922bc3147da2b246ee446ae80e798b0f3fbfab5d1086af3e58 |
| /home/misbahul45/.claude/skills/arkcli-chat/SKILL.md | arkcli-chat | 2690 | strict YAML + required fields valid | c2623a814f8d7c0dc056dc27e85a8ff60049bbe6284cf21797efe8d48d655f3a |
| /home/misbahul45/.claude/skills/arkcli-config/SKILL.md | arkcli-config | 2245 | strict YAML + required fields valid | c7a0a208cd313cf2685764d3d5fbacc8795aca36550dc5080c8d0fd710fc999a |
| /home/misbahul45/.claude/skills/arkcli-connect/SKILL.md | arkcli-connect | 1841 | strict YAML + required fields valid | fc22cc62593486e43fd5ad668ee82220a579a065151db2ec451b917bed3310f7 |
| /home/misbahul45/.claude/skills/arkcli-custommodel/SKILL.md | arkcli-custommodel | 3587 | strict YAML + required fields valid | a3bc4baae305022e278467fae8c981959a8ee3bb9f674318fd0cef91e9514deb |
| /home/misbahul45/.claude/skills/arkcli-datasets/SKILL.md | arkcli-datasets | 859 | strict YAML + required fields valid | e26a6e0436177ec39c0a7a566723f7c8955027caf430e84ba56677fbca958ce9 |
| /home/misbahul45/.claude/skills/arkcli-deploy/SKILL.md | arkcli-deploy | 2211 | strict YAML + required fields valid | 4676351726365e842b64f5a24029bbc1da1752dfd54a2775844bcf9972cf1de0 |
| /home/misbahul45/.claude/skills/arkcli-doctor/SKILL.md | arkcli-doctor | 4433 | strict YAML + required fields valid | 3ed1b518572e8b8d81e85da3c7907967fae305d835a1eeff496ae0bc19203947 |
| /home/misbahul45/.claude/skills/arkcli-gen/SKILL.md | arkcli-gen | 3886 | strict YAML + required fields valid | 7289c636e853ddfa4fcab508375cdb3fa85eebca0e26913bc4b676ac316eb596 |
| /home/misbahul45/.claude/skills/arkcli-helper/SKILL.md | arkcli-helper | 1903 | strict YAML + required fields valid | d03683009a249395a5aacf3c2bcf04f062deedfe28ad9abd9279f423688b1e46 |
| /home/misbahul45/.claude/skills/arkcli-iam/SKILL.md | arkcli-iam | 601 | strict YAML + required fields valid | ed15bc290bd35c3dd5ef6495a2f5c7b1fe50515b420847772f175042cd7f8dbe |
| /home/misbahul45/.claude/skills/arkcli-infer-endpoint/SKILL.md | arkcli-infer-endpoint | 1607 | strict YAML + required fields valid | a42376322e5693ee1c926d9210b685ab75d97b1678474415c1e6956d2e3bd326 |
| /home/misbahul45/.claude/skills/arkcli-models/SKILL.md | arkcli-models | 5578 | strict YAML + required fields valid | 93b56da3c0a2ec86eba6b6f7b1cd1ab9ce590c3a6277e556cae18be7e36c39b1 |
| /home/misbahul45/.claude/skills/arkcli-onboard/SKILL.md | arkcli-onboard | 1513 | strict YAML + required fields valid | ec065aee469d6eadb19629d891646dd6c8a11ae2056e912abde9a5f1b4730115 |
| /home/misbahul45/.claude/skills/arkcli-plans/SKILL.md | arkcli-plans | 3103 | strict YAML + required fields valid | feafb57f9aacefc5aab98e311f22a36cfa86122379c7d3424a4deac4d7a614ed |
| /home/misbahul45/.claude/skills/arkcli-pricing/SKILL.md | arkcli-pricing | 2581 | strict YAML + required fields valid | d1277394760cbe9d0d0dca55ea7a348b4705c89bf75aa5aa8dcd1d54607c77bb |
| /home/misbahul45/.claude/skills/arkcli-profile/SKILL.md | arkcli-profile | 1260 | strict YAML + required fields valid | 12cea1aca8978ce65702570b4cd55c3be7e972ffe6d8555440f442d5ab3a3063 |
| /home/misbahul45/.claude/skills/arkcli-resources/SKILL.md | arkcli-resources | 2120 | strict YAML + required fields valid | b774ff8d80e38b03c45b5288166ae852487bccfb4d9c6060d263d0ba10c8af27 |
| /home/misbahul45/.claude/skills/arkcli-shared/SKILL.md | arkcli-shared | 1870 | strict YAML + required fields valid | de4b74c46feedbd2c15908357bc034ff920b42fce95a87da8a566552d9e1a45c |
| /home/misbahul45/.claude/skills/arkcli-train-finetune/SKILL.md | arkcli-train-finetune | 2216 | strict YAML + required fields valid | c21fa94d7ca09e4093eee9c93fdac894da22c6c9806db4dbc0a2e68f6ed572db |
| /home/misbahul45/.claude/skills/arkcli-understand/SKILL.md | arkcli-understand | 2544 | strict YAML + required fields valid | bfdd2f1aea38096421e82b71b4cea42e591b315f0675eedcf755768cdd046ea1 |
| /home/misbahul45/.claude/skills/arkcli-usage/SKILL.md | arkcli-usage | 3112 | strict YAML + required fields valid | e5803a26c0762d4d8ef2ddc055015fe502b1a417c4640d3f0e6abc924b15a0b8 |
| /home/misbahul45/.claude/skills/benchmark-analysis/SKILL.md | benchmark-analysis | 539 | strict YAML + required fields valid | aca8329463885331581fbfc26face5d4b342e41c67d77cf8898a622a7c631b32 |
| /home/misbahul45/.claude/skills/business-writer/SKILL.md | business-writer | 398 | strict YAML + required fields valid | b09b31698d699599837beebc4c07382eca4f05f466ce9bffb5e31358d8215904 |
| /home/misbahul45/.claude/skills/career/alternative-titles/SKILL.md | alternative-titles | 288 | strict YAML + required fields valid | c2a60507cdd95a5aa4d196fbcbd70fb42b1a03dc270b9bba1a753d0baf12baf8 |
| /home/misbahul45/.claude/skills/career/application-tracking/SKILL.md | application-tracking | 314 | strict YAML + required fields valid | 07566e6753d4586d4a2626290228a21d6a03258e41a1d015239b0e60389121b1 |
| /home/misbahul45/.claude/skills/career/company-research/SKILL.md | company-research | 382 | strict YAML + required fields valid | e86e906d82b6376eb87c85ee3100f82ea5b163e0314719284773997c810fef91 |
| /home/misbahul45/.claude/skills/career/company-search/SKILL.md | company-search | 312 | strict YAML + required fields valid | f0012d6fffafd7d554d196b9506c121497c5d311c6f991e6bcadd809bb980354 |
| /home/misbahul45/.claude/skills/career/cv-analysis/SKILL.md | cv-analysis | 393 | strict YAML + required fields valid | 14b129e35c78b117f8722ae2e94f5d17912dc57bd353341ce299d6cde97a8edd |
| /home/misbahul45/.claude/skills/career/extract-requirements/SKILL.md | extract-requirements | 291 | strict YAML + required fields valid | cb57c75aa69097ef688bd913b923de16fa0dfb6ce576bf10fd45fec1176fd7b4 |
| /home/misbahul45/.claude/skills/career/hidden-jobs/SKILL.md | hidden-jobs | 325 | strict YAML + required fields valid | c0f91e7cf101e79dc44d46af004828bcf8e93801c58ba981e4d9c6ece3d2c91b |
| /home/misbahul45/.claude/skills/career/internship-discovery/SKILL.md | internship-discovery | 405 | strict YAML + required fields valid | 77f18c4d791b4aa5cf34e699486e1a4406782a4ba997fa3d4c690a041ce01699 |
| /home/misbahul45/.claude/skills/career/interview-prep/SKILL.md | interview-prep | 386 | ScannerError | 66485ca3ef5f7761c39f0123bf1cbc75ae605a8c01e87a8817682756510860bf |
| /home/misbahul45/.claude/skills/career/job-discovery/SKILL.md | job-discovery | 477 | strict YAML + required fields valid | cc29eaac41ca80ca92f85d6fb7124e2835a9194a75e29acd585cc0c286d4e701 |
| /home/misbahul45/.claude/skills/career/job-matching/SKILL.md | job-matching | 405 | strict YAML + required fields valid | b1549fdef652bae132d8cf55c139c744de5f1570c9f51ed36ef9a769fae408ed |
| /home/misbahul45/.claude/skills/career/job-monitoring/SKILL.md | job-monitoring | 344 | strict YAML + required fields valid | f3c2d90125b9682d7c9d17241bed4489ee8411b5f36efece629283a0dfa594e1 |
| /home/misbahul45/.claude/skills/career/job-risk-analysis/SKILL.md | job-risk-analysis | 372 | strict YAML + required fields valid | e02ab3bbdf7b58a216ba00322b445cb53759174de905179b929322f38de5a260 |
| /home/misbahul45/.claude/skills/career/job-search/SKILL.md | job-search | 438 | strict YAML + required fields valid | 719a1c086bef4702fe3738ce612d20282e4740e12da2db344652546526a50263 |
| /home/misbahul45/.claude/skills/career/market-skill-trend/SKILL.md | market-skill-trend | 408 | strict YAML + required fields valid | 65fdc6acdf13e80033f271d249383b27588b654d465b9518097c4bd25c50eb6a |
| /home/misbahul45/.claude/skills/career/resume-tailoring/SKILL.md | resume-tailoring | 374 | strict YAML + required fields valid | 68237fe3762724f959b8e33a0fc061d3901d6328603905ca8a76a7163fd47228 |
| /home/misbahul45/.claude/skills/career/salary-analysis/SKILL.md | salary-analysis | 386 | strict YAML + required fields valid | 927f1db77aa1174279fc4a486fcc1b951dc63dd7f0f05daf49fa9c47557292ef |
| /home/misbahul45/.claude/skills/career/similar-jobs/SKILL.md | similar-jobs | 302 | strict YAML + required fields valid | 9c1f579ef6130d492f2b91bf0b5fda2c3ceb43979fa3cd26601cff3041815627 |
| /home/misbahul45/.claude/skills/career/skill-gap/SKILL.md | skill-gap | 428 | strict YAML + required fields valid | 1d9477eab81534aae106d8af9bbd5461b9fbcaad3c006f1ef6cb5273631cccc7 |
| /home/misbahul45/.claude/skills/citation-validation/SKILL.md | citation-validation | 941 | strict YAML + required fields valid | 0af168b02c3e0ded78271854eb7c062b08751a5c1cf2718a53cee9b46c64ed6f |
| /home/misbahul45/.claude/skills/claim-lattice/SKILL.md | claim-lattice | 1544 | strict YAML + required fields valid | 8d73475d60e26163f8d6e07dd49fbd26ecacce1c0586dd61b590e5fc6f0cdec2 |
| /home/misbahul45/.claude/skills/cli-creator/SKILL.md | cli-creator | 7186 | strict YAML + required fields valid | f37263afb9a0c66d6d85e316fbf258e1e248965b10de1edfe6fe747b4ef3f249 |
| /home/misbahul45/.claude/skills/code-review/SKILL.md | code-review | 7082 | strict YAML + required fields valid | 0e5958e3571783a8cce19cef8a12df25c7db082d76cbf9cae5f59678ece446d0 |
| /home/misbahul45/.claude/skills/competition-proposal/SKILL.md | competition-proposal | 402 | strict YAML + required fields valid | 58cfa8fc400ffd527a52b364d04a4b607b1eb10e93a5bfb1f0bb172a9aafc3a4 |
| /home/misbahul45/.claude/skills/consultant-challenge/SKILL.md | consultant-challenge | 392 | strict YAML + required fields valid | 8257e6a72604473201a131081ce520661fe3a5fa65e67238fe9f650963472acd |
| /home/misbahul45/.claude/skills/consultant/SKILL.md | consultant | 417 | strict YAML + required fields valid | 38a1ec7e0f8b8d42307160bd4d9488f912dcf7c14c205f7ae1386631fea37604 |
| /home/misbahul45/.claude/skills/consulting-pptx-skill/SKILL.md | consulting-pptx-skill | 3232 | strict YAML + required fields valid | 973c838db1e44f364f6695ef86e8f90a74504aee1ba10914f96b0d1a84295a5b |
| /home/misbahul45/.claude/skills/consulting-pptx/SKILL.md | consulting-pptx | 1013 | strict YAML + required fields valid | 913fa711c0349746d5cb69f3f4bcfb16e53a8679e5fb3abecc952a0551904c05 |
| /home/misbahul45/.claude/skills/context-engineering/SKILL.md | context-engineering | 7177 | strict YAML + required fields valid | c1a810f0796bbfbefeba3b119a54f7581ccfdeb74a7c80eb256933528f8dfc92 |
| /home/misbahul45/.claude/skills/contradiction-hunter/SKILL.md | contradiction-hunter | 468 | strict YAML + required fields valid | 0675c5460eaf7233141035c55fd28f9962f648f75590e1da17a805c8c0cd2820 |
| /home/misbahul45/.claude/skills/cyber-campus/SKILL.md | cyber-campus | 5777 | strict YAML + required fields valid | 2f9baf88354828c1fabdc1c7fc1b052c3be60c1aed17b9a0dd02a25b9a95b287 |
| /home/misbahul45/.claude/skills/data-analysis/SKILL.md | data-analysis | 610 | strict YAML + required fields valid | 788437361517076801a2be07f4b059bf5d1bd21b6f2175b17153c2a32c71b1ac |
| /home/misbahul45/.claude/skills/debugging/SKILL.md | debugging | 6561 | strict YAML + required fields valid | 2d22d97f0e5d8b1c4e699582ac2f66cfdfe81b4bae6f79346ec9b3f4e4f8bea8 |
| /home/misbahul45/.claude/skills/define-goal/SKILL.md | define-goal | 7059 | strict YAML + required fields valid | 68531b47ba2806e2be94c76850516d413681981c9d9097092c5f94b6f13e3d60 |
| /home/misbahul45/.claude/skills/dependency-audit/SKILL.md | dependency-audit | 8361 | strict YAML + required fields valid | 24ae5c89d692de565643aa79f72e1723dafb627fe38ce301a95510700a763821 |
| /home/misbahul45/.claude/skills/doc-coauthoring/SKILL.md | doc-coauthoring | 3289 | strict YAML + required fields valid | 2e47d78846faeea4a56e9809c52700087a15a2155a3f293a3efbaded81398ef4 |
| /home/misbahul45/.claude/skills/docx/SKILL.md | docx | 1773 | strict YAML + required fields valid | 8017469ea95fb7d28225c62daf8e2f3492a7b516fc64c18c28977cbf8980b7fe |
| /home/misbahul45/.claude/skills/evidence-grader/SKILL.md | evidence-grader | 463 | strict YAML + required fields valid | 02fdf8320773cfd6d05fb52e0aa9aa6b6a7e0a98370b152bb48a8e0a910a5394 |
| /home/misbahul45/.claude/skills/evidence-synthesis/SKILL.md | evidence-synthesis | 752 | strict YAML + required fields valid | 57e0f526fea50430d3faf7ff82b395837cd776c0403922473ac2e31c1ccaeb18 |
| /home/misbahul45/.claude/skills/exam_qa/SKILL.md | exam_qa | 435 | strict YAML + required fields valid | 4b73517232d23453550801daf41eff49ddd217512094a193344dffdd12b3199b |
| /home/misbahul45/.claude/skills/executive-writer/SKILL.md | executive-writer | 411 | strict YAML + required fields valid | 10b2aab99ef39184f446f8356508f6d5e584688e65642e727c2b0dea26411a12 |
| /home/misbahul45/.claude/skills/find-skills/SKILL.md | find-skills | 1291 | strict YAML + required fields valid | c00eeea0e13e74fe4a9d84ba0a8542205a1b736d65f13134fe1a6647eb14976f |
| /home/misbahul45/.claude/skills/frontend-design/SKILL.md | frontend-design | 1924 | strict YAML + required fields valid | d91970639e9f5c37682ac7ab60094d35f1c7c1f38d731bd56396563aee10c1d3 |
| /home/misbahul45/.claude/skills/gh-fix-ci/SKILL.md | gh-fix-ci | 892 | strict YAML + required fields valid | 66ffd7fd69abc96527d8cde3920490eaff1b686ce29152ab97e0f577c47f11a6 |
| /home/misbahul45/.claude/skills/google-agents-cli-adk-code/SKILL.md | google-agents-cli-adk-code | 748 | strict YAML + required fields valid | 744a359d57ccaa68a7b48bfc2f0b773de84bb5bcac0af07ce28a46b6d6c61832 |
| /home/misbahul45/.claude/skills/google-agents-cli-deploy/SKILL.md | google-agents-cli-deploy | 5498 | strict YAML + required fields valid | 7823ac5dfbca07b7e123d81eeded289b207a7bc2b903de94fb238b432c62d789 |
| /home/misbahul45/.claude/skills/google-agents-cli-eval/SKILL.md | google-agents-cli-eval | 6173 | strict YAML + required fields valid | 8427a75ec62eb174042cd297623f7d79f0e31fc8e84510efc2854ab58e33f5e4 |
| /home/misbahul45/.claude/skills/google-agents-cli-observability/SKILL.md | google-agents-cli-observability | 2277 | strict YAML + required fields valid | 47c688d8a645f2ca2d82fd7d842dcca53051ea3726f55ed300a025395a351105 |
| /home/misbahul45/.claude/skills/google-agents-cli-publish/SKILL.md | google-agents-cli-publish | 2231 | strict YAML + required fields valid | e3096f10bbeb696a97ddb9210ebfd3f21bfcf18706302fee919c7ff629c29cc3 |
| /home/misbahul45/.claude/skills/google-agents-cli-scaffold/SKILL.md | google-agents-cli-scaffold | 2671 | strict YAML + required fields valid | faf87b632abda32c250a0521cb2222e61579749ff1aae291cc72c9bee4a60866 |
| /home/misbahul45/.claude/skills/google-agents-cli-workflow/SKILL.md | google-agents-cli-workflow | 5250 | strict YAML + required fields valid | 32daccab4e0aeb49fd628b9bca1dcb167207f7d2649b8ae78fd0e19a85d69a22 |
| /home/misbahul45/.claude/skills/grant-proposal/SKILL.md | grant-proposal | 402 | strict YAML + required fields valid | 5b796c40ab5b92481bf2956d74bf58fb5e0bc206cb48d4cbb5cfca663b8e3eac |
| /home/misbahul45/.claude/skills/graph-rag/SKILL.md | graph-rag | 8913 | strict YAML + required fields valid | fd294179bdad92ad091af0a082add852b2d27186c413f3809e26c6dbe22b184a |
| /home/misbahul45/.claude/skills/hebat-academic/SKILL.md | hebat-academic | 4028 | strict YAML + required fields valid | b0d3c305b9e05cfebaf91fcb265bb0346a4e15f0a0a668a6ead6773e3d440ffd |
| /home/misbahul45/.claude/skills/hebat-assignment/SKILL.md | hebat-assignment | 5080 | strict YAML + required fields valid | de2b27b3fd35d7e334186d6700d6df13e9cfccf6523db1b2b1d8db167955ccaf |
| /home/misbahul45/.claude/skills/it-learning/SKILL.md | it-learning | 1534 | strict YAML + required fields valid | c24d46654a7742ed263102be08fdb3047d87a5d49a5ad407c081608a2039806b |
| /home/misbahul45/.claude/skills/jupyter-notebook/SKILL.md | jupyter-notebook | 934 | strict YAML + required fields valid | 735c09068509503cffd764e6d32be58e734cc9e7c6f14aab1c26c394c7d6c7d1 |
| /home/misbahul45/.claude/skills/life-management/SKILL.md | life-management | 1648 | strict YAML + required fields valid | 7bc57608409c31342cfc45808b23ba3f5454dabd147a082b100604326b59d8be |
| /home/misbahul45/.claude/skills/literature-review-writer/SKILL.md | literature-review-writer | 411 | strict YAML + required fields valid | f6e66ff67f10024908902aae063a44de4446cafeb7c8f1f641888702bcf5a083 |
| /home/misbahul45/.claude/skills/literature-review/SKILL.md | literature-review | 653 | strict YAML + required fields valid | 61b457849ad8f32c32ab71cac908a419db82efc68c6012550612ae22043d6abb |
| /home/misbahul45/.claude/skills/mcp-builder/SKILL.md | mcp-builder | 1922 | strict YAML + required fields valid | 0f4592dcb53cf2b5d6b7febee6b4152018b565551a1c29e3c612f57b218ab295 |
| /home/misbahul45/.claude/skills/mcp-development/SKILL.md | mcp-development | 1848 | strict YAML + required fields valid | 26a3e1e376efd2012197f0322020bdf1f3acc3ad1f9a86688cf74c6622cb3601 |
| /home/misbahul45/.claude/skills/mcp-discovery/SKILL.md | mcp-discovery | 584 | strict YAML + required fields valid | b3c02d2151a328628fba78015d17142509d66fa50a663a4338694e604d0418fb |
| /home/misbahul45/.claude/skills/memory-chat/SKILL.md | memory-chat | 1753 | strict YAML + required fields valid | b7bbfabb0be019fbbc8ce5e7c078589725c47c3d6f540fd3a1ee27e2dda1cb1f |
| /home/misbahul45/.claude/skills/memory-management/SKILL.md | memory-management | 1552 | strict YAML + required fields valid | 620a86e9039bf2445b632b07a263698ba1dab2353c9610a2ffd024bc7dc27daf |
| /home/misbahul45/.claude/skills/methodology-rater/SKILL.md | methodology-rater | 1772 | strict YAML + required fields valid | b0f99aadd4f3d3346691824c99e78ebd55464d6da339b11480de3ff55afeda4e |
| /home/misbahul45/.claude/skills/mmx-cli/SKILL.md | mmx-cli | 2839 | strict YAML + required fields valid | 1adee4231e1c37cc0d09bd890cebacc1d62a6a69f059cb78fd5654480b8a0ee2 |
| /home/misbahul45/.claude/skills/mmx-cli/h3-video/SKILL.md | mmx-h3-video | 2410 | strict YAML + required fields valid | 5ddf4209eb4cdcf6b88a011285bbfc7e470d544856b53d27269524bc6390c5a1 |
| /home/misbahul45/.claude/skills/multi-agent-orchestration/SKILL.md | multi-agent-orchestration | 1556 | strict YAML + required fields valid | 101ef2b7e5951f717ce19a15899b90a13e8da00b723578d3efe6a2065effdf7f |
| /home/misbahul45/.claude/skills/obsidian-knowledge/SKILL.md | obsidian-knowledge | 350 | strict YAML + required fields valid | a6b9c662d9c715b6958c8441001e10497647b876c964788dcbdafdab6a1f157d |
| /home/misbahul45/.claude/skills/obsidian-ops/SKILL.md | obsidian-ops | 417 | strict YAML + required fields valid | 4d50723d3ad14fdcebd4bda81f57964895f9d75a19ce229d5bd60c500f8cfd1f |
| /home/misbahul45/.claude/skills/outline-builder/SKILL.md | outline-builder | 1664 | strict YAML + required fields valid | 532830f1a9d223ca116ab84646251b9c355518b70702e9788c2abce9216236c0 |
| /home/misbahul45/.claude/skills/paper-analysis/SKILL.md | paper-analysis | 759 | strict YAML + required fields valid | 829c8cb275d335108ef7cec63ef2a035e254ddcec49ee2a9579ed3c82eb86277 |
| /home/misbahul45/.claude/skills/paper-review/SKILL.md | paper-review | 398 | strict YAML + required fields valid | e875f7550fba9a6d26bd788c0398a32b14edc87c3c15e2cf08787ca4895d6920 |
| /home/misbahul45/.claude/skills/pdf/SKILL.md | pdf | 3125 | strict YAML + required fields valid | 51cde8bdc880d44e9e13e629d618462be4563e4803219a2ed189ffe39635c3f2 |
| /home/misbahul45/.claude/skills/personal-os/SKILL.md | personal-os | 520 | strict YAML + required fields valid | 29a76589da05e4162a439ad14d45f32cb229ec9d7b17b2812fe192a08ac31571 |
| /home/misbahul45/.claude/skills/playwright-interactive/SKILL.md | playwright-interactive | 6801 | strict YAML + required fields valid | 2529dd902005f12c89b65aed648cd22af4d4e7ba7e991159f73e2db740c48ff5 |
| /home/misbahul45/.claude/skills/playwright-mcp-workflows/SKILL.md | playwright-mcp-workflows | 1116 | strict YAML + required fields valid | 66410f6a3a31664ba7d4318ada23a8632adffe79a67cce9b6d1e5d3e9e59ae0f |
| /home/misbahul45/.claude/skills/playwright/SKILL.md | playwright | 946 | strict YAML + required fields valid | d5693079440907bd2d8dde943ee096212dc276c90437512ce4ed802aa2b0f976 |
| /home/misbahul45/.claude/skills/pptx-skills/.claude/skills/markitdown/SKILL.md | markitdown | 1035 | strict YAML + required fields valid | cf2e206be8baf949216a70b321d8b124b9ca534d36cf6a10c1cc47c9a95749a9 |
| /home/misbahul45/.claude/skills/pptx-skills/.claude/skills/slide-analyze/SKILL.md | slide-analyze | 1399 | strict YAML + required fields valid | 32d4cdadce4d654673c07516b2f8d8cb979231840926d2cb495bc991c024d734 |
| /home/misbahul45/.claude/skills/pptx-skills/.claude/skills/slide-edit/SKILL.md | slide-edit | 1348 | strict YAML + required fields valid | b2847845e2819ff84a7c045ed07ee4c60aef73845166622592e79214b10bef6a |
| /home/misbahul45/.claude/skills/pptx-skills/.claude/skills/slide-generate/SKILL.md | slide-generate | 1724 | strict YAML + required fields valid | ad87f1a97a1645a0daa223358f79bdbfbb9c4dad0459cb04146fc34cf189143b |
| /home/misbahul45/.claude/skills/pptx-skills/SKILL.md | pptx-skills | 559 | strict YAML + required fields valid | 9ca9e518127ee10a6db771b51b3aa007f8a93230ee85e1626006b9e7126bb34d |
| /home/misbahul45/.claude/skills/pptx/SKILL.md | pptx | 5349 | strict YAML + required fields valid | a7ff03e2c85b636f55232a6b1555f5dd90216b7a1a359ab289d8364e6acbc6a0 |
| /home/misbahul45/.claude/skills/process-engineering-providers/SKILL.md | process-engineering-providers | 685 | strict YAML + required fields valid | f512f27a4b69425ffd9b06e331a4e02c7aad05e62226aae057e2c1e5d7b750be |
| /home/misbahul45/.claude/skills/process_engineering/SKILL.md | process_engineering | 404 | strict YAML + required fields valid | 0ce5856b9c39cc200d95006c350f2d2b3e32af58a8a762057f8934439c18fe4b |
| /home/misbahul45/.claude/skills/professional-editor/SKILL.md | professional-editor | 412 | strict YAML + required fields valid | 91dadc5ef8e9dad1ea7b6c59cef392dc5d46d7a90fc21a85d1f9d2f759c3c7bc |
| /home/misbahul45/.claude/skills/professional-writer/SKILL.md | professional-writer | 518 | strict YAML + required fields valid | 0cef09ebe9890e2889f8f45abdb426ac589881f4568cde0e9931a740a3390c87 |
| /home/misbahul45/.claude/skills/proposal-red-team/SKILL.md | proposal-red-team | 401 | strict YAML + required fields valid | 5ecd43d84f83af62bca442f3a3257ec9c9e762f73d467df641d5461fbc147f88 |
| /home/misbahul45/.claude/skills/proposal-writer/SKILL.md | proposal-writer | 405 | strict YAML + required fields valid | f1c2cd635efbaecde5323f7d40fe5153a70eb12eb9fea52dad00871afedacd4d |
| /home/misbahul45/.claude/skills/reasoning-critic/SKILL.md | reasoning-critic | 448 | strict YAML + required fields valid | 996ce829eb0a203333b9a380be8619b3dc5072f9cad407c2a5cac53f719cd8b2 |
| /home/misbahul45/.claude/skills/reasoning-orchestrator/SKILL.md | reasoning-orchestrator | 853 | strict YAML + required fields valid | 9a3cc386c644131aba52d69da0061c3b307e2d9dd54097236208b7a50949d4e6 |
| /home/misbahul45/.claude/skills/reasoning-strategy-learner/SKILL.md | reasoning-strategy-learner | 399 | strict YAML + required fields valid | e0fd1c7a44c7ee5c13cb5d969f83e00a8ba1cb432e7ae5a27b379985e489fbb8 |
| /home/misbahul45/.claude/skills/regression-analysis/SKILL.md | regression-analysis | 511 | strict YAML + required fields valid | fcfceb0b2f2f7bd9fa285be712bbf66e6ebbdf08df4387dbe7d2cdd6642d1df6 |
| /home/misbahul45/.claude/skills/repo-context-packaging/SKILL.md | repo-context-packaging | 1363 | strict YAML + required fields valid | 9a3ed45936de1f4f5ad2538001df05142c96b39a2f1e9fedfb1dceb79cf8cd2d |
| /home/misbahul45/.claude/skills/requirement-coverage/SKILL.md | requirement-coverage | 830 | strict YAML + required fields valid | 449f78b8aa67903f106bb1aea1f80014cd2ae2aafe26c3fddbc94657d922dc95 |
| /home/misbahul45/.claude/skills/research-critic/SKILL.md | research-critic | 578 | strict YAML + required fields valid | a7d6bb1b788696de37ade981a008c3cbfd79c6c5384e5d20357ffbda074ef7fa |
| /home/misbahul45/.claude/skills/research-paper-writer/SKILL.md | research-paper-writer | 404 | strict YAML + required fields valid | e6b5af989654d9833aec12e8665e04332b2b61fd4f13ba8df36359bc1fa0f9bf |
| /home/misbahul45/.claude/skills/research-planner/SKILL.md | research-planner | 616 | strict YAML + required fields valid | e6888e8bf01b3643076263088752f32708337f65bc37ada73fc7fc2f54a9f542 |
| /home/misbahul45/.claude/skills/research-proposal/SKILL.md | research-proposal | 401 | strict YAML + required fields valid | 291ba454e45c1724c366884f1a9e5d482408276c1617ab551babeb052813b99e |
| /home/misbahul45/.claude/skills/research/SKILL.md | research | 2637 | strict YAML + required fields valid | 3d8afc8a7fd31151ba4c34aa94b127c0aea4b514ab923c95e66e4429c4cec7cf |
| /home/misbahul45/.claude/skills/reverse-engineer-anything/SKILL.md | reverse-engineer-anything | 5090 | strict YAML + required fields valid | fbcd39d6abe803cf7aa49c1880815bc8e22ba2af87a23681944f687bb7629eb1 |
| /home/misbahul45/.claude/skills/scientific-paper-writer/SKILL.md | scientific-paper-writer | 400 | strict YAML + required fields valid | bb7903316aca315ffc7bf2ce745e6323ce8dcc38d2ca274ea492499f444c9080 |
| /home/misbahul45/.claude/skills/scoring-rubric/SKILL.md | scoring-rubric | 1617 | strict YAML + required fields valid | c452e27b3f276b244604de9b4bd2f2690f214b06ee1da657601128004bb62eb8 |
| /home/misbahul45/.claude/skills/screenshot/SKILL.md | screenshot | 1915 | strict YAML + required fields valid | e54300fdc7c9c6a683263dabb4cf5a4967ec77d343faed439bc6586caea87c36 |
| /home/misbahul45/.claude/skills/secret-audit/SKILL.md | secret-audit | 637 | strict YAML + required fields valid | 2d1b5df0f753154a7efc3a01a36b932196cf6d1ff5ed24a5346236a8f1ba5bb9 |
| /home/misbahul45/.claude/skills/security-best-practices/SKILL.md | security-best-practices | 1663 | strict YAML + required fields valid | 2e52ba9dfd39bb0988ac01642177e0441aeedbcb1f5ca85e88ad3764cb6ac7c4 |
| /home/misbahul45/.claude/skills/security-ownership-map/SKILL.md | security-ownership-map | 2083 | strict YAML + required fields valid | 7dc70ffb10bd9de513ad329d6acccccf3e262175affcf9f73e307bb7bc7449f7 |
| /home/misbahul45/.claude/skills/security-research/SKILL.md | security-research | 588 | strict YAML + required fields valid | 82cf566002604da2d2ff4ea63b71ed6975171985009c2a8978207f26adad6ffd |
| /home/misbahul45/.claude/skills/security-review/SKILL.md | security-review | 1459 | strict YAML + required fields valid | 558471609233989414617ab4195568ffe41d2f86fd6e9db0d867faab722a37a6 |
| /home/misbahul45/.claude/skills/security-threat-model/SKILL.md | security-threat-model | 1112 | strict YAML + required fields valid | 6f891ea91133e99a4391e5edf1fbdbde59a4445efaf43a85d3c61b35be0797de |
| /home/misbahul45/.claude/skills/self-improvement/analyze-failure/SKILL.md | analyze-failure | 579 | strict YAML + required fields valid | 05c16aa3a0336ffd1cbc01ff26fec6945623d8a6896e96b8018ea698eb07a795 |
| /home/misbahul45/.claude/skills/self-improvement/benchmark-model/SKILL.md | benchmark-model | 466 | strict YAML + required fields valid | 420bbe8a2c9061f11625458c6774fdb642afb669f03b3b43e8d5b47c5d094fa0 |
| /home/misbahul45/.claude/skills/self-improvement/compare-models/SKILL.md | compare-models | 369 | strict YAML + required fields valid | 1ac7b84d79899518ee02218015321fffa445a5d76c9337192221ca967a902ec9 |
| /home/misbahul45/.claude/skills/self-improvement/evaluate-agent/SKILL.md | evaluate-agent | 557 | strict YAML + required fields valid | f346651079f7334019bbf1c0444d827110fd019a03171abb9fdb43dec5e377e7 |
| /home/misbahul45/.claude/skills/self-improvement/experience-mining/SKILL.md | experience-mining | 482 | strict YAML + required fields valid | 5c22654451e6753d8efc47acb2764514ef180f8245480ed8f9f0b3f7da83a7f4 |
| /home/misbahul45/.claude/skills/self-improvement/generate-training-data/SKILL.md | generate-training-data | 504 | strict YAML + required fields valid | d29442cdfcfa28487d19cc3fd7e2735c3d81a06642b284ff303de6870b680439 |
| /home/misbahul45/.claude/skills/self-improvement/memory-consolidation/SKILL.md | memory-consolidation | 474 | strict YAML + required fields valid | e134b0b1581c9931d818ae4469bdbd7c368f8149d924f9e0ef4bec4429354816 |
| /home/misbahul45/.claude/skills/self-improvement/optimize-agent-policy/SKILL.md | optimize-agent-policy | 458 | strict YAML + required fields valid | 81ad1ede449a82695a25d6df8121c0f0cee680e5f057ea3488f4b6162501decc |
| /home/misbahul45/.claude/skills/self-improvement/optimize-prompt/SKILL.md | optimize-prompt | 570 | strict YAML + required fields valid | c724892b249e184edceebd33247bce9e7cb9e62b3ba6591d170e6b51fd3919e2 |
| /home/misbahul45/.claude/skills/self-improvement/optimize-rag/SKILL.md | optimize-rag | 456 | strict YAML + required fields valid | 65f46fb1ae87b62b2c7f90763cd1a286187b2b52f39a958977bb8c05d9d90b73 |
| /home/misbahul45/.claude/skills/self-improvement/optimize-tool-routing/SKILL.md | optimize-tool-routing | 437 | strict YAML + required fields valid | b6dbdad1b278e692650240260a7bb6b5964190ec20bec9b2d48826e4c07befab |
| /home/misbahul45/.claude/skills/self-improvement/promote-model/SKILL.md | promote-model | 415 | strict YAML + required fields valid | 7d7a221f8cabc35609ab074d90448de3eca85bc351284c2a4526f20fbe562edb |
| /home/misbahul45/.claude/skills/self-improvement/reflect-trajectory/SKILL.md | reflect-trajectory | 413 | strict YAML + required fields valid | 9322fb7e70195c8c51f01c5bd92621d5504bf981b81e8e464fdd23b2680df072 |
| /home/misbahul45/.claude/skills/self-improvement/rollback-model/SKILL.md | rollback-model | 365 | strict YAML + required fields valid | a4d20b81ed662fbbeaf56dd60decee0a04a985a407a022d7a588566fd8c62505 |
| /home/misbahul45/.claude/skills/self-improvement/run-dpo/SKILL.md | run-dpo | 423 | strict YAML + required fields valid | e438734237b91f978c045e29d008e9fc0a8efcd5c50340a09bab3345a73a2f38 |
| /home/misbahul45/.claude/skills/self-improvement/run-grpo/SKILL.md | run-grpo | 425 | strict YAML + required fields valid | 0c8671dae1f95838cc03438e2c4c40f955046951038766265594e1bf66b60108 |
| /home/misbahul45/.claude/skills/self-improvement/run-sft/SKILL.md | run-sft | 472 | strict YAML + required fields valid | 7b61bbab613d1ffbc43d666163de8832c8f513391245b17bc17cd11f1e5b8f54 |
| /home/misbahul45/.claude/skills/skill-creator/SKILL.md | skill-creator | 1538 | strict YAML + required fields valid | 62b1fc3025c889361a258b719abee551fe1e62478e96155a3a6c7a8a0c5d1081 |
| /home/misbahul45/.claude/skills/skill-improvement-opportunity-logger/SKILL.md | skill-improvement-opportunity-logger | 1367 | strict YAML + required fields valid | 11492b62b6ee9378656f7029af5bdb3523ea6788b7a7ec2944958c62703d3498 |
| /home/misbahul45/.claude/skills/skill-security-review/SKILL.md | skill-security-review | 2308 | strict YAML + required fields valid | 6a49956a987021f607ef78329e8411f3803ab49ce2357507ed20d374d39fee38 |
| /home/misbahul45/.claude/skills/source-evaluation/SKILL.md | source-evaluation | 1160 | strict YAML + required fields valid | 2fbd99894bdc75a244575e131f9b874ed0c6d6b0b352ceab5b941d4d7c4233c0 |
| /home/misbahul45/.claude/skills/source-selector/SKILL.md | source-selector | 762 | strict YAML + required fields valid | a785130364164de43c66477ed8f224dd53c4b4339548c1441b15eb9c3054f49d |
| /home/misbahul45/.claude/skills/structured-project-execution/SKILL.md | structured-project-execution | 1418 | strict YAML + required fields valid | 5ae09343de69ba97fc987d7ce4ba0709544af57dc72781b11df2566123913f30 |
| /home/misbahul45/.claude/skills/submission-readiness/SKILL.md | submission-readiness | 387 | strict YAML + required fields valid | ff725129fc7f5fe6628b16c25d12e38579b29dd6effea48ec78bccbd95044b91 |
| /home/misbahul45/.claude/skills/synced/8e3029d4-9cea-4cf3-996f-0cca498eb494_ef1def4e-0c6b-4db3-b584-88514174c489/built-in-browser/SKILL.md | built-in-browser | 1449 | strict YAML + required fields valid | b5a720afbcde0d6a77c1bc1d34ab56f3d4b09d071b92129783b4faf7f2a3fe62 |
| /home/misbahul45/.claude/skills/synced/8e3029d4-9cea-4cf3-996f-0cca498eb494_ef1def4e-0c6b-4db3-b584-88514174c489/chrome-browser/SKILL.md | chrome-browser | 1321 | strict YAML + required fields valid | c8b0afeee246f333529be3c73c49efaf7d9d10a46d8948b4b736cc758cb4e885 |
| /home/misbahul45/.claude/skills/synced/8e3029d4-9cea-4cf3-996f-0cca498eb494_ef1def4e-0c6b-4db3-b584-88514174c489/computer-use/SKILL.md | computer-use | 2864 | strict YAML + required fields valid | ffbf11e989df3b8c135f6c97e188982908a794a4b1ab640a48e6602129a0206b |
| /home/misbahul45/.claude/skills/synced/8e3029d4-9cea-4cf3-996f-0cca498eb494_ef1def4e-0c6b-4db3-b584-88514174c489/deep-research/SKILL.md | deep-research | 2761 | strict YAML + required fields valid | 46ae8d5a0b95efad0329ac287ea5248c19fbbe195d8270231c4a78ba6217c024 |
| /home/misbahul45/.claude/skills/synced/8e3029d4-9cea-4cf3-996f-0cca498eb494_ef1def4e-0c6b-4db3-b584-88514174c489/docs/SKILL.md | docs | 291 | strict YAML + required fields valid | 98e4fb5934042152d57bc9cb8c0736d5d8e31c6c0122b13ff5836f4c2411fa3e |
| /home/misbahul45/.claude/skills/synced/8e3029d4-9cea-4cf3-996f-0cca498eb494_ef1def4e-0c6b-4db3-b584-88514174c489/docx/SKILL.md | docx | 2095 | strict YAML + required fields valid | b555a732276bba637440d124c1e1a3f8a322ad0441ae885a611c82083441cab7 |
| /home/misbahul45/.claude/skills/synced/8e3029d4-9cea-4cf3-996f-0cca498eb494_ef1def4e-0c6b-4db3-b584-88514174c489/google-workspace/SKILL.md | google-workspace | 3560 | strict YAML + required fields valid | 073e4f759b4aa054be72a4f5bb9d8f51d3df3f8e02149605cf5c5dad3412bc83 |
| /home/misbahul45/.claude/skills/synced/8e3029d4-9cea-4cf3-996f-0cca498eb494_ef1def4e-0c6b-4db3-b584-88514174c489/import-memory/SKILL.md | import-memory | 2244 | strict YAML + required fields valid | 5179b0780b7025c93271c181636a23acc8d05cad3b20584639cbaf1cf9c3b07a |
| /home/misbahul45/.claude/skills/synced/8e3029d4-9cea-4cf3-996f-0cca498eb494_ef1def4e-0c6b-4db3-b584-88514174c489/morning/SKILL.md | morning | 4159 | strict YAML + required fields valid | a7c4dbcb745799736991b027cceae39aae4880cc00ff43871ae5e87b38023bdd |
| /home/misbahul45/.claude/skills/synced/8e3029d4-9cea-4cf3-996f-0cca498eb494_ef1def4e-0c6b-4db3-b584-88514174c489/pdf/SKILL.md | pdf | 2075 | strict YAML + required fields valid | d1c7caf5f35eb7d37877dd7fc33a095037be2b34fb5d2f7f4d43bde3165bb4ee |
| /home/misbahul45/.claude/skills/synced/8e3029d4-9cea-4cf3-996f-0cca498eb494_ef1def4e-0c6b-4db3-b584-88514174c489/pptx/SKILL.md | pptx | 7388 | strict YAML + required fields valid | 3679488c7e497c9b2f14bf026f39624d4c45b9519d845bc08650ce31598b0d6a |
| /home/misbahul45/.claude/skills/synced/8e3029d4-9cea-4cf3-996f-0cca498eb494_ef1def4e-0c6b-4db3-b584-88514174c489/skill-creator/SKILL.md | skill-creator | 8049 | strict YAML + required fields valid | 1d51c0b077c24489baa7fdb6c7072ff0c94479dab7110dad2fc6039a47a4bed4 |
| /home/misbahul45/.claude/skills/synced/8e3029d4-9cea-4cf3-996f-0cca498eb494_ef1def4e-0c6b-4db3-b584-88514174c489/xlsx/SKILL.md | xlsx | 2131 | strict YAML + required fields valid | caa1e1c29cf974c8d874bf3d0a70838445e7342b570f856ddb3e4a21ef7c7e8b |
| /home/misbahul45/.claude/skills/synced/f63407b1-2ca6-4709-8345-45a40e025358_f1e1d4ce-1aac-42a4-9804-73317d4ca8d3/artifact-emulator/SKILL.md | artifact-emulator | 4646 | strict YAML + required fields valid | c0fd1fe3eac655f04d1dd52a82d8e58d1c435dce76a6bb77e7b5ab7365fb9863 |
| /home/misbahul45/.claude/skills/synced/f63407b1-2ca6-4709-8345-45a40e025358_f1e1d4ce-1aac-42a4-9804-73317d4ca8d3/built-in-browser/SKILL.md | built-in-browser | 1561 | strict YAML + required fields valid | 2b6a33da0ff4e041c1bcced2b5d2bd39efc5bfde8f5269cadcc4416ad7df4626 |
| /home/misbahul45/.claude/skills/synced/f63407b1-2ca6-4709-8345-45a40e025358_f1e1d4ce-1aac-42a4-9804-73317d4ca8d3/chrome-browser/SKILL.md | chrome-browser | 1321 | strict YAML + required fields valid | c8b0afeee246f333529be3c73c49efaf7d9d10a46d8948b4b736cc758cb4e885 |
| /home/misbahul45/.claude/skills/synced/f63407b1-2ca6-4709-8345-45a40e025358_f1e1d4ce-1aac-42a4-9804-73317d4ca8d3/computer-use/SKILL.md | computer-use | 2864 | strict YAML + required fields valid | ffbf11e989df3b8c135f6c97e188982908a794a4b1ab640a48e6602129a0206b |
| /home/misbahul45/.claude/skills/synced/f63407b1-2ca6-4709-8345-45a40e025358_f1e1d4ce-1aac-42a4-9804-73317d4ca8d3/deep-research/SKILL.md | deep-research | 2761 | strict YAML + required fields valid | 46ae8d5a0b95efad0329ac287ea5248c19fbbe195d8270231c4a78ba6217c024 |
| /home/misbahul45/.claude/skills/synced/f63407b1-2ca6-4709-8345-45a40e025358_f1e1d4ce-1aac-42a4-9804-73317d4ca8d3/docs/SKILL.md | docs | 291 | strict YAML + required fields valid | 98e4fb5934042152d57bc9cb8c0736d5d8e31c6c0122b13ff5836f4c2411fa3e |
| /home/misbahul45/.claude/skills/synced/f63407b1-2ca6-4709-8345-45a40e025358_f1e1d4ce-1aac-42a4-9804-73317d4ca8d3/docx/SKILL.md | docx | 2095 | strict YAML + required fields valid | b555a732276bba637440d124c1e1a3f8a322ad0441ae885a611c82083441cab7 |
| /home/misbahul45/.claude/skills/synced/f63407b1-2ca6-4709-8345-45a40e025358_f1e1d4ce-1aac-42a4-9804-73317d4ca8d3/google-workspace/SKILL.md | google-workspace | 3560 | strict YAML + required fields valid | 073e4f759b4aa054be72a4f5bb9d8f51d3df3f8e02149605cf5c5dad3412bc83 |
| /home/misbahul45/.claude/skills/synced/f63407b1-2ca6-4709-8345-45a40e025358_f1e1d4ce-1aac-42a4-9804-73317d4ca8d3/import-memory/SKILL.md | import-memory | 2244 | strict YAML + required fields valid | 5179b0780b7025c93271c181636a23acc8d05cad3b20584639cbaf1cf9c3b07a |
| /home/misbahul45/.claude/skills/synced/f63407b1-2ca6-4709-8345-45a40e025358_f1e1d4ce-1aac-42a4-9804-73317d4ca8d3/morning/SKILL.md | morning | 4159 | strict YAML + required fields valid | a7c4dbcb745799736991b027cceae39aae4880cc00ff43871ae5e87b38023bdd |
| /home/misbahul45/.claude/skills/synced/f63407b1-2ca6-4709-8345-45a40e025358_f1e1d4ce-1aac-42a4-9804-73317d4ca8d3/pdf/SKILL.md | pdf | 2075 | strict YAML + required fields valid | d1c7caf5f35eb7d37877dd7fc33a095037be2b34fb5d2f7f4d43bde3165bb4ee |
| /home/misbahul45/.claude/skills/synced/f63407b1-2ca6-4709-8345-45a40e025358_f1e1d4ce-1aac-42a4-9804-73317d4ca8d3/pptx/SKILL.md | pptx | 7388 | strict YAML + required fields valid | 3679488c7e497c9b2f14bf026f39624d4c45b9519d845bc08650ce31598b0d6a |
| /home/misbahul45/.claude/skills/synced/f63407b1-2ca6-4709-8345-45a40e025358_f1e1d4ce-1aac-42a4-9804-73317d4ca8d3/skill-creator/SKILL.md | skill-creator | 8049 | strict YAML + required fields valid | 1d51c0b077c24489baa7fdb6c7072ff0c94479dab7110dad2fc6039a47a4bed4 |
| /home/misbahul45/.claude/skills/synced/f63407b1-2ca6-4709-8345-45a40e025358_f1e1d4ce-1aac-42a4-9804-73317d4ca8d3/xlsx/SKILL.md | xlsx | 2131 | strict YAML + required fields valid | caa1e1c29cf974c8d874bf3d0a70838445e7342b570f856ddb3e4a21ef7c7e8b |
| /home/misbahul45/.claude/skills/tableau-workbook-builder/SKILL.md | tableau-workbook-builder | 2993 | strict YAML + required fields valid | 181c454b0aed5e4793060c69494e46d80ec29c4d7a51215a2cd7ca77f99d18d1 |
| /home/misbahul45/.claude/skills/tdd-workflow/SKILL.md | tdd-workflow | 1264 | strict YAML + required fields valid | 95aa311c529cd9eda0d50522db0b8d43850ef221fd31f146b68993c11af63863 |
| /home/misbahul45/.claude/skills/technical-content-writer/SKILL.md | technical-content-writer | 411 | strict YAML + required fields valid | 43032b121aba05b1a1c4b260bdb9513d2310af01a0df457109c3b7fa5fe23e75 |
| /home/misbahul45/.claude/skills/terminology-bank/SKILL.md | terminology-bank | 1144 | strict YAML + required fields valid | 58e192f1600fa36e1c63d7a2d8e80394140eef2d1afe2e094d32fdbf1c70ce89 |
| /home/misbahul45/.claude/skills/todolife-budget-tracker/SKILL.md | todolife-budget-tracker | 385 | strict YAML + required fields valid | 42a20995c53baa6af4139f57ebc373d057498b007756db0123381e68d9fd8ade |
| /home/misbahul45/.claude/skills/todolife-core-tracker/SKILL.md | todolife-core-tracker | 388 | strict YAML + required fields valid | fb4e09159db1e7d4235355c82b87ee157ef2d1c8392bd8af0365472238106205 |
| /home/misbahul45/.claude/skills/todolife-daily-planner/SKILL.md | todolife-daily-planner | 1951 | strict YAML + required fields valid | fba2728546ae84832b7f700e5f59577a7b0613bc37645025d834284790aa6a3f |
| /home/misbahul45/.claude/skills/todolife-project-router/SKILL.md | todolife-project-router | 437 | strict YAML + required fields valid | 5d1932ae095acf90fe5088c1f9111301fd7bd22115f7643aecaf2a21cafcf5e0 |
| /home/misbahul45/.claude/skills/todolife-schedule-auditor/SKILL.md | todolife-schedule-auditor | 624 | strict YAML + required fields valid | 0b59973f40a7416e6f3276e87a596c6c11f57fde7fb0ca306ff30adea936d66a |
| /home/misbahul45/.claude/skills/transcribe/SKILL.md | transcribe | 711 | strict YAML + required fields valid | 96adbbf92d3aa150af94bb492cc159b903ad519872412ed68adcd287b74d5087 |
| /home/misbahul45/.claude/skills/vercel-react-best-practices/SKILL.md | vercel-react-best-practices | 1756 | strict YAML + required fields valid | 71ed7794962fa6e803ee83030517b5b93a9f70fbfeb431ec4535c5480a8d8355 |
| /home/misbahul45/.claude/skills/web-design-guidelines/SKILL.md | web-design-guidelines | 268 | strict YAML + required fields valid | f4647ca866a3accf763777f83e7682954f0187cd6bea7eea0399796652414e8f |
| /home/misbahul45/.claude/skills/webapp-testing/SKILL.md | webapp-testing | 881 | strict YAML + required fields valid | 51b7349e77ec63b7744a6f63647e7566a0b4d2e301121cc10e8c2113af6556a2 |
| /home/misbahul45/.claude/skills/xlsx/SKILL.md | xlsx | 2135 | strict YAML + required fields valid | 6712b39718fe815054abca9c3ee72f989613e6f771c8a5c58f30a65a6c905622 |
| /home/misbahul45/.claude/skills/xninetzy-academic-safety/SKILL.md | xninetzy-academic-safety | 167 | strict YAML + required fields valid | 96f4ccb1922421efd581fde5e6ad362848221045fa2908f3f7d98275f0a03a13 |
| /home/misbahul45/.claude/skills/xninetzy-artifact-orchestrator/SKILL.md | xninetzy-artifact-orchestrator | 4770 | strict YAML + required fields valid | 4c059137a0f329f6a141ec92ad564271ade05543e25cadb34bf7519131066b2e |
| /home/misbahul45/.claude/skills/xninetzy-assignment-orchestrator/SKILL.md | xninetzy-assignment-orchestrator | 2324 | strict YAML + required fields valid | 0d8f60558d89d55953725c48e0f49f48cd566134e3891cd3f988f6ff5b7871ed |
| /home/misbahul45/.claude/skills/xninetzy-cyber-campus/SKILL.md | xninetzy-cyber-campus | 332 | strict YAML + required fields valid | 8727fa4ef27cbf07d47b9b74f4b5552284a95a64c5b8b6e7c35cffeaf6ab69c2 |
| /home/misbahul45/.claude/skills/xninetzy-deep-research/SKILL.md | xninetzy-deep-research | 2950 | strict YAML + required fields valid | 309e1e4c9f9b9ba118b420a5d0f475f7ad3514dfa841a398b1c84cdac76e0565 |
| /home/misbahul45/.claude/skills/xninetzy-hebat/SKILL.md | xninetzy-hebat | 206 | strict YAML + required fields valid | 64ef561eb8d342d2353927ff293facc98e5483c1c4114427f2ffaa7f08931c95 |
| /home/misbahul45/.claude/skills/xninetzy-krs/SKILL.md | xninetzy-krs | 1107 | strict YAML + required fields valid | 4e66af0dbbb6574413feac817232d18b2b529ae16c52477d64a47a5b8982381b |
| /home/misbahul45/.claude/skills/xninetzy-learning-coach/SKILL.md | xninetzy-learning-coach | 2950 | strict YAML + required fields valid | 8eeb680bc0c0cd0cd82398056f416558ff92bc46d5b56e786964e189a279381d |
| /home/misbahul45/.claude/skills/xninetzy-mcp-lightning/SKILL.md | xninetzy-mcp-lightning | 3118 | strict YAML + required fields valid | 09434f191a4243a790b53e0903c2ece94b7735432acb55e93d265ed1c45b10bf |
| /home/misbahul45/.claude/skills/xninetzy-memory/SKILL.md | xninetzy-memory | 2314 | strict YAML + required fields valid | 67f3d1c7e98e0595f5a60784b54ee02618cb7a23d558b30d9c7113df574ced2f |
| /home/misbahul45/.claude/skills/xninetzy-obsidian-orchestra/SKILL.md | xninetzy-obsidian-orchestra | 740 | strict YAML + required fields valid | d6aef8eb83eaef01931bf7b9e8ad04c1ded48ae4f65ebf50aa5157d9785ef81a |
| /home/misbahul45/.claude/skills/xninetzy-os/SKILL.md | xninetzy-os | 2540 | strict YAML + required fields valid | e970b659487fb645993877ffcfe667170d64a515c2c2151d3538059757223dd8 |
| /home/misbahul45/.claude/skills/xninetzy-research-memory/SKILL.md | xninetzy-research-memory | 2744 | strict YAML + required fields valid | 28c43f838498c66ee2a34efe8583120f057a625cfb57bd0633e4b87324357fee |
| /home/misbahul45/.claude/skills/xninetzy-security-testing/SKILL.md | xninetzy-security-testing | 8235 | strict YAML + required fields valid | 6865264159a3e39202908113351aeff5b5697b21d674b413a7b3105973025a61 |
| /home/misbahul45/.claude/skills/xninetzy-uacc/SKILL.md | xninetzy-uacc | 2687 | strict YAML + required fields valid | c11f65fca46863d827faacb4fe941f541e153dc6afaafb13ab60164b8b28214a |
| /home/misbahul45/.claude/skills/xninetzy-web-analysis/SKILL.md | xninetzy-web-analysis | 4695 | strict YAML + required fields valid | cd086b5e085cd074ab5ec66bbe7a4ed46907b09a3c4813ad812a8cad4b1846f7 |
### opencode

| Path | Name | Tokens | Syntax status | SHA-256 |
|---|---|---|---|---|
| /home/misbahul45/.config/opencode/skills/academic-editor/SKILL.md | academic-editor | 388 | strict YAML + required fields valid | 635f73179fcbb3d6636bc1dc519695550e822e0875717ae50eb11582f9ac33ff |
| /home/misbahul45/.config/opencode/skills/academic-writer/SKILL.md | academic-writer | 404 | strict YAML + required fields valid | 161a3dcd84f25ea63252764a3faa7c82c5e1c89556b9336fa217953d314aaa13 |
| /home/misbahul45/.config/opencode/skills/anti-slop/SKILL.md | anti-slop | 426 | strict YAML + required fields valid | a5137a98751d747285cf8728ed7af6969eae676a1cea07009405e9ee5a841361 |
| /home/misbahul45/.config/opencode/skills/api-security/SKILL.md | api-security | 5764 | strict YAML + required fields valid | 1203063191b9b69c04760429adb7a4c7f6f28cdb0f01c0a4c947c570f7d531c9 |
| /home/misbahul45/.config/opencode/skills/architecture-analysis/SKILL.md | architecture-analysis | 5446 | strict YAML + required fields valid | 17244f125e7e9004004352d32c2282141aa2ba4c0db35085434ad149b5e69a62 |
| /home/misbahul45/.config/opencode/skills/argument-coherence/SKILL.md | argument-coherence | 970 | strict YAML + required fields valid | c2c2eef4a2b1188e65f3fff3f5ae721e498d59be6641b4b06c20b965e226148a |
| /home/misbahul45/.config/opencode/skills/arkcli-agent/SKILL.md | arkcli-agent | 2925 | strict YAML + required fields valid | 61d4f8a8d4972d7aad0077e23da95e85e4aa64e23d8ca8477f4f9341fe29268a |
| /home/misbahul45/.config/opencode/skills/arkcli-api-explorer/SKILL.md | arkcli-api-explorer | 1650 | strict YAML + required fields valid | f98c55d64c6537e9d685ddb3f2cba8693e6f4a616e04350a0e94bb075fbf2f07 |
| /home/misbahul45/.config/opencode/skills/arkcli-auth/SKILL.md | arkcli-auth | 1361 | strict YAML + required fields valid | 55438901d16b9db7602d6746a05a8ce93a68ad62f4217758bea79a4fd573e91b |
| /home/misbahul45/.config/opencode/skills/arkcli-billing/SKILL.md | arkcli-billing | 2680 | strict YAML + required fields valid | 2a22e741820ae9922bc3147da2b246ee446ae80e798b0f3fbfab5d1086af3e58 |
| /home/misbahul45/.config/opencode/skills/arkcli-chat/SKILL.md | arkcli-chat | 2690 | strict YAML + required fields valid | c2623a814f8d7c0dc056dc27e85a8ff60049bbe6284cf21797efe8d48d655f3a |
| /home/misbahul45/.config/opencode/skills/arkcli-config/SKILL.md | arkcli-config | 2245 | strict YAML + required fields valid | c7a0a208cd313cf2685764d3d5fbacc8795aca36550dc5080c8d0fd710fc999a |
| /home/misbahul45/.config/opencode/skills/arkcli-connect/SKILL.md | arkcli-connect | 1841 | strict YAML + required fields valid | fc22cc62593486e43fd5ad668ee82220a579a065151db2ec451b917bed3310f7 |
| /home/misbahul45/.config/opencode/skills/arkcli-custommodel/SKILL.md | arkcli-custommodel | 3587 | strict YAML + required fields valid | a3bc4baae305022e278467fae8c981959a8ee3bb9f674318fd0cef91e9514deb |
| /home/misbahul45/.config/opencode/skills/arkcli-datasets/SKILL.md | arkcli-datasets | 859 | strict YAML + required fields valid | e26a6e0436177ec39c0a7a566723f7c8955027caf430e84ba56677fbca958ce9 |
| /home/misbahul45/.config/opencode/skills/arkcli-deploy/SKILL.md | arkcli-deploy | 2211 | strict YAML + required fields valid | 4676351726365e842b64f5a24029bbc1da1752dfd54a2775844bcf9972cf1de0 |
| /home/misbahul45/.config/opencode/skills/arkcli-doctor/SKILL.md | arkcli-doctor | 4433 | strict YAML + required fields valid | 3ed1b518572e8b8d81e85da3c7907967fae305d835a1eeff496ae0bc19203947 |
| /home/misbahul45/.config/opencode/skills/arkcli-gen/SKILL.md | arkcli-gen | 3886 | strict YAML + required fields valid | 7289c636e853ddfa4fcab508375cdb3fa85eebca0e26913bc4b676ac316eb596 |
| /home/misbahul45/.config/opencode/skills/arkcli-helper/SKILL.md | arkcli-helper | 1903 | strict YAML + required fields valid | d03683009a249395a5aacf3c2bcf04f062deedfe28ad9abd9279f423688b1e46 |
| /home/misbahul45/.config/opencode/skills/arkcli-iam/SKILL.md | arkcli-iam | 601 | strict YAML + required fields valid | ed15bc290bd35c3dd5ef6495a2f5c7b1fe50515b420847772f175042cd7f8dbe |
| /home/misbahul45/.config/opencode/skills/arkcli-infer-endpoint/SKILL.md | arkcli-infer-endpoint | 1607 | strict YAML + required fields valid | a42376322e5693ee1c926d9210b685ab75d97b1678474415c1e6956d2e3bd326 |
| /home/misbahul45/.config/opencode/skills/arkcli-models/SKILL.md | arkcli-models | 5578 | strict YAML + required fields valid | 93b56da3c0a2ec86eba6b6f7b1cd1ab9ce590c3a6277e556cae18be7e36c39b1 |
| /home/misbahul45/.config/opencode/skills/arkcli-onboard/SKILL.md | arkcli-onboard | 1513 | strict YAML + required fields valid | ec065aee469d6eadb19629d891646dd6c8a11ae2056e912abde9a5f1b4730115 |
| /home/misbahul45/.config/opencode/skills/arkcli-plans/SKILL.md | arkcli-plans | 3103 | strict YAML + required fields valid | feafb57f9aacefc5aab98e311f22a36cfa86122379c7d3424a4deac4d7a614ed |
| /home/misbahul45/.config/opencode/skills/arkcli-pricing/SKILL.md | arkcli-pricing | 2581 | strict YAML + required fields valid | d1277394760cbe9d0d0dca55ea7a348b4705c89bf75aa5aa8dcd1d54607c77bb |
| /home/misbahul45/.config/opencode/skills/arkcli-profile/SKILL.md | arkcli-profile | 1260 | strict YAML + required fields valid | 12cea1aca8978ce65702570b4cd55c3be7e972ffe6d8555440f442d5ab3a3063 |
| /home/misbahul45/.config/opencode/skills/arkcli-resources/SKILL.md | arkcli-resources | 2120 | strict YAML + required fields valid | b774ff8d80e38b03c45b5288166ae852487bccfb4d9c6060d263d0ba10c8af27 |
| /home/misbahul45/.config/opencode/skills/arkcli-shared/SKILL.md | arkcli-shared | 1870 | strict YAML + required fields valid | de4b74c46feedbd2c15908357bc034ff920b42fce95a87da8a566552d9e1a45c |
| /home/misbahul45/.config/opencode/skills/arkcli-train-finetune/SKILL.md | arkcli-train-finetune | 2216 | strict YAML + required fields valid | c21fa94d7ca09e4093eee9c93fdac894da22c6c9806db4dbc0a2e68f6ed572db |
| /home/misbahul45/.config/opencode/skills/arkcli-understand/SKILL.md | arkcli-understand | 2544 | strict YAML + required fields valid | bfdd2f1aea38096421e82b71b4cea42e591b315f0675eedcf755768cdd046ea1 |
| /home/misbahul45/.config/opencode/skills/arkcli-usage/SKILL.md | arkcli-usage | 3112 | strict YAML + required fields valid | e5803a26c0762d4d8ef2ddc055015fe502b1a417c4640d3f0e6abc924b15a0b8 |
| /home/misbahul45/.config/opencode/skills/benchmark-analysis/SKILL.md | benchmark-analysis | 539 | strict YAML + required fields valid | aca8329463885331581fbfc26face5d4b342e41c67d77cf8898a622a7c631b32 |
| /home/misbahul45/.config/opencode/skills/business-writer/SKILL.md | business-writer | 398 | strict YAML + required fields valid | b09b31698d699599837beebc4c07382eca4f05f466ce9bffb5e31358d8215904 |
| /home/misbahul45/.config/opencode/skills/career/alternative-titles/SKILL.md | alternative-titles | 288 | strict YAML + required fields valid | c2a60507cdd95a5aa4d196fbcbd70fb42b1a03dc270b9bba1a753d0baf12baf8 |
| /home/misbahul45/.config/opencode/skills/career/application-tracking/SKILL.md | application-tracking | 314 | strict YAML + required fields valid | 07566e6753d4586d4a2626290228a21d6a03258e41a1d015239b0e60389121b1 |
| /home/misbahul45/.config/opencode/skills/career/company-research/SKILL.md | company-research | 382 | strict YAML + required fields valid | e86e906d82b6376eb87c85ee3100f82ea5b163e0314719284773997c810fef91 |
| /home/misbahul45/.config/opencode/skills/career/company-search/SKILL.md | company-search | 312 | strict YAML + required fields valid | f0012d6fffafd7d554d196b9506c121497c5d311c6f991e6bcadd809bb980354 |
| /home/misbahul45/.config/opencode/skills/career/cv-analysis/SKILL.md | cv-analysis | 393 | strict YAML + required fields valid | 14b129e35c78b117f8722ae2e94f5d17912dc57bd353341ce299d6cde97a8edd |
| /home/misbahul45/.config/opencode/skills/career/extract-requirements/SKILL.md | extract-requirements | 291 | strict YAML + required fields valid | cb57c75aa69097ef688bd913b923de16fa0dfb6ce576bf10fd45fec1176fd7b4 |
| /home/misbahul45/.config/opencode/skills/career/hidden-jobs/SKILL.md | hidden-jobs | 325 | strict YAML + required fields valid | c0f91e7cf101e79dc44d46af004828bcf8e93801c58ba981e4d9c6ece3d2c91b |
| /home/misbahul45/.config/opencode/skills/career/internship-discovery/SKILL.md | internship-discovery | 405 | strict YAML + required fields valid | 77f18c4d791b4aa5cf34e699486e1a4406782a4ba997fa3d4c690a041ce01699 |
| /home/misbahul45/.config/opencode/skills/career/interview-prep/SKILL.md | interview-prep | 386 | ScannerError | 66485ca3ef5f7761c39f0123bf1cbc75ae605a8c01e87a8817682756510860bf |
| /home/misbahul45/.config/opencode/skills/career/job-discovery/SKILL.md | job-discovery | 477 | strict YAML + required fields valid | cc29eaac41ca80ca92f85d6fb7124e2835a9194a75e29acd585cc0c286d4e701 |
| /home/misbahul45/.config/opencode/skills/career/job-matching/SKILL.md | job-matching | 405 | strict YAML + required fields valid | b1549fdef652bae132d8cf55c139c744de5f1570c9f51ed36ef9a769fae408ed |
| /home/misbahul45/.config/opencode/skills/career/job-monitoring/SKILL.md | job-monitoring | 344 | strict YAML + required fields valid | f3c2d90125b9682d7c9d17241bed4489ee8411b5f36efece629283a0dfa594e1 |
| /home/misbahul45/.config/opencode/skills/career/job-risk-analysis/SKILL.md | job-risk-analysis | 372 | strict YAML + required fields valid | e02ab3bbdf7b58a216ba00322b445cb53759174de905179b929322f38de5a260 |
| /home/misbahul45/.config/opencode/skills/career/job-search/SKILL.md | job-search | 438 | strict YAML + required fields valid | 719a1c086bef4702fe3738ce612d20282e4740e12da2db344652546526a50263 |
| /home/misbahul45/.config/opencode/skills/career/market-skill-trend/SKILL.md | market-skill-trend | 408 | strict YAML + required fields valid | 65fdc6acdf13e80033f271d249383b27588b654d465b9518097c4bd25c50eb6a |
| /home/misbahul45/.config/opencode/skills/career/resume-tailoring/SKILL.md | resume-tailoring | 374 | strict YAML + required fields valid | 68237fe3762724f959b8e33a0fc061d3901d6328603905ca8a76a7163fd47228 |
| /home/misbahul45/.config/opencode/skills/career/salary-analysis/SKILL.md | salary-analysis | 386 | strict YAML + required fields valid | 927f1db77aa1174279fc4a486fcc1b951dc63dd7f0f05daf49fa9c47557292ef |
| /home/misbahul45/.config/opencode/skills/career/similar-jobs/SKILL.md | similar-jobs | 302 | strict YAML + required fields valid | 9c1f579ef6130d492f2b91bf0b5fda2c3ceb43979fa3cd26601cff3041815627 |
| /home/misbahul45/.config/opencode/skills/career/skill-gap/SKILL.md | skill-gap | 428 | strict YAML + required fields valid | 1d9477eab81534aae106d8af9bbd5461b9fbcaad3c006f1ef6cb5273631cccc7 |
| /home/misbahul45/.config/opencode/skills/citation-validation/SKILL.md | citation-validation | 941 | strict YAML + required fields valid | 0af168b02c3e0ded78271854eb7c062b08751a5c1cf2718a53cee9b46c64ed6f |
| /home/misbahul45/.config/opencode/skills/claim-lattice/SKILL.md | claim-lattice | 1544 | strict YAML + required fields valid | 8d73475d60e26163f8d6e07dd49fbd26ecacce1c0586dd61b590e5fc6f0cdec2 |
| /home/misbahul45/.config/opencode/skills/cli-creator/SKILL.md | cli-creator | 7186 | strict YAML + required fields valid | f37263afb9a0c66d6d85e316fbf258e1e248965b10de1edfe6fe747b4ef3f249 |
| /home/misbahul45/.config/opencode/skills/code-review/SKILL.md | code-review | 7082 | strict YAML + required fields valid | 0e5958e3571783a8cce19cef8a12df25c7db082d76cbf9cae5f59678ece446d0 |
| /home/misbahul45/.config/opencode/skills/competition-proposal/SKILL.md | competition-proposal | 402 | strict YAML + required fields valid | 58cfa8fc400ffd527a52b364d04a4b607b1eb10e93a5bfb1f0bb172a9aafc3a4 |
| /home/misbahul45/.config/opencode/skills/consultant-challenge/SKILL.md | consultant-challenge | 392 | strict YAML + required fields valid | 8257e6a72604473201a131081ce520661fe3a5fa65e67238fe9f650963472acd |
| /home/misbahul45/.config/opencode/skills/consultant/SKILL.md | consultant | 417 | strict YAML + required fields valid | 38a1ec7e0f8b8d42307160bd4d9488f912dcf7c14c205f7ae1386631fea37604 |
| /home/misbahul45/.config/opencode/skills/consulting-pptx-skill/SKILL.md | consulting-pptx-skill | 3232 | strict YAML + required fields valid | 973c838db1e44f364f6695ef86e8f90a74504aee1ba10914f96b0d1a84295a5b |
| /home/misbahul45/.config/opencode/skills/consulting-pptx/SKILL.md | consulting-pptx | 1013 | strict YAML + required fields valid | 913fa711c0349746d5cb69f3f4bcfb16e53a8679e5fb3abecc952a0551904c05 |
| /home/misbahul45/.config/opencode/skills/context-engineering/SKILL.md | context-engineering | 7177 | strict YAML + required fields valid | c1a810f0796bbfbefeba3b119a54f7581ccfdeb74a7c80eb256933528f8dfc92 |
| /home/misbahul45/.config/opencode/skills/contradiction-hunter/SKILL.md | contradiction-hunter | 468 | strict YAML + required fields valid | 0675c5460eaf7233141035c55fd28f9962f648f75590e1da17a805c8c0cd2820 |
| /home/misbahul45/.config/opencode/skills/cyber-campus/SKILL.md | cyber-campus | 5777 | strict YAML + required fields valid | 2f9baf88354828c1fabdc1c7fc1b052c3be60c1aed17b9a0dd02a25b9a95b287 |
| /home/misbahul45/.config/opencode/skills/data-analysis/SKILL.md | data-analysis | 610 | strict YAML + required fields valid | 788437361517076801a2be07f4b059bf5d1bd21b6f2175b17153c2a32c71b1ac |
| /home/misbahul45/.config/opencode/skills/debugging/SKILL.md | debugging | 6561 | strict YAML + required fields valid | 2d22d97f0e5d8b1c4e699582ac2f66cfdfe81b4bae6f79346ec9b3f4e4f8bea8 |
| /home/misbahul45/.config/opencode/skills/define-goal/SKILL.md | define-goal | 7059 | strict YAML + required fields valid | 68531b47ba2806e2be94c76850516d413681981c9d9097092c5f94b6f13e3d60 |
| /home/misbahul45/.config/opencode/skills/dependency-audit/SKILL.md | dependency-audit | 8361 | strict YAML + required fields valid | 24ae5c89d692de565643aa79f72e1723dafb627fe38ce301a95510700a763821 |
| /home/misbahul45/.config/opencode/skills/evidence-grader/SKILL.md | evidence-grader | 463 | strict YAML + required fields valid | 02fdf8320773cfd6d05fb52e0aa9aa6b6a7e0a98370b152bb48a8e0a910a5394 |
| /home/misbahul45/.config/opencode/skills/evidence-synthesis/SKILL.md | evidence-synthesis | 752 | strict YAML + required fields valid | 57e0f526fea50430d3faf7ff82b395837cd776c0403922473ac2e31c1ccaeb18 |
| /home/misbahul45/.config/opencode/skills/exam_qa/SKILL.md | exam_qa | 435 | strict YAML + required fields valid | 4b73517232d23453550801daf41eff49ddd217512094a193344dffdd12b3199b |
| /home/misbahul45/.config/opencode/skills/executive-writer/SKILL.md | executive-writer | 411 | strict YAML + required fields valid | 10b2aab99ef39184f446f8356508f6d5e584688e65642e727c2b0dea26411a12 |
| /home/misbahul45/.config/opencode/skills/gh-fix-ci/SKILL.md | gh-fix-ci | 892 | strict YAML + required fields valid | 66ffd7fd69abc96527d8cde3920490eaff1b686ce29152ab97e0f577c47f11a6 |
| /home/misbahul45/.config/opencode/skills/grant-proposal/SKILL.md | grant-proposal | 402 | strict YAML + required fields valid | 5b796c40ab5b92481bf2956d74bf58fb5e0bc206cb48d4cbb5cfca663b8e3eac |
| /home/misbahul45/.config/opencode/skills/graph-rag/SKILL.md | graph-rag | 8913 | strict YAML + required fields valid | fd294179bdad92ad091af0a082add852b2d27186c413f3809e26c6dbe22b184a |
| /home/misbahul45/.config/opencode/skills/hebat-academic/SKILL.md | hebat-academic | 4028 | strict YAML + required fields valid | b0d3c305b9e05cfebaf91fcb265bb0346a4e15f0a0a668a6ead6773e3d440ffd |
| /home/misbahul45/.config/opencode/skills/hebat-assignment/SKILL.md | hebat-assignment | 5080 | strict YAML + required fields valid | de2b27b3fd35d7e334186d6700d6df13e9cfccf6523db1b2b1d8db167955ccaf |
| /home/misbahul45/.config/opencode/skills/it-learning/SKILL.md | it-learning | 1534 | strict YAML + required fields valid | c24d46654a7742ed263102be08fdb3047d87a5d49a5ad407c081608a2039806b |
| /home/misbahul45/.config/opencode/skills/jupyter-notebook/SKILL.md | jupyter-notebook | 934 | strict YAML + required fields valid | 735c09068509503cffd764e6d32be58e734cc9e7c6f14aab1c26c394c7d6c7d1 |
| /home/misbahul45/.config/opencode/skills/life-management/SKILL.md | life-management | 1648 | strict YAML + required fields valid | 7bc57608409c31342cfc45808b23ba3f5454dabd147a082b100604326b59d8be |
| /home/misbahul45/.config/opencode/skills/literature-review-writer/SKILL.md | literature-review-writer | 411 | strict YAML + required fields valid | f6e66ff67f10024908902aae063a44de4446cafeb7c8f1f641888702bcf5a083 |
| /home/misbahul45/.config/opencode/skills/literature-review/SKILL.md | literature-review | 653 | strict YAML + required fields valid | 61b457849ad8f32c32ab71cac908a419db82efc68c6012550612ae22043d6abb |
| /home/misbahul45/.config/opencode/skills/mcp-development/SKILL.md | mcp-development | 1848 | strict YAML + required fields valid | 26a3e1e376efd2012197f0322020bdf1f3acc3ad1f9a86688cf74c6622cb3601 |
| /home/misbahul45/.config/opencode/skills/mcp-discovery/SKILL.md | mcp-discovery | 584 | strict YAML + required fields valid | b3c02d2151a328628fba78015d17142509d66fa50a663a4338694e604d0418fb |
| /home/misbahul45/.config/opencode/skills/memory-chat/SKILL.md | memory-chat | 1753 | strict YAML + required fields valid | b7bbfabb0be019fbbc8ce5e7c078589725c47c3d6f540fd3a1ee27e2dda1cb1f |
| /home/misbahul45/.config/opencode/skills/memory-management/SKILL.md | memory-management | 1552 | strict YAML + required fields valid | 620a86e9039bf2445b632b07a263698ba1dab2353c9610a2ffd024bc7dc27daf |
| /home/misbahul45/.config/opencode/skills/methodology-rater/SKILL.md | methodology-rater | 1772 | strict YAML + required fields valid | b0f99aadd4f3d3346691824c99e78ebd55464d6da339b11480de3ff55afeda4e |
| /home/misbahul45/.config/opencode/skills/multi-agent-orchestration/SKILL.md | multi-agent-orchestration | 1556 | strict YAML + required fields valid | 101ef2b7e5951f717ce19a15899b90a13e8da00b723578d3efe6a2065effdf7f |
| /home/misbahul45/.config/opencode/skills/obsidian-knowledge/SKILL.md | obsidian-knowledge | 350 | strict YAML + required fields valid | a6b9c662d9c715b6958c8441001e10497647b876c964788dcbdafdab6a1f157d |
| /home/misbahul45/.config/opencode/skills/obsidian-ops/SKILL.md | obsidian-ops | 417 | strict YAML + required fields valid | 4d50723d3ad14fdcebd4bda81f57964895f9d75a19ce229d5bd60c500f8cfd1f |
| /home/misbahul45/.config/opencode/skills/outline-builder/SKILL.md | outline-builder | 1664 | strict YAML + required fields valid | 532830f1a9d223ca116ab84646251b9c355518b70702e9788c2abce9216236c0 |
| /home/misbahul45/.config/opencode/skills/paper-analysis/SKILL.md | paper-analysis | 759 | strict YAML + required fields valid | 829c8cb275d335108ef7cec63ef2a035e254ddcec49ee2a9579ed3c82eb86277 |
| /home/misbahul45/.config/opencode/skills/paper-review/SKILL.md | paper-review | 398 | strict YAML + required fields valid | e875f7550fba9a6d26bd788c0398a32b14edc87c3c15e2cf08787ca4895d6920 |
| /home/misbahul45/.config/opencode/skills/pdf/SKILL.md | pdf | 3125 | strict YAML + required fields valid | 51cde8bdc880d44e9e13e629d618462be4563e4803219a2ed189ffe39635c3f2 |
| /home/misbahul45/.config/opencode/skills/personal-os/SKILL.md | personal-os | 520 | strict YAML + required fields valid | 29a76589da05e4162a439ad14d45f32cb229ec9d7b17b2812fe192a08ac31571 |
| /home/misbahul45/.config/opencode/skills/playwright-interactive/SKILL.md | playwright-interactive | 6801 | strict YAML + required fields valid | 2529dd902005f12c89b65aed648cd22af4d4e7ba7e991159f73e2db740c48ff5 |
| /home/misbahul45/.config/opencode/skills/playwright-mcp-workflows/SKILL.md | playwright-mcp-workflows | 1116 | strict YAML + required fields valid | 66410f6a3a31664ba7d4318ada23a8632adffe79a67cce9b6d1e5d3e9e59ae0f |
| /home/misbahul45/.config/opencode/skills/playwright/SKILL.md | playwright | 946 | strict YAML + required fields valid | d5693079440907bd2d8dde943ee096212dc276c90437512ce4ed802aa2b0f976 |
| /home/misbahul45/.config/opencode/skills/pptx-skills/.claude/skills/markitdown/SKILL.md | markitdown | 1035 | strict YAML + required fields valid | cf2e206be8baf949216a70b321d8b124b9ca534d36cf6a10c1cc47c9a95749a9 |
| /home/misbahul45/.config/opencode/skills/pptx-skills/.claude/skills/slide-analyze/SKILL.md | slide-analyze | 1399 | strict YAML + required fields valid | 32d4cdadce4d654673c07516b2f8d8cb979231840926d2cb495bc991c024d734 |
| /home/misbahul45/.config/opencode/skills/pptx-skills/.claude/skills/slide-edit/SKILL.md | slide-edit | 1348 | strict YAML + required fields valid | b2847845e2819ff84a7c045ed07ee4c60aef73845166622592e79214b10bef6a |
| /home/misbahul45/.config/opencode/skills/pptx-skills/.claude/skills/slide-generate/SKILL.md | slide-generate | 1724 | strict YAML + required fields valid | ad87f1a97a1645a0daa223358f79bdbfbb9c4dad0459cb04146fc34cf189143b |
| /home/misbahul45/.config/opencode/skills/pptx-skills/SKILL.md | pptx-skills | 559 | strict YAML + required fields valid | 9ca9e518127ee10a6db771b51b3aa007f8a93230ee85e1626006b9e7126bb34d |
| /home/misbahul45/.config/opencode/skills/process-engineering-providers/SKILL.md | process-engineering-providers | 685 | strict YAML + required fields valid | f512f27a4b69425ffd9b06e331a4e02c7aad05e62226aae057e2c1e5d7b750be |
| /home/misbahul45/.config/opencode/skills/process_engineering/SKILL.md | process_engineering | 404 | strict YAML + required fields valid | 0ce5856b9c39cc200d95006c350f2d2b3e32af58a8a762057f8934439c18fe4b |
| /home/misbahul45/.config/opencode/skills/professional-editor/SKILL.md | professional-editor | 412 | strict YAML + required fields valid | 91dadc5ef8e9dad1ea7b6c59cef392dc5d46d7a90fc21a85d1f9d2f759c3c7bc |
| /home/misbahul45/.config/opencode/skills/professional-writer/SKILL.md | professional-writer | 518 | strict YAML + required fields valid | 0cef09ebe9890e2889f8f45abdb426ac589881f4568cde0e9931a740a3390c87 |
| /home/misbahul45/.config/opencode/skills/proposal-red-team/SKILL.md | proposal-red-team | 401 | strict YAML + required fields valid | 5ecd43d84f83af62bca442f3a3257ec9c9e762f73d467df641d5461fbc147f88 |
| /home/misbahul45/.config/opencode/skills/proposal-writer/SKILL.md | proposal-writer | 405 | strict YAML + required fields valid | f1c2cd635efbaecde5323f7d40fe5153a70eb12eb9fea52dad00871afedacd4d |
| /home/misbahul45/.config/opencode/skills/reasoning-critic/SKILL.md | reasoning-critic | 448 | strict YAML + required fields valid | 996ce829eb0a203333b9a380be8619b3dc5072f9cad407c2a5cac53f719cd8b2 |
| /home/misbahul45/.config/opencode/skills/reasoning-orchestrator/SKILL.md | reasoning-orchestrator | 853 | strict YAML + required fields valid | 9a3cc386c644131aba52d69da0061c3b307e2d9dd54097236208b7a50949d4e6 |
| /home/misbahul45/.config/opencode/skills/reasoning-strategy-learner/SKILL.md | reasoning-strategy-learner | 399 | strict YAML + required fields valid | e0fd1c7a44c7ee5c13cb5d969f83e00a8ba1cb432e7ae5a27b379985e489fbb8 |
| /home/misbahul45/.config/opencode/skills/regression-analysis/SKILL.md | regression-analysis | 511 | strict YAML + required fields valid | fcfceb0b2f2f7bd9fa285be712bbf66e6ebbdf08df4387dbe7d2cdd6642d1df6 |
| /home/misbahul45/.config/opencode/skills/repo-context-packaging/SKILL.md | repo-context-packaging | 1363 | strict YAML + required fields valid | 9a3ed45936de1f4f5ad2538001df05142c96b39a2f1e9fedfb1dceb79cf8cd2d |
| /home/misbahul45/.config/opencode/skills/requirement-coverage/SKILL.md | requirement-coverage | 830 | strict YAML + required fields valid | 449f78b8aa67903f106bb1aea1f80014cd2ae2aafe26c3fddbc94657d922dc95 |
| /home/misbahul45/.config/opencode/skills/research-critic/SKILL.md | research-critic | 578 | strict YAML + required fields valid | a7d6bb1b788696de37ade981a008c3cbfd79c6c5384e5d20357ffbda074ef7fa |
| /home/misbahul45/.config/opencode/skills/research-paper-writer/SKILL.md | research-paper-writer | 404 | strict YAML + required fields valid | e6b5af989654d9833aec12e8665e04332b2b61fd4f13ba8df36359bc1fa0f9bf |
| /home/misbahul45/.config/opencode/skills/research-planner/SKILL.md | research-planner | 616 | strict YAML + required fields valid | e6888e8bf01b3643076263088752f32708337f65bc37ada73fc7fc2f54a9f542 |
| /home/misbahul45/.config/opencode/skills/research-proposal/SKILL.md | research-proposal | 401 | strict YAML + required fields valid | 291ba454e45c1724c366884f1a9e5d482408276c1617ab551babeb052813b99e |
| /home/misbahul45/.config/opencode/skills/research/SKILL.md | research | 2637 | strict YAML + required fields valid | 3d8afc8a7fd31151ba4c34aa94b127c0aea4b514ab923c95e66e4429c4cec7cf |
| /home/misbahul45/.config/opencode/skills/reverse-engineer-anything/SKILL.md | reverse-engineer-anything | 5090 | strict YAML + required fields valid | fbcd39d6abe803cf7aa49c1880815bc8e22ba2af87a23681944f687bb7629eb1 |
| /home/misbahul45/.config/opencode/skills/scientific-paper-writer/SKILL.md | scientific-paper-writer | 400 | strict YAML + required fields valid | bb7903316aca315ffc7bf2ce745e6323ce8dcc38d2ca274ea492499f444c9080 |
| /home/misbahul45/.config/opencode/skills/scoring-rubric/SKILL.md | scoring-rubric | 1617 | strict YAML + required fields valid | c452e27b3f276b244604de9b4bd2f2690f214b06ee1da657601128004bb62eb8 |
| /home/misbahul45/.config/opencode/skills/screenshot/SKILL.md | screenshot | 1915 | strict YAML + required fields valid | e54300fdc7c9c6a683263dabb4cf5a4967ec77d343faed439bc6586caea87c36 |
| /home/misbahul45/.config/opencode/skills/secret-audit/SKILL.md | secret-audit | 637 | strict YAML + required fields valid | 2d1b5df0f753154a7efc3a01a36b932196cf6d1ff5ed24a5346236a8f1ba5bb9 |
| /home/misbahul45/.config/opencode/skills/security-best-practices/SKILL.md | security-best-practices | 1663 | strict YAML + required fields valid | 2e52ba9dfd39bb0988ac01642177e0441aeedbcb1f5ca85e88ad3764cb6ac7c4 |
| /home/misbahul45/.config/opencode/skills/security-ownership-map/SKILL.md | security-ownership-map | 2083 | strict YAML + required fields valid | 7dc70ffb10bd9de513ad329d6acccccf3e262175affcf9f73e307bb7bc7449f7 |
| /home/misbahul45/.config/opencode/skills/security-research/SKILL.md | security-research | 588 | strict YAML + required fields valid | 82cf566002604da2d2ff4ea63b71ed6975171985009c2a8978207f26adad6ffd |
| /home/misbahul45/.config/opencode/skills/security-review/SKILL.md | security-review | 1459 | strict YAML + required fields valid | 558471609233989414617ab4195568ffe41d2f86fd6e9db0d867faab722a37a6 |
| /home/misbahul45/.config/opencode/skills/security-threat-model/SKILL.md | security-threat-model | 1112 | strict YAML + required fields valid | 6f891ea91133e99a4391e5edf1fbdbde59a4445efaf43a85d3c61b35be0797de |
| /home/misbahul45/.config/opencode/skills/self-improvement/analyze-failure/SKILL.md | analyze-failure | 579 | strict YAML + required fields valid | 05c16aa3a0336ffd1cbc01ff26fec6945623d8a6896e96b8018ea698eb07a795 |
| /home/misbahul45/.config/opencode/skills/self-improvement/benchmark-model/SKILL.md | benchmark-model | 466 | strict YAML + required fields valid | 420bbe8a2c9061f11625458c6774fdb642afb669f03b3b43e8d5b47c5d094fa0 |
| /home/misbahul45/.config/opencode/skills/self-improvement/compare-models/SKILL.md | compare-models | 369 | strict YAML + required fields valid | 1ac7b84d79899518ee02218015321fffa445a5d76c9337192221ca967a902ec9 |
| /home/misbahul45/.config/opencode/skills/self-improvement/evaluate-agent/SKILL.md | evaluate-agent | 557 | strict YAML + required fields valid | f346651079f7334019bbf1c0444d827110fd019a03171abb9fdb43dec5e377e7 |
| /home/misbahul45/.config/opencode/skills/self-improvement/experience-mining/SKILL.md | experience-mining | 482 | strict YAML + required fields valid | 5c22654451e6753d8efc47acb2764514ef180f8245480ed8f9f0b3f7da83a7f4 |
| /home/misbahul45/.config/opencode/skills/self-improvement/generate-training-data/SKILL.md | generate-training-data | 504 | strict YAML + required fields valid | d29442cdfcfa28487d19cc3fd7e2735c3d81a06642b284ff303de6870b680439 |
| /home/misbahul45/.config/opencode/skills/self-improvement/memory-consolidation/SKILL.md | memory-consolidation | 474 | strict YAML + required fields valid | e134b0b1581c9931d818ae4469bdbd7c368f8149d924f9e0ef4bec4429354816 |
| /home/misbahul45/.config/opencode/skills/self-improvement/optimize-agent-policy/SKILL.md | optimize-agent-policy | 458 | strict YAML + required fields valid | 81ad1ede449a82695a25d6df8121c0f0cee680e5f057ea3488f4b6162501decc |
| /home/misbahul45/.config/opencode/skills/self-improvement/optimize-prompt/SKILL.md | optimize-prompt | 570 | strict YAML + required fields valid | c724892b249e184edceebd33247bce9e7cb9e62b3ba6591d170e6b51fd3919e2 |
| /home/misbahul45/.config/opencode/skills/self-improvement/optimize-rag/SKILL.md | optimize-rag | 456 | strict YAML + required fields valid | 65f46fb1ae87b62b2c7f90763cd1a286187b2b52f39a958977bb8c05d9d90b73 |
| /home/misbahul45/.config/opencode/skills/self-improvement/optimize-tool-routing/SKILL.md | optimize-tool-routing | 437 | strict YAML + required fields valid | b6dbdad1b278e692650240260a7bb6b5964190ec20bec9b2d48826e4c07befab |
| /home/misbahul45/.config/opencode/skills/self-improvement/promote-model/SKILL.md | promote-model | 415 | strict YAML + required fields valid | 7d7a221f8cabc35609ab074d90448de3eca85bc351284c2a4526f20fbe562edb |
| /home/misbahul45/.config/opencode/skills/self-improvement/reflect-trajectory/SKILL.md | reflect-trajectory | 413 | strict YAML + required fields valid | 9322fb7e70195c8c51f01c5bd92621d5504bf981b81e8e464fdd23b2680df072 |
| /home/misbahul45/.config/opencode/skills/self-improvement/rollback-model/SKILL.md | rollback-model | 365 | strict YAML + required fields valid | a4d20b81ed662fbbeaf56dd60decee0a04a985a407a022d7a588566fd8c62505 |
| /home/misbahul45/.config/opencode/skills/self-improvement/run-dpo/SKILL.md | run-dpo | 423 | strict YAML + required fields valid | e438734237b91f978c045e29d008e9fc0a8efcd5c50340a09bab3345a73a2f38 |
| /home/misbahul45/.config/opencode/skills/self-improvement/run-grpo/SKILL.md | run-grpo | 425 | strict YAML + required fields valid | 0c8671dae1f95838cc03438e2c4c40f955046951038766265594e1bf66b60108 |
| /home/misbahul45/.config/opencode/skills/self-improvement/run-sft/SKILL.md | run-sft | 472 | strict YAML + required fields valid | 7b61bbab613d1ffbc43d666163de8832c8f513391245b17bc17cd11f1e5b8f54 |
| /home/misbahul45/.config/opencode/skills/skill-creator/SKILL.md | skill-creator | 1538 | strict YAML + required fields valid | 62b1fc3025c889361a258b719abee551fe1e62478e96155a3a6c7a8a0c5d1081 |
| /home/misbahul45/.config/opencode/skills/skill-improvement-opportunity-logger/SKILL.md | skill-improvement-opportunity-logger | 1367 | strict YAML + required fields valid | 11492b62b6ee9378656f7029af5bdb3523ea6788b7a7ec2944958c62703d3498 |
| /home/misbahul45/.config/opencode/skills/skill-security-review/SKILL.md | skill-security-review | 2308 | strict YAML + required fields valid | 6a49956a987021f607ef78329e8411f3803ab49ce2357507ed20d374d39fee38 |
| /home/misbahul45/.config/opencode/skills/source-evaluation/SKILL.md | source-evaluation | 1160 | strict YAML + required fields valid | 2fbd99894bdc75a244575e131f9b874ed0c6d6b0b352ceab5b941d4d7c4233c0 |
| /home/misbahul45/.config/opencode/skills/source-selector/SKILL.md | source-selector | 762 | strict YAML + required fields valid | a785130364164de43c66477ed8f224dd53c4b4339548c1441b15eb9c3054f49d |
| /home/misbahul45/.config/opencode/skills/structured-project-execution/SKILL.md | structured-project-execution | 1418 | strict YAML + required fields valid | 5ae09343de69ba97fc987d7ce4ba0709544af57dc72781b11df2566123913f30 |
| /home/misbahul45/.config/opencode/skills/submission-readiness/SKILL.md | submission-readiness | 387 | strict YAML + required fields valid | ff725129fc7f5fe6628b16c25d12e38579b29dd6effea48ec78bccbd95044b91 |
| /home/misbahul45/.config/opencode/skills/tableau-workbook-builder/SKILL.md | tableau-workbook-builder | 2993 | strict YAML + required fields valid | 181c454b0aed5e4793060c69494e46d80ec29c4d7a51215a2cd7ca77f99d18d1 |
| /home/misbahul45/.config/opencode/skills/tdd-workflow/SKILL.md | tdd-workflow | 1264 | strict YAML + required fields valid | 95aa311c529cd9eda0d50522db0b8d43850ef221fd31f146b68993c11af63863 |
| /home/misbahul45/.config/opencode/skills/technical-content-writer/SKILL.md | technical-content-writer | 411 | strict YAML + required fields valid | 43032b121aba05b1a1c4b260bdb9513d2310af01a0df457109c3b7fa5fe23e75 |
| /home/misbahul45/.config/opencode/skills/terminology-bank/SKILL.md | terminology-bank | 1144 | strict YAML + required fields valid | 58e192f1600fa36e1c63d7a2d8e80394140eef2d1afe2e094d32fdbf1c70ce89 |
| /home/misbahul45/.config/opencode/skills/todolife-budget-tracker/SKILL.md | todolife-budget-tracker | 385 | strict YAML + required fields valid | 42a20995c53baa6af4139f57ebc373d057498b007756db0123381e68d9fd8ade |
| /home/misbahul45/.config/opencode/skills/todolife-core-tracker/SKILL.md | todolife-core-tracker | 388 | strict YAML + required fields valid | fb4e09159db1e7d4235355c82b87ee157ef2d1c8392bd8af0365472238106205 |
| /home/misbahul45/.config/opencode/skills/todolife-daily-planner/SKILL.md | todolife-daily-planner | 1951 | strict YAML + required fields valid | fba2728546ae84832b7f700e5f59577a7b0613bc37645025d834284790aa6a3f |
| /home/misbahul45/.config/opencode/skills/todolife-project-router/SKILL.md | todolife-project-router | 437 | strict YAML + required fields valid | 5d1932ae095acf90fe5088c1f9111301fd7bd22115f7643aecaf2a21cafcf5e0 |
| /home/misbahul45/.config/opencode/skills/todolife-schedule-auditor/SKILL.md | todolife-schedule-auditor | 624 | strict YAML + required fields valid | 0b59973f40a7416e6f3276e87a596c6c11f57fde7fb0ca306ff30adea936d66a |
| /home/misbahul45/.config/opencode/skills/transcribe/SKILL.md | transcribe | 711 | strict YAML + required fields valid | 96adbbf92d3aa150af94bb492cc159b903ad519872412ed68adcd287b74d5087 |
| /home/misbahul45/.config/opencode/skills/xninetzy-academic-safety.xninetzy.bak.disabled/SKILL.md | xninetzy-academic-safety.xninetzy.bak.disabled | 3629 | backup/disabled; missing-frontmatter | e5b3aeee8595bf94eeb426b82af7b3fc140e33bf73e8875b415d3900d6624e8f |
| /home/misbahul45/.config/opencode/skills/xninetzy-academic-safety/SKILL.md | xninetzy-academic-safety | 167 | strict YAML + required fields valid | 96f4ccb1922421efd581fde5e6ad362848221045fa2908f3f7d98275f0a03a13 |
| /home/misbahul45/.config/opencode/skills/xninetzy-artifact-orchestrator.xninetzy.bak.disabled/SKILL.md | xninetzy-artifact-orchestrator.xninetzy.bak.disabled | 5678 | backup/disabled; missing-frontmatter | 65eb4e912103b8056e350021b3172b1844dfd1f0b81a48b788c6db9786e9047f |
| /home/misbahul45/.config/opencode/skills/xninetzy-artifact-orchestrator/SKILL.md | xninetzy-artifact-orchestrator | 4770 | strict YAML + required fields valid | 4c059137a0f329f6a141ec92ad564271ade05543e25cadb34bf7519131066b2e |
| /home/misbahul45/.config/opencode/skills/xninetzy-assignment-orchestrator.xninetzy.bak.disabled/SKILL.md | xninetzy-assignment-orchestrator.xninetzy.bak.disabled | 5490 | backup/disabled; missing-frontmatter | 13055f451c7662987250e9cab41235133b147659e4248ae7a0961c387dd474ca |
| /home/misbahul45/.config/opencode/skills/xninetzy-assignment-orchestrator/SKILL.md | xninetzy-assignment-orchestrator | 2324 | strict YAML + required fields valid | 0d8f60558d89d55953725c48e0f49f48cd566134e3891cd3f988f6ff5b7871ed |
| /home/misbahul45/.config/opencode/skills/xninetzy-cyber-campus.xninetzy.bak.disabled/SKILL.md | xninetzy-cyber-campus.xninetzy.bak.disabled | 1272 | backup/disabled; missing-frontmatter | 7ef30e3ea35306f7405abbde51aca51b8c169731acce7c91513d385e29c01b52 |
| /home/misbahul45/.config/opencode/skills/xninetzy-cyber-campus/SKILL.md | xninetzy-cyber-campus | 332 | strict YAML + required fields valid | 8727fa4ef27cbf07d47b9b74f4b5552284a95a64c5b8b6e7c35cffeaf6ab69c2 |
| /home/misbahul45/.config/opencode/skills/xninetzy-deep-research.xninetzy.bak.disabled/SKILL.md | xninetzy-deep-research.xninetzy.bak.disabled | 1658 | backup/disabled; missing-frontmatter | e38910f121421332691fbfdeb6e350794d0e1d8e33ded819cafe456b903721b5 |
| /home/misbahul45/.config/opencode/skills/xninetzy-deep-research/SKILL.md | xninetzy-deep-research | 2950 | strict YAML + required fields valid | 309e1e4c9f9b9ba118b420a5d0f475f7ad3514dfa841a398b1c84cdac76e0565 |
| /home/misbahul45/.config/opencode/skills/xninetzy-hebat.xninetzy.bak.disabled/SKILL.md | xninetzy-hebat.xninetzy.bak.disabled | 3625 | backup/disabled; missing-frontmatter | 33e3edcfee27c9c923db466a546f35e9e451b71ae6a740a78adb06139d72d208 |
| /home/misbahul45/.config/opencode/skills/xninetzy-hebat/SKILL.md | xninetzy-hebat | 206 | strict YAML + required fields valid | 64ef561eb8d342d2353927ff293facc98e5483c1c4114427f2ffaa7f08931c95 |
| /home/misbahul45/.config/opencode/skills/xninetzy-krs.xninetzy.bak.disabled/SKILL.md | xninetzy-krs | 1124 | backup/disabled; strict YAML + required fields valid | aa7396b780783eb3eb80230d2f490329abaa933d9c377cbbf4c0ac9461184d9f |
| /home/misbahul45/.config/opencode/skills/xninetzy-krs/SKILL.md | xninetzy-krs | 1107 | strict YAML + required fields valid | 4e66af0dbbb6574413feac817232d18b2b529ae16c52477d64a47a5b8982381b |
| /home/misbahul45/.config/opencode/skills/xninetzy-learning-coach.xninetzy.bak.disabled/SKILL.md | xninetzy-learning-coach.xninetzy.bak.disabled | 4006 | backup/disabled; missing-frontmatter | b6119510e2dfd610f764a153cbdd0a7c08edb0193b44349e8f945db2881eb693 |
| /home/misbahul45/.config/opencode/skills/xninetzy-learning-coach/SKILL.md | xninetzy-learning-coach | 2950 | strict YAML + required fields valid | 8eeb680bc0c0cd0cd82398056f416558ff92bc46d5b56e786964e189a279381d |
| /home/misbahul45/.config/opencode/skills/xninetzy-mcp-lightning/SKILL.md | xninetzy-mcp-lightning | 3118 | strict YAML + required fields valid | 09434f191a4243a790b53e0903c2ece94b7735432acb55e93d265ed1c45b10bf |
| /home/misbahul45/.config/opencode/skills/xninetzy-memory.xninetzy.bak.disabled/SKILL.md | xninetzy-memory.xninetzy.bak.disabled | 3599 | backup/disabled; missing-frontmatter | a6c702670e6d87854db770ca126c7fcf88989365319ec1f28c75a62ce92e30c1 |
| /home/misbahul45/.config/opencode/skills/xninetzy-memory/SKILL.md | xninetzy-memory | 2314 | strict YAML + required fields valid | 67f3d1c7e98e0595f5a60784b54ee02618cb7a23d558b30d9c7113df574ced2f |
| /home/misbahul45/.config/opencode/skills/xninetzy-obsidian-orchestra.xninetzy.bak.disabled/SKILL.md | xninetzy-obsidian-orchestra.xninetzy.bak.disabled | 5150 | backup/disabled; missing-frontmatter | 40dc1e3760ea85c503d30637f918169c5c7e38a631ab99739605d3067d63e92b |
| /home/misbahul45/.config/opencode/skills/xninetzy-obsidian-orchestra/SKILL.md | xninetzy-obsidian-orchestra | 740 | strict YAML + required fields valid | d6aef8eb83eaef01931bf7b9e8ad04c1ded48ae4f65ebf50aa5157d9785ef81a |
| /home/misbahul45/.config/opencode/skills/xninetzy-os/SKILL.md | xninetzy-os | 2540 | strict YAML + required fields valid | e970b659487fb645993877ffcfe667170d64a515c2c2151d3538059757223dd8 |
| /home/misbahul45/.config/opencode/skills/xninetzy-research-memory.xninetzy.bak.disabled/SKILL.md | xninetzy-research-memory.xninetzy.bak.disabled | 4073 | backup/disabled; missing-frontmatter | 20dfc995d7368b4c11533aa0fed2b4c647218e2a4787dccf2807145eb21a422e |
| /home/misbahul45/.config/opencode/skills/xninetzy-research-memory/SKILL.md | xninetzy-research-memory | 2744 | strict YAML + required fields valid | 28c43f838498c66ee2a34efe8583120f057a625cfb57bd0633e4b87324357fee |
| /home/misbahul45/.config/opencode/skills/xninetzy-security-testing/SKILL.md | xninetzy-security-testing | 8235 | strict YAML + required fields valid | 6865264159a3e39202908113351aeff5b5697b21d674b413a7b3105973025a61 |
| /home/misbahul45/.config/opencode/skills/xninetzy-uacc.xninetzy.bak.disabled/SKILL.md | xninetzy-uacc.xninetzy.bak.disabled | 3483 | backup/disabled; missing-frontmatter | 9f05eba857a66f184f857c06667ed2891456fe199decf58b5fd09331a6e6997c |
| /home/misbahul45/.config/opencode/skills/xninetzy-uacc/SKILL.md | xninetzy-uacc | 2687 | strict YAML + required fields valid | c11f65fca46863d827faacb4fe941f541e153dc6afaafb13ab60164b8b28214a |
| /home/misbahul45/.config/opencode/skills/xninetzy-web-analysis/SKILL.md | xninetzy-web-analysis | 4695 | strict YAML + required fields valid | cd086b5e085cd074ab5ec66bbe7a4ed46907b09a3c4813ad812a8cad4b1846f7 |
### shared

| Path | Name | Tokens | Syntax status | SHA-256 |
|---|---|---|---|---|
| /home/misbahul45/.agents/skills/academic-editor/SKILL.md | academic-editor | 388 | strict YAML + required fields valid | 635f73179fcbb3d6636bc1dc519695550e822e0875717ae50eb11582f9ac33ff |
| /home/misbahul45/.agents/skills/academic-writer/SKILL.md | academic-writer | 404 | strict YAML + required fields valid | 161a3dcd84f25ea63252764a3faa7c82c5e1c89556b9336fa217953d314aaa13 |
| /home/misbahul45/.agents/skills/anti-slop/SKILL.md | anti-slop | 426 | strict YAML + required fields valid | a5137a98751d747285cf8728ed7af6969eae676a1cea07009405e9ee5a841361 |
| /home/misbahul45/.agents/skills/api-security/SKILL.md | api-security | 5764 | strict YAML + required fields valid | 1203063191b9b69c04760429adb7a4c7f6f28cdb0f01c0a4c947c570f7d531c9 |
| /home/misbahul45/.agents/skills/architecture-analysis/SKILL.md | architecture-analysis | 5446 | strict YAML + required fields valid | 17244f125e7e9004004352d32c2282141aa2ba4c0db35085434ad149b5e69a62 |
| /home/misbahul45/.agents/skills/argument-coherence/SKILL.md | argument-coherence | 970 | strict YAML + required fields valid | c2c2eef4a2b1188e65f3fff3f5ae721e498d59be6641b4b06c20b965e226148a |
| /home/misbahul45/.agents/skills/arkcli-agent/SKILL.md | arkcli-agent | 2925 | strict YAML + required fields valid | 61d4f8a8d4972d7aad0077e23da95e85e4aa64e23d8ca8477f4f9341fe29268a |
| /home/misbahul45/.agents/skills/arkcli-api-explorer/SKILL.md | arkcli-api-explorer | 1650 | strict YAML + required fields valid | f98c55d64c6537e9d685ddb3f2cba8693e6f4a616e04350a0e94bb075fbf2f07 |
| /home/misbahul45/.agents/skills/arkcli-auth/SKILL.md | arkcli-auth | 1361 | strict YAML + required fields valid | 55438901d16b9db7602d6746a05a8ce93a68ad62f4217758bea79a4fd573e91b |
| /home/misbahul45/.agents/skills/arkcli-billing/SKILL.md | arkcli-billing | 2680 | strict YAML + required fields valid | 2a22e741820ae9922bc3147da2b246ee446ae80e798b0f3fbfab5d1086af3e58 |
| /home/misbahul45/.agents/skills/arkcli-chat/SKILL.md | arkcli-chat | 2690 | strict YAML + required fields valid | c2623a814f8d7c0dc056dc27e85a8ff60049bbe6284cf21797efe8d48d655f3a |
| /home/misbahul45/.agents/skills/arkcli-config/SKILL.md | arkcli-config | 2245 | strict YAML + required fields valid | c7a0a208cd313cf2685764d3d5fbacc8795aca36550dc5080c8d0fd710fc999a |
| /home/misbahul45/.agents/skills/arkcli-connect/SKILL.md | arkcli-connect | 1841 | strict YAML + required fields valid | fc22cc62593486e43fd5ad668ee82220a579a065151db2ec451b917bed3310f7 |
| /home/misbahul45/.agents/skills/arkcli-custommodel/SKILL.md | arkcli-custommodel | 3587 | strict YAML + required fields valid | a3bc4baae305022e278467fae8c981959a8ee3bb9f674318fd0cef91e9514deb |
| /home/misbahul45/.agents/skills/arkcli-datasets/SKILL.md | arkcli-datasets | 859 | strict YAML + required fields valid | e26a6e0436177ec39c0a7a566723f7c8955027caf430e84ba56677fbca958ce9 |
| /home/misbahul45/.agents/skills/arkcli-deploy/SKILL.md | arkcli-deploy | 2211 | strict YAML + required fields valid | 4676351726365e842b64f5a24029bbc1da1752dfd54a2775844bcf9972cf1de0 |
| /home/misbahul45/.agents/skills/arkcli-doctor/SKILL.md | arkcli-doctor | 4433 | strict YAML + required fields valid | 3ed1b518572e8b8d81e85da3c7907967fae305d835a1eeff496ae0bc19203947 |
| /home/misbahul45/.agents/skills/arkcli-gen/SKILL.md | arkcli-gen | 3886 | strict YAML + required fields valid | 7289c636e853ddfa4fcab508375cdb3fa85eebca0e26913bc4b676ac316eb596 |
| /home/misbahul45/.agents/skills/arkcli-helper/SKILL.md | arkcli-helper | 1903 | strict YAML + required fields valid | d03683009a249395a5aacf3c2bcf04f062deedfe28ad9abd9279f423688b1e46 |
| /home/misbahul45/.agents/skills/arkcli-iam/SKILL.md | arkcli-iam | 601 | strict YAML + required fields valid | ed15bc290bd35c3dd5ef6495a2f5c7b1fe50515b420847772f175042cd7f8dbe |
| /home/misbahul45/.agents/skills/arkcli-infer-endpoint/SKILL.md | arkcli-infer-endpoint | 1607 | strict YAML + required fields valid | a42376322e5693ee1c926d9210b685ab75d97b1678474415c1e6956d2e3bd326 |
| /home/misbahul45/.agents/skills/arkcli-models/SKILL.md | arkcli-models | 5578 | strict YAML + required fields valid | 93b56da3c0a2ec86eba6b6f7b1cd1ab9ce590c3a6277e556cae18be7e36c39b1 |
| /home/misbahul45/.agents/skills/arkcli-onboard/SKILL.md | arkcli-onboard | 1513 | strict YAML + required fields valid | ec065aee469d6eadb19629d891646dd6c8a11ae2056e912abde9a5f1b4730115 |
| /home/misbahul45/.agents/skills/arkcli-plans/SKILL.md | arkcli-plans | 3103 | strict YAML + required fields valid | feafb57f9aacefc5aab98e311f22a36cfa86122379c7d3424a4deac4d7a614ed |
| /home/misbahul45/.agents/skills/arkcli-pricing/SKILL.md | arkcli-pricing | 2581 | strict YAML + required fields valid | d1277394760cbe9d0d0dca55ea7a348b4705c89bf75aa5aa8dcd1d54607c77bb |
| /home/misbahul45/.agents/skills/arkcli-profile/SKILL.md | arkcli-profile | 1260 | strict YAML + required fields valid | 12cea1aca8978ce65702570b4cd55c3be7e972ffe6d8555440f442d5ab3a3063 |
| /home/misbahul45/.agents/skills/arkcli-resources/SKILL.md | arkcli-resources | 2120 | strict YAML + required fields valid | b774ff8d80e38b03c45b5288166ae852487bccfb4d9c6060d263d0ba10c8af27 |
| /home/misbahul45/.agents/skills/arkcli-shared/SKILL.md | arkcli-shared | 1870 | strict YAML + required fields valid | de4b74c46feedbd2c15908357bc034ff920b42fce95a87da8a566552d9e1a45c |
| /home/misbahul45/.agents/skills/arkcli-train-finetune/SKILL.md | arkcli-train-finetune | 2216 | strict YAML + required fields valid | c21fa94d7ca09e4093eee9c93fdac894da22c6c9806db4dbc0a2e68f6ed572db |
| /home/misbahul45/.agents/skills/arkcli-understand/SKILL.md | arkcli-understand | 2544 | strict YAML + required fields valid | bfdd2f1aea38096421e82b71b4cea42e591b315f0675eedcf755768cdd046ea1 |
| /home/misbahul45/.agents/skills/arkcli-usage/SKILL.md | arkcli-usage | 3112 | strict YAML + required fields valid | e5803a26c0762d4d8ef2ddc055015fe502b1a417c4640d3f0e6abc924b15a0b8 |
| /home/misbahul45/.agents/skills/benchmark-analysis/SKILL.md | benchmark-analysis | 539 | strict YAML + required fields valid | aca8329463885331581fbfc26face5d4b342e41c67d77cf8898a622a7c631b32 |
| /home/misbahul45/.agents/skills/business-writer/SKILL.md | business-writer | 398 | strict YAML + required fields valid | b09b31698d699599837beebc4c07382eca4f05f466ce9bffb5e31358d8215904 |
| /home/misbahul45/.agents/skills/career/alternative-titles/SKILL.md | alternative-titles | 288 | strict YAML + required fields valid | c2a60507cdd95a5aa4d196fbcbd70fb42b1a03dc270b9bba1a753d0baf12baf8 |
| /home/misbahul45/.agents/skills/career/application-tracking/SKILL.md | application-tracking | 314 | strict YAML + required fields valid | 07566e6753d4586d4a2626290228a21d6a03258e41a1d015239b0e60389121b1 |
| /home/misbahul45/.agents/skills/career/company-research/SKILL.md | company-research | 382 | strict YAML + required fields valid | e86e906d82b6376eb87c85ee3100f82ea5b163e0314719284773997c810fef91 |
| /home/misbahul45/.agents/skills/career/company-search/SKILL.md | company-search | 312 | strict YAML + required fields valid | f0012d6fffafd7d554d196b9506c121497c5d311c6f991e6bcadd809bb980354 |
| /home/misbahul45/.agents/skills/career/cv-analysis/SKILL.md | cv-analysis | 393 | strict YAML + required fields valid | 14b129e35c78b117f8722ae2e94f5d17912dc57bd353341ce299d6cde97a8edd |
| /home/misbahul45/.agents/skills/career/extract-requirements/SKILL.md | extract-requirements | 291 | strict YAML + required fields valid | cb57c75aa69097ef688bd913b923de16fa0dfb6ce576bf10fd45fec1176fd7b4 |
| /home/misbahul45/.agents/skills/career/hidden-jobs/SKILL.md | hidden-jobs | 325 | strict YAML + required fields valid | c0f91e7cf101e79dc44d46af004828bcf8e93801c58ba981e4d9c6ece3d2c91b |
| /home/misbahul45/.agents/skills/career/internship-discovery/SKILL.md | internship-discovery | 405 | strict YAML + required fields valid | 77f18c4d791b4aa5cf34e699486e1a4406782a4ba997fa3d4c690a041ce01699 |
| /home/misbahul45/.agents/skills/career/interview-prep/SKILL.md | interview-prep | 386 | ScannerError | 66485ca3ef5f7761c39f0123bf1cbc75ae605a8c01e87a8817682756510860bf |
| /home/misbahul45/.agents/skills/career/job-discovery/SKILL.md | job-discovery | 477 | strict YAML + required fields valid | cc29eaac41ca80ca92f85d6fb7124e2835a9194a75e29acd585cc0c286d4e701 |
| /home/misbahul45/.agents/skills/career/job-matching/SKILL.md | job-matching | 405 | strict YAML + required fields valid | b1549fdef652bae132d8cf55c139c744de5f1570c9f51ed36ef9a769fae408ed |
| /home/misbahul45/.agents/skills/career/job-monitoring/SKILL.md | job-monitoring | 344 | strict YAML + required fields valid | f3c2d90125b9682d7c9d17241bed4489ee8411b5f36efece629283a0dfa594e1 |
| /home/misbahul45/.agents/skills/career/job-risk-analysis/SKILL.md | job-risk-analysis | 372 | strict YAML + required fields valid | e02ab3bbdf7b58a216ba00322b445cb53759174de905179b929322f38de5a260 |
| /home/misbahul45/.agents/skills/career/job-search/SKILL.md | job-search | 438 | strict YAML + required fields valid | 719a1c086bef4702fe3738ce612d20282e4740e12da2db344652546526a50263 |
| /home/misbahul45/.agents/skills/career/market-skill-trend/SKILL.md | market-skill-trend | 408 | strict YAML + required fields valid | 65fdc6acdf13e80033f271d249383b27588b654d465b9518097c4bd25c50eb6a |
| /home/misbahul45/.agents/skills/career/resume-tailoring/SKILL.md | resume-tailoring | 374 | strict YAML + required fields valid | 68237fe3762724f959b8e33a0fc061d3901d6328603905ca8a76a7163fd47228 |
| /home/misbahul45/.agents/skills/career/salary-analysis/SKILL.md | salary-analysis | 386 | strict YAML + required fields valid | 927f1db77aa1174279fc4a486fcc1b951dc63dd7f0f05daf49fa9c47557292ef |
| /home/misbahul45/.agents/skills/career/similar-jobs/SKILL.md | similar-jobs | 302 | strict YAML + required fields valid | 9c1f579ef6130d492f2b91bf0b5fda2c3ceb43979fa3cd26601cff3041815627 |
| /home/misbahul45/.agents/skills/career/skill-gap/SKILL.md | skill-gap | 428 | strict YAML + required fields valid | 1d9477eab81534aae106d8af9bbd5461b9fbcaad3c006f1ef6cb5273631cccc7 |
| /home/misbahul45/.agents/skills/citation-validation/SKILL.md | citation-validation | 941 | strict YAML + required fields valid | 0af168b02c3e0ded78271854eb7c062b08751a5c1cf2718a53cee9b46c64ed6f |
| /home/misbahul45/.agents/skills/claim-lattice/SKILL.md | claim-lattice | 1544 | strict YAML + required fields valid | 8d73475d60e26163f8d6e07dd49fbd26ecacce1c0586dd61b590e5fc6f0cdec2 |
| /home/misbahul45/.agents/skills/cli-creator/SKILL.md | cli-creator | 7186 | strict YAML + required fields valid | f37263afb9a0c66d6d85e316fbf258e1e248965b10de1edfe6fe747b4ef3f249 |
| /home/misbahul45/.agents/skills/code-review/SKILL.md | code-review | 7082 | strict YAML + required fields valid | 0e5958e3571783a8cce19cef8a12df25c7db082d76cbf9cae5f59678ece446d0 |
| /home/misbahul45/.agents/skills/competition-proposal/SKILL.md | competition-proposal | 402 | strict YAML + required fields valid | 58cfa8fc400ffd527a52b364d04a4b607b1eb10e93a5bfb1f0bb172a9aafc3a4 |
| /home/misbahul45/.agents/skills/consultant-challenge/SKILL.md | consultant-challenge | 392 | strict YAML + required fields valid | 8257e6a72604473201a131081ce520661fe3a5fa65e67238fe9f650963472acd |
| /home/misbahul45/.agents/skills/consultant/SKILL.md | consultant | 417 | strict YAML + required fields valid | 38a1ec7e0f8b8d42307160bd4d9488f912dcf7c14c205f7ae1386631fea37604 |
| /home/misbahul45/.agents/skills/consulting-pptx-skill/SKILL.md | consulting-pptx-skill | 3232 | strict YAML + required fields valid | 973c838db1e44f364f6695ef86e8f90a74504aee1ba10914f96b0d1a84295a5b |
| /home/misbahul45/.agents/skills/consulting-pptx/SKILL.md | consulting-pptx | 1013 | strict YAML + required fields valid | 913fa711c0349746d5cb69f3f4bcfb16e53a8679e5fb3abecc952a0551904c05 |
| /home/misbahul45/.agents/skills/context-engineering/SKILL.md | context-engineering | 7177 | strict YAML + required fields valid | c1a810f0796bbfbefeba3b119a54f7581ccfdeb74a7c80eb256933528f8dfc92 |
| /home/misbahul45/.agents/skills/contradiction-hunter/SKILL.md | contradiction-hunter | 468 | strict YAML + required fields valid | 0675c5460eaf7233141035c55fd28f9962f648f75590e1da17a805c8c0cd2820 |
| /home/misbahul45/.agents/skills/cyber-campus/SKILL.md | cyber-campus | 5777 | strict YAML + required fields valid | 2f9baf88354828c1fabdc1c7fc1b052c3be60c1aed17b9a0dd02a25b9a95b287 |
| /home/misbahul45/.agents/skills/data-analysis/SKILL.md | data-analysis | 610 | strict YAML + required fields valid | 788437361517076801a2be07f4b059bf5d1bd21b6f2175b17153c2a32c71b1ac |
| /home/misbahul45/.agents/skills/debugging/SKILL.md | debugging | 6561 | strict YAML + required fields valid | 2d22d97f0e5d8b1c4e699582ac2f66cfdfe81b4bae6f79346ec9b3f4e4f8bea8 |
| /home/misbahul45/.agents/skills/define-goal/SKILL.md | define-goal | 7059 | strict YAML + required fields valid | 68531b47ba2806e2be94c76850516d413681981c9d9097092c5f94b6f13e3d60 |
| /home/misbahul45/.agents/skills/dependency-audit/SKILL.md | dependency-audit | 8361 | strict YAML + required fields valid | 24ae5c89d692de565643aa79f72e1723dafb627fe38ce301a95510700a763821 |
| /home/misbahul45/.agents/skills/doc-coauthoring/SKILL.md | doc-coauthoring | 3289 | strict YAML + required fields valid | 2e47d78846faeea4a56e9809c52700087a15a2155a3f293a3efbaded81398ef4 |
| /home/misbahul45/.agents/skills/docx/SKILL.md | docx | 1773 | strict YAML + required fields valid | 8017469ea95fb7d28225c62daf8e2f3492a7b516fc64c18c28977cbf8980b7fe |
| /home/misbahul45/.agents/skills/evidence-grader/SKILL.md | evidence-grader | 463 | strict YAML + required fields valid | 02fdf8320773cfd6d05fb52e0aa9aa6b6a7e0a98370b152bb48a8e0a910a5394 |
| /home/misbahul45/.agents/skills/evidence-synthesis/SKILL.md | evidence-synthesis | 752 | strict YAML + required fields valid | 57e0f526fea50430d3faf7ff82b395837cd776c0403922473ac2e31c1ccaeb18 |
| /home/misbahul45/.agents/skills/exam_qa/SKILL.md | exam_qa | 435 | strict YAML + required fields valid | 4b73517232d23453550801daf41eff49ddd217512094a193344dffdd12b3199b |
| /home/misbahul45/.agents/skills/executive-writer/SKILL.md | executive-writer | 411 | strict YAML + required fields valid | 10b2aab99ef39184f446f8356508f6d5e584688e65642e727c2b0dea26411a12 |
| /home/misbahul45/.agents/skills/find-skills/SKILL.md | find-skills | 1291 | strict YAML + required fields valid | c00eeea0e13e74fe4a9d84ba0a8542205a1b736d65f13134fe1a6647eb14976f |
| /home/misbahul45/.agents/skills/frontend-design/SKILL.md | frontend-design | 1924 | strict YAML + required fields valid | d91970639e9f5c37682ac7ab60094d35f1c7c1f38d731bd56396563aee10c1d3 |
| /home/misbahul45/.agents/skills/gh-fix-ci/SKILL.md | gh-fix-ci | 892 | strict YAML + required fields valid | 66ffd7fd69abc96527d8cde3920490eaff1b686ce29152ab97e0f577c47f11a6 |
| /home/misbahul45/.agents/skills/google-agents-cli-adk-code/SKILL.md | google-agents-cli-adk-code | 748 | strict YAML + required fields valid | 744a359d57ccaa68a7b48bfc2f0b773de84bb5bcac0af07ce28a46b6d6c61832 |
| /home/misbahul45/.agents/skills/google-agents-cli-deploy/SKILL.md | google-agents-cli-deploy | 5498 | strict YAML + required fields valid | 7823ac5dfbca07b7e123d81eeded289b207a7bc2b903de94fb238b432c62d789 |
| /home/misbahul45/.agents/skills/google-agents-cli-eval/SKILL.md | google-agents-cli-eval | 6173 | strict YAML + required fields valid | 8427a75ec62eb174042cd297623f7d79f0e31fc8e84510efc2854ab58e33f5e4 |
| /home/misbahul45/.agents/skills/google-agents-cli-observability/SKILL.md | google-agents-cli-observability | 2277 | strict YAML + required fields valid | 47c688d8a645f2ca2d82fd7d842dcca53051ea3726f55ed300a025395a351105 |
| /home/misbahul45/.agents/skills/google-agents-cli-publish/SKILL.md | google-agents-cli-publish | 2231 | strict YAML + required fields valid | e3096f10bbeb696a97ddb9210ebfd3f21bfcf18706302fee919c7ff629c29cc3 |
| /home/misbahul45/.agents/skills/google-agents-cli-scaffold/SKILL.md | google-agents-cli-scaffold | 2671 | strict YAML + required fields valid | faf87b632abda32c250a0521cb2222e61579749ff1aae291cc72c9bee4a60866 |
| /home/misbahul45/.agents/skills/google-agents-cli-workflow/SKILL.md | google-agents-cli-workflow | 5250 | strict YAML + required fields valid | 32daccab4e0aeb49fd628b9bca1dcb167207f7d2649b8ae78fd0e19a85d69a22 |
| /home/misbahul45/.agents/skills/grant-proposal/SKILL.md | grant-proposal | 402 | strict YAML + required fields valid | 5b796c40ab5b92481bf2956d74bf58fb5e0bc206cb48d4cbb5cfca663b8e3eac |
| /home/misbahul45/.agents/skills/graph-rag/SKILL.md | graph-rag | 8913 | strict YAML + required fields valid | fd294179bdad92ad091af0a082add852b2d27186c413f3809e26c6dbe22b184a |
| /home/misbahul45/.agents/skills/hebat-academic/SKILL.md | hebat-academic | 4028 | strict YAML + required fields valid | b0d3c305b9e05cfebaf91fcb265bb0346a4e15f0a0a668a6ead6773e3d440ffd |
| /home/misbahul45/.agents/skills/hebat-assignment/SKILL.md | hebat-assignment | 5080 | strict YAML + required fields valid | de2b27b3fd35d7e334186d6700d6df13e9cfccf6523db1b2b1d8db167955ccaf |
| /home/misbahul45/.agents/skills/it-learning/SKILL.md | it-learning | 1534 | strict YAML + required fields valid | c24d46654a7742ed263102be08fdb3047d87a5d49a5ad407c081608a2039806b |
| /home/misbahul45/.agents/skills/jupyter-notebook/SKILL.md | jupyter-notebook | 934 | strict YAML + required fields valid | 735c09068509503cffd764e6d32be58e734cc9e7c6f14aab1c26c394c7d6c7d1 |
| /home/misbahul45/.agents/skills/life-management/SKILL.md | life-management | 1648 | strict YAML + required fields valid | 7bc57608409c31342cfc45808b23ba3f5454dabd147a082b100604326b59d8be |
| /home/misbahul45/.agents/skills/literature-review-writer/SKILL.md | literature-review-writer | 411 | strict YAML + required fields valid | f6e66ff67f10024908902aae063a44de4446cafeb7c8f1f641888702bcf5a083 |
| /home/misbahul45/.agents/skills/literature-review/SKILL.md | literature-review | 653 | strict YAML + required fields valid | 61b457849ad8f32c32ab71cac908a419db82efc68c6012550612ae22043d6abb |
| /home/misbahul45/.agents/skills/mcp-builder/SKILL.md | mcp-builder | 1922 | strict YAML + required fields valid | 0f4592dcb53cf2b5d6b7febee6b4152018b565551a1c29e3c612f57b218ab295 |
| /home/misbahul45/.agents/skills/mcp-development/SKILL.md | mcp-development | 1848 | strict YAML + required fields valid | 26a3e1e376efd2012197f0322020bdf1f3acc3ad1f9a86688cf74c6622cb3601 |
| /home/misbahul45/.agents/skills/mcp-discovery/SKILL.md | mcp-discovery | 584 | strict YAML + required fields valid | b3c02d2151a328628fba78015d17142509d66fa50a663a4338694e604d0418fb |
| /home/misbahul45/.agents/skills/memory-chat/SKILL.md | memory-chat | 1753 | strict YAML + required fields valid | b7bbfabb0be019fbbc8ce5e7c078589725c47c3d6f540fd3a1ee27e2dda1cb1f |
| /home/misbahul45/.agents/skills/memory-management/SKILL.md | memory-management | 1552 | strict YAML + required fields valid | 620a86e9039bf2445b632b07a263698ba1dab2353c9610a2ffd024bc7dc27daf |
| /home/misbahul45/.agents/skills/methodology-rater/SKILL.md | methodology-rater | 1772 | strict YAML + required fields valid | b0f99aadd4f3d3346691824c99e78ebd55464d6da339b11480de3ff55afeda4e |
| /home/misbahul45/.agents/skills/mmx-cli/SKILL.md | mmx-cli | 2839 | strict YAML + required fields valid | 1adee4231e1c37cc0d09bd890cebacc1d62a6a69f059cb78fd5654480b8a0ee2 |
| /home/misbahul45/.agents/skills/mmx-cli/h3-video/SKILL.md | mmx-h3-video | 2410 | strict YAML + required fields valid | 5ddf4209eb4cdcf6b88a011285bbfc7e470d544856b53d27269524bc6390c5a1 |
| /home/misbahul45/.agents/skills/multi-agent-orchestration/SKILL.md | multi-agent-orchestration | 1556 | strict YAML + required fields valid | 101ef2b7e5951f717ce19a15899b90a13e8da00b723578d3efe6a2065effdf7f |
| /home/misbahul45/.agents/skills/obsidian-knowledge/SKILL.md | obsidian-knowledge | 350 | strict YAML + required fields valid | a6b9c662d9c715b6958c8441001e10497647b876c964788dcbdafdab6a1f157d |
| /home/misbahul45/.agents/skills/obsidian-ops/SKILL.md | obsidian-ops | 417 | strict YAML + required fields valid | 4d50723d3ad14fdcebd4bda81f57964895f9d75a19ce229d5bd60c500f8cfd1f |
| /home/misbahul45/.agents/skills/outline-builder/SKILL.md | outline-builder | 1664 | strict YAML + required fields valid | 532830f1a9d223ca116ab84646251b9c355518b70702e9788c2abce9216236c0 |
| /home/misbahul45/.agents/skills/paper-analysis/SKILL.md | paper-analysis | 759 | strict YAML + required fields valid | 829c8cb275d335108ef7cec63ef2a035e254ddcec49ee2a9579ed3c82eb86277 |
| /home/misbahul45/.agents/skills/paper-review/SKILL.md | paper-review | 398 | strict YAML + required fields valid | e875f7550fba9a6d26bd788c0398a32b14edc87c3c15e2cf08787ca4895d6920 |
| /home/misbahul45/.agents/skills/pdf/SKILL.md | pdf | 2079 | strict YAML + required fields valid | 9f78b8359fbd4943ad260a7a1e436e5a96503406d6c34e99f69223d647d85b9c |
| /home/misbahul45/.agents/skills/personal-os/SKILL.md | personal-os | 520 | strict YAML + required fields valid | 29a76589da05e4162a439ad14d45f32cb229ec9d7b17b2812fe192a08ac31571 |
| /home/misbahul45/.agents/skills/playwright-interactive/SKILL.md | playwright-interactive | 6801 | strict YAML + required fields valid | 2529dd902005f12c89b65aed648cd22af4d4e7ba7e991159f73e2db740c48ff5 |
| /home/misbahul45/.agents/skills/playwright-mcp-workflows/SKILL.md | playwright-mcp-workflows | 1116 | strict YAML + required fields valid | 66410f6a3a31664ba7d4318ada23a8632adffe79a67cce9b6d1e5d3e9e59ae0f |
| /home/misbahul45/.agents/skills/playwright/SKILL.md | playwright | 946 | strict YAML + required fields valid | d5693079440907bd2d8dde943ee096212dc276c90437512ce4ed802aa2b0f976 |
| /home/misbahul45/.agents/skills/pptx-skills/.claude/skills/markitdown/SKILL.md | markitdown | 1035 | strict YAML + required fields valid | cf2e206be8baf949216a70b321d8b124b9ca534d36cf6a10c1cc47c9a95749a9 |
| /home/misbahul45/.agents/skills/pptx-skills/.claude/skills/slide-analyze/SKILL.md | slide-analyze | 1399 | strict YAML + required fields valid | 32d4cdadce4d654673c07516b2f8d8cb979231840926d2cb495bc991c024d734 |
| /home/misbahul45/.agents/skills/pptx-skills/.claude/skills/slide-edit/SKILL.md | slide-edit | 1348 | strict YAML + required fields valid | b2847845e2819ff84a7c045ed07ee4c60aef73845166622592e79214b10bef6a |
| /home/misbahul45/.agents/skills/pptx-skills/.claude/skills/slide-generate/SKILL.md | slide-generate | 1724 | strict YAML + required fields valid | ad87f1a97a1645a0daa223358f79bdbfbb9c4dad0459cb04146fc34cf189143b |
| /home/misbahul45/.agents/skills/pptx-skills/SKILL.md | pptx-skills | 559 | strict YAML + required fields valid | 9ca9e518127ee10a6db771b51b3aa007f8a93230ee85e1626006b9e7126bb34d |
| /home/misbahul45/.agents/skills/pptx/SKILL.md | pptx | 5349 | strict YAML + required fields valid | a7ff03e2c85b636f55232a6b1555f5dd90216b7a1a359ab289d8364e6acbc6a0 |
| /home/misbahul45/.agents/skills/process-engineering-providers/SKILL.md | process-engineering-providers | 685 | strict YAML + required fields valid | f512f27a4b69425ffd9b06e331a4e02c7aad05e62226aae057e2c1e5d7b750be |
| /home/misbahul45/.agents/skills/process_engineering/SKILL.md | process_engineering | 404 | strict YAML + required fields valid | 0ce5856b9c39cc200d95006c350f2d2b3e32af58a8a762057f8934439c18fe4b |
| /home/misbahul45/.agents/skills/professional-editor/SKILL.md | professional-editor | 412 | strict YAML + required fields valid | 91dadc5ef8e9dad1ea7b6c59cef392dc5d46d7a90fc21a85d1f9d2f759c3c7bc |
| /home/misbahul45/.agents/skills/professional-writer/SKILL.md | professional-writer | 518 | strict YAML + required fields valid | 0cef09ebe9890e2889f8f45abdb426ac589881f4568cde0e9931a740a3390c87 |
| /home/misbahul45/.agents/skills/proposal-red-team/SKILL.md | proposal-red-team | 401 | strict YAML + required fields valid | 5ecd43d84f83af62bca442f3a3257ec9c9e762f73d467df641d5461fbc147f88 |
| /home/misbahul45/.agents/skills/proposal-writer/SKILL.md | proposal-writer | 405 | strict YAML + required fields valid | f1c2cd635efbaecde5323f7d40fe5153a70eb12eb9fea52dad00871afedacd4d |
| /home/misbahul45/.agents/skills/reasoning-critic/SKILL.md | reasoning-critic | 448 | strict YAML + required fields valid | 996ce829eb0a203333b9a380be8619b3dc5072f9cad407c2a5cac53f719cd8b2 |
| /home/misbahul45/.agents/skills/reasoning-orchestrator/SKILL.md | reasoning-orchestrator | 853 | strict YAML + required fields valid | 9a3cc386c644131aba52d69da0061c3b307e2d9dd54097236208b7a50949d4e6 |
| /home/misbahul45/.agents/skills/reasoning-strategy-learner/SKILL.md | reasoning-strategy-learner | 399 | strict YAML + required fields valid | e0fd1c7a44c7ee5c13cb5d969f83e00a8ba1cb432e7ae5a27b379985e489fbb8 |
| /home/misbahul45/.agents/skills/regression-analysis/SKILL.md | regression-analysis | 511 | strict YAML + required fields valid | fcfceb0b2f2f7bd9fa285be712bbf66e6ebbdf08df4387dbe7d2cdd6642d1df6 |
| /home/misbahul45/.agents/skills/repo-context-packaging/SKILL.md | repo-context-packaging | 1363 | strict YAML + required fields valid | 9a3ed45936de1f4f5ad2538001df05142c96b39a2f1e9fedfb1dceb79cf8cd2d |
| /home/misbahul45/.agents/skills/requirement-coverage/SKILL.md | requirement-coverage | 830 | strict YAML + required fields valid | 449f78b8aa67903f106bb1aea1f80014cd2ae2aafe26c3fddbc94657d922dc95 |
| /home/misbahul45/.agents/skills/research-critic/SKILL.md | research-critic | 578 | strict YAML + required fields valid | a7d6bb1b788696de37ade981a008c3cbfd79c6c5384e5d20357ffbda074ef7fa |
| /home/misbahul45/.agents/skills/research-paper-writer/SKILL.md | research-paper-writer | 404 | strict YAML + required fields valid | e6b5af989654d9833aec12e8665e04332b2b61fd4f13ba8df36359bc1fa0f9bf |
| /home/misbahul45/.agents/skills/research-planner/SKILL.md | research-planner | 616 | strict YAML + required fields valid | e6888e8bf01b3643076263088752f32708337f65bc37ada73fc7fc2f54a9f542 |
| /home/misbahul45/.agents/skills/research-proposal/SKILL.md | research-proposal | 401 | strict YAML + required fields valid | 291ba454e45c1724c366884f1a9e5d482408276c1617ab551babeb052813b99e |
| /home/misbahul45/.agents/skills/research/SKILL.md | research | 2637 | strict YAML + required fields valid | 3d8afc8a7fd31151ba4c34aa94b127c0aea4b514ab923c95e66e4429c4cec7cf |
| /home/misbahul45/.agents/skills/reverse-engineer-anything/SKILL.md | reverse-engineer-anything | 5090 | strict YAML + required fields valid | fbcd39d6abe803cf7aa49c1880815bc8e22ba2af87a23681944f687bb7629eb1 |
| /home/misbahul45/.agents/skills/scientific-paper-writer/SKILL.md | scientific-paper-writer | 400 | strict YAML + required fields valid | bb7903316aca315ffc7bf2ce745e6323ce8dcc38d2ca274ea492499f444c9080 |
| /home/misbahul45/.agents/skills/scoring-rubric/SKILL.md | scoring-rubric | 1617 | strict YAML + required fields valid | c452e27b3f276b244604de9b4bd2f2690f214b06ee1da657601128004bb62eb8 |
| /home/misbahul45/.agents/skills/screenshot/SKILL.md | screenshot | 1915 | strict YAML + required fields valid | e54300fdc7c9c6a683263dabb4cf5a4967ec77d343faed439bc6586caea87c36 |
| /home/misbahul45/.agents/skills/secret-audit/SKILL.md | secret-audit | 637 | strict YAML + required fields valid | 2d1b5df0f753154a7efc3a01a36b932196cf6d1ff5ed24a5346236a8f1ba5bb9 |
| /home/misbahul45/.agents/skills/security-best-practices/SKILL.md | security-best-practices | 1663 | strict YAML + required fields valid | 2e52ba9dfd39bb0988ac01642177e0441aeedbcb1f5ca85e88ad3764cb6ac7c4 |
| /home/misbahul45/.agents/skills/security-ownership-map/SKILL.md | security-ownership-map | 2083 | strict YAML + required fields valid | 7dc70ffb10bd9de513ad329d6acccccf3e262175affcf9f73e307bb7bc7449f7 |
| /home/misbahul45/.agents/skills/security-research/SKILL.md | security-research | 588 | strict YAML + required fields valid | 82cf566002604da2d2ff4ea63b71ed6975171985009c2a8978207f26adad6ffd |
| /home/misbahul45/.agents/skills/security-review/SKILL.md | security-review | 1459 | strict YAML + required fields valid | 558471609233989414617ab4195568ffe41d2f86fd6e9db0d867faab722a37a6 |
| /home/misbahul45/.agents/skills/security-threat-model/SKILL.md | security-threat-model | 1112 | strict YAML + required fields valid | 6f891ea91133e99a4391e5edf1fbdbde59a4445efaf43a85d3c61b35be0797de |
| /home/misbahul45/.agents/skills/self-improvement/analyze-failure/SKILL.md | analyze-failure | 579 | strict YAML + required fields valid | 05c16aa3a0336ffd1cbc01ff26fec6945623d8a6896e96b8018ea698eb07a795 |
| /home/misbahul45/.agents/skills/self-improvement/benchmark-model/SKILL.md | benchmark-model | 466 | strict YAML + required fields valid | 420bbe8a2c9061f11625458c6774fdb642afb669f03b3b43e8d5b47c5d094fa0 |
| /home/misbahul45/.agents/skills/self-improvement/compare-models/SKILL.md | compare-models | 369 | strict YAML + required fields valid | 1ac7b84d79899518ee02218015321fffa445a5d76c9337192221ca967a902ec9 |
| /home/misbahul45/.agents/skills/self-improvement/evaluate-agent/SKILL.md | evaluate-agent | 557 | strict YAML + required fields valid | f346651079f7334019bbf1c0444d827110fd019a03171abb9fdb43dec5e377e7 |
| /home/misbahul45/.agents/skills/self-improvement/experience-mining/SKILL.md | experience-mining | 482 | strict YAML + required fields valid | 5c22654451e6753d8efc47acb2764514ef180f8245480ed8f9f0b3f7da83a7f4 |
| /home/misbahul45/.agents/skills/self-improvement/generate-training-data/SKILL.md | generate-training-data | 504 | strict YAML + required fields valid | d29442cdfcfa28487d19cc3fd7e2735c3d81a06642b284ff303de6870b680439 |
| /home/misbahul45/.agents/skills/self-improvement/memory-consolidation/SKILL.md | memory-consolidation | 474 | strict YAML + required fields valid | e134b0b1581c9931d818ae4469bdbd7c368f8149d924f9e0ef4bec4429354816 |
| /home/misbahul45/.agents/skills/self-improvement/optimize-agent-policy/SKILL.md | optimize-agent-policy | 458 | strict YAML + required fields valid | 81ad1ede449a82695a25d6df8121c0f0cee680e5f057ea3488f4b6162501decc |
| /home/misbahul45/.agents/skills/self-improvement/optimize-prompt/SKILL.md | optimize-prompt | 570 | strict YAML + required fields valid | c724892b249e184edceebd33247bce9e7cb9e62b3ba6591d170e6b51fd3919e2 |
| /home/misbahul45/.agents/skills/self-improvement/optimize-rag/SKILL.md | optimize-rag | 456 | strict YAML + required fields valid | 65f46fb1ae87b62b2c7f90763cd1a286187b2b52f39a958977bb8c05d9d90b73 |
| /home/misbahul45/.agents/skills/self-improvement/optimize-tool-routing/SKILL.md | optimize-tool-routing | 437 | strict YAML + required fields valid | b6dbdad1b278e692650240260a7bb6b5964190ec20bec9b2d48826e4c07befab |
| /home/misbahul45/.agents/skills/self-improvement/promote-model/SKILL.md | promote-model | 415 | strict YAML + required fields valid | 7d7a221f8cabc35609ab074d90448de3eca85bc351284c2a4526f20fbe562edb |
| /home/misbahul45/.agents/skills/self-improvement/reflect-trajectory/SKILL.md | reflect-trajectory | 413 | strict YAML + required fields valid | 9322fb7e70195c8c51f01c5bd92621d5504bf981b81e8e464fdd23b2680df072 |
| /home/misbahul45/.agents/skills/self-improvement/rollback-model/SKILL.md | rollback-model | 365 | strict YAML + required fields valid | a4d20b81ed662fbbeaf56dd60decee0a04a985a407a022d7a588566fd8c62505 |
| /home/misbahul45/.agents/skills/self-improvement/run-dpo/SKILL.md | run-dpo | 423 | strict YAML + required fields valid | e438734237b91f978c045e29d008e9fc0a8efcd5c50340a09bab3345a73a2f38 |
| /home/misbahul45/.agents/skills/self-improvement/run-grpo/SKILL.md | run-grpo | 425 | strict YAML + required fields valid | 0c8671dae1f95838cc03438e2c4c40f955046951038766265594e1bf66b60108 |
| /home/misbahul45/.agents/skills/self-improvement/run-sft/SKILL.md | run-sft | 472 | strict YAML + required fields valid | 7b61bbab613d1ffbc43d666163de8832c8f513391245b17bc17cd11f1e5b8f54 |
| /home/misbahul45/.agents/skills/skill-creator/SKILL.md | skill-creator | 7322 | strict YAML + required fields valid | dcd4803e61e913e6fc27294184cd3a71f09f5e924ff20c8a9a20173e7b3c2bcf |
| /home/misbahul45/.agents/skills/skill-improvement-opportunity-logger/SKILL.md | skill-improvement-opportunity-logger | 1367 | strict YAML + required fields valid | 11492b62b6ee9378656f7029af5bdb3523ea6788b7a7ec2944958c62703d3498 |
| /home/misbahul45/.agents/skills/skill-security-review/SKILL.md | skill-security-review | 2308 | strict YAML + required fields valid | 6a49956a987021f607ef78329e8411f3803ab49ce2357507ed20d374d39fee38 |
| /home/misbahul45/.agents/skills/source-evaluation/SKILL.md | source-evaluation | 1160 | strict YAML + required fields valid | 2fbd99894bdc75a244575e131f9b874ed0c6d6b0b352ceab5b941d4d7c4233c0 |
| /home/misbahul45/.agents/skills/source-selector/SKILL.md | source-selector | 762 | strict YAML + required fields valid | a785130364164de43c66477ed8f224dd53c4b4339548c1441b15eb9c3054f49d |
| /home/misbahul45/.agents/skills/structured-project-execution/SKILL.md | structured-project-execution | 1418 | strict YAML + required fields valid | 5ae09343de69ba97fc987d7ce4ba0709544af57dc72781b11df2566123913f30 |
| /home/misbahul45/.agents/skills/submission-readiness/SKILL.md | submission-readiness | 387 | strict YAML + required fields valid | ff725129fc7f5fe6628b16c25d12e38579b29dd6effea48ec78bccbd95044b91 |
| /home/misbahul45/.agents/skills/tableau-workbook-builder/SKILL.md | tableau-workbook-builder | 2993 | strict YAML + required fields valid | 181c454b0aed5e4793060c69494e46d80ec29c4d7a51215a2cd7ca77f99d18d1 |
| /home/misbahul45/.agents/skills/tdd-workflow/SKILL.md | tdd-workflow | 1264 | strict YAML + required fields valid | 95aa311c529cd9eda0d50522db0b8d43850ef221fd31f146b68993c11af63863 |
| /home/misbahul45/.agents/skills/technical-content-writer/SKILL.md | technical-content-writer | 411 | strict YAML + required fields valid | 43032b121aba05b1a1c4b260bdb9513d2310af01a0df457109c3b7fa5fe23e75 |
| /home/misbahul45/.agents/skills/terminology-bank/SKILL.md | terminology-bank | 1144 | strict YAML + required fields valid | 58e192f1600fa36e1c63d7a2d8e80394140eef2d1afe2e094d32fdbf1c70ce89 |
| /home/misbahul45/.agents/skills/transcribe/SKILL.md | transcribe | 711 | strict YAML + required fields valid | 96adbbf92d3aa150af94bb492cc159b903ad519872412ed68adcd287b74d5087 |
| /home/misbahul45/.agents/skills/vercel-react-best-practices/SKILL.md | vercel-react-best-practices | 1756 | strict YAML + required fields valid | 71ed7794962fa6e803ee83030517b5b93a9f70fbfeb431ec4535c5480a8d8355 |
| /home/misbahul45/.agents/skills/web-design-guidelines/SKILL.md | web-design-guidelines | 268 | strict YAML + required fields valid | f4647ca866a3accf763777f83e7682954f0187cd6bea7eea0399796652414e8f |
| /home/misbahul45/.agents/skills/webapp-testing/SKILL.md | webapp-testing | 881 | strict YAML + required fields valid | 51b7349e77ec63b7744a6f63647e7566a0b4d2e301121cc10e8c2113af6556a2 |
| /home/misbahul45/.agents/skills/xlsx/SKILL.md | xlsx | 2135 | strict YAML + required fields valid | 6712b39718fe815054abca9c3ee72f989613e6f771c8a5c58f30a65a6c905622 |
| /home/misbahul45/.agents/skills/xninetzy-academic-safety/SKILL.md | xninetzy-academic-safety | 167 | strict YAML + required fields valid | 96f4ccb1922421efd581fde5e6ad362848221045fa2908f3f7d98275f0a03a13 |
| /home/misbahul45/.agents/skills/xninetzy-artifact-orchestrator/SKILL.md | xninetzy-artifact-orchestrator | 4770 | strict YAML + required fields valid | 4c059137a0f329f6a141ec92ad564271ade05543e25cadb34bf7519131066b2e |
| /home/misbahul45/.agents/skills/xninetzy-assignment-orchestrator/SKILL.md | xninetzy-assignment-orchestrator | 2324 | strict YAML + required fields valid | 0d8f60558d89d55953725c48e0f49f48cd566134e3891cd3f988f6ff5b7871ed |
| /home/misbahul45/.agents/skills/xninetzy-cyber-campus/SKILL.md | xninetzy-cyber-campus | 332 | strict YAML + required fields valid | 8727fa4ef27cbf07d47b9b74f4b5552284a95a64c5b8b6e7c35cffeaf6ab69c2 |
| /home/misbahul45/.agents/skills/xninetzy-deep-research/SKILL.md | xninetzy-deep-research | 2950 | strict YAML + required fields valid | 309e1e4c9f9b9ba118b420a5d0f475f7ad3514dfa841a398b1c84cdac76e0565 |
| /home/misbahul45/.agents/skills/xninetzy-hebat/SKILL.md | xninetzy-hebat | 206 | strict YAML + required fields valid | 64ef561eb8d342d2353927ff293facc98e5483c1c4114427f2ffaa7f08931c95 |
| /home/misbahul45/.agents/skills/xninetzy-krs/SKILL.md | xninetzy-krs | 1107 | strict YAML + required fields valid | 4e66af0dbbb6574413feac817232d18b2b529ae16c52477d64a47a5b8982381b |
| /home/misbahul45/.agents/skills/xninetzy-learning-coach/SKILL.md | xninetzy-learning-coach | 2950 | strict YAML + required fields valid | 8eeb680bc0c0cd0cd82398056f416558ff92bc46d5b56e786964e189a279381d |
| /home/misbahul45/.agents/skills/xninetzy-mcp-lightning/SKILL.md | xninetzy-mcp-lightning | 3118 | strict YAML + required fields valid | 09434f191a4243a790b53e0903c2ece94b7735432acb55e93d265ed1c45b10bf |
| /home/misbahul45/.agents/skills/xninetzy-memory/SKILL.md | xninetzy-memory | 2314 | strict YAML + required fields valid | 67f3d1c7e98e0595f5a60784b54ee02618cb7a23d558b30d9c7113df574ced2f |
| /home/misbahul45/.agents/skills/xninetzy-obsidian-orchestra/SKILL.md | xninetzy-obsidian-orchestra | 740 | strict YAML + required fields valid | d6aef8eb83eaef01931bf7b9e8ad04c1ded48ae4f65ebf50aa5157d9785ef81a |
| /home/misbahul45/.agents/skills/xninetzy-os/SKILL.md | xninetzy-os | 2540 | strict YAML + required fields valid | e970b659487fb645993877ffcfe667170d64a515c2c2151d3538059757223dd8 |
| /home/misbahul45/.agents/skills/xninetzy-research-memory/SKILL.md | xninetzy-research-memory | 2744 | strict YAML + required fields valid | 28c43f838498c66ee2a34efe8583120f057a625cfb57bd0633e4b87324357fee |
| /home/misbahul45/.agents/skills/xninetzy-security-testing/SKILL.md | xninetzy-security-testing | 8235 | strict YAML + required fields valid | 6865264159a3e39202908113351aeff5b5697b21d674b413a7b3105973025a61 |
| /home/misbahul45/.agents/skills/xninetzy-uacc/SKILL.md | xninetzy-uacc | 2687 | strict YAML + required fields valid | c11f65fca46863d827faacb4fe941f541e153dc6afaafb13ab60164b8b28214a |
| /home/misbahul45/.agents/skills/xninetzy-web-analysis/SKILL.md | xninetzy-web-analysis | 4695 | strict YAML + required fields valid | cd086b5e085cd074ab5ec66bbe7a4ed46907b09a3c4813ad812a8cad4b1846f7 |
### codex_plugins

| Path | Name | Tokens | Syntax status | SHA-256 |
|---|---|---|---|---|
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/figma/17.0.0/skills/figma-code-connect/SKILL.md | figma-code-connect | 6482 | strict YAML + required fields valid | 87af3996edb167d6aa3c044cb1bbb6a0d8e2d631c731bb896b1e1e8669640415 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/figma/17.0.0/skills/figma-code-workflows/SKILL.md | figma-code-workflows | 921 | strict YAML + required fields valid | ac69b52d96a5d1b1832be9f0be99c221cfd861f8aad2260a0508386229982c7c |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/figma/17.0.0/skills/figma-create-new-file/SKILL.md | figma-create-new-file | 462 | strict YAML + required fields valid | bb7bc48c487f0ad7e738c23d0685bad5ec0bbbca8f5b5bb6295dc0666cc9ddf1 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/figma/17.0.0/skills/figma-design-to-code/SKILL.md | figma-design-to-code | 806 | strict YAML + required fields valid | a6e852421e4db72260b2ca641929b1f84684e5b067aead081e35111f5b5feee4 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/figma/17.0.0/skills/figma-generate-design/SKILL.md | figma-generate-design | 8807 | strict YAML + required fields valid | 4dcebaa45ca3942d0b90f5847cedbff62e040fb381ca643cac79700978402705 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/figma/17.0.0/skills/figma-generate-diagram/SKILL.md | figma-generate-diagram | 2360 | strict YAML + required fields valid | 7297638dbf2130d1b37bfd85df65d290a4dd0b11a11b54abafcf7d07565922b5 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/figma/17.0.0/skills/figma-generate-library/SKILL.md | figma-generate-library | 5383 | strict YAML + required fields valid | 65ee2aa9fd565b47bf627b773986f3c121616825d01c9ded78ea314532f5d10c |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/figma/17.0.0/skills/figma-generative-plugins/SKILL.md | figma-generative-plugins | 1012 | strict YAML + required fields valid | b97eb184a1f6b6545f3b8266a4d1a1e29304888904db7daed2864b9fd036b124 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/figma/17.0.0/skills/figma-implement-motion/SKILL.md | figma-implement-motion | 5436 | strict YAML + required fields valid | 5995716f9453c86f6cd68831e2a586a3bcce1989e0b86eb41717b5b78d8350e7 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/figma/17.0.0/skills/figma-shaders/SKILL.md | figma-shaders | 1213 | strict YAML + required fields valid | c7e34c5a4eb316cfe84768cb419fe71b3ce840b29561ecd0f90eb402a72e1adf |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/figma/17.0.0/skills/figma-spec/SKILL.md | figma-spec | 1486 | strict YAML + required fields valid | cc2d6fa7a8b14983ba1dd3f537036cf7f266e86cc5d5e847b48b96df6592e746 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/figma/17.0.0/skills/figma-swiftui/SKILL.md | figma-swiftui | 964 | strict YAML + required fields valid | 868c4defe2c0854f5a3e27594d3fa0f20347c86a9b15d103483b7488bfa8affe |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/figma/17.0.0/skills/figma-use-figjam/SKILL.md | figma-use-figjam | 1599 | strict YAML + required fields valid | 8d566444a1aaf31c122682a5fbe3d6f14c6a844a4e05164cda3de872752cea24 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/figma/17.0.0/skills/figma-use-motion/SKILL.md | figma-use-motion | 2010 | strict YAML + required fields valid | 399193f13154f9d515d5265f301aeaf39b9ff14ef6d67b50123b657ef0dfacc0 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/figma/17.0.0/skills/figma-use-slides/SKILL.md | figma-use-slides | 4942 | strict YAML + required fields valid | 0a69a65e686dcc223581afb409a4d31cf318716e2c65cc9c926839a8737e71a4 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/figma/17.0.0/skills/figma-use/SKILL.md | figma-use | 8418 | strict YAML + required fields valid | abffccc5eddba774690364e274db83a3d4b9b7bf9aa5e73e9c4517e2f352c94a |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-analytics-dashboard/SKILL.md | artifact-template-analytics-dashboard | 277 | strict YAML + required fields valid | cf5360fd8b197673bb237c52c603c97fa319c875c3dfa2cd8efff52d4422f513 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-business-review/SKILL.md | artifact-template-business-review | 276 | strict YAML + required fields valid | 27721fc1d67d1b41949caa75ac8f94f81952ff124406878af6524047929e60d2 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-design-report/SKILL.md | artifact-template-design-report | 272 | strict YAML + required fields valid | 563722f53854e606f8a9f87e37e72d7ef70a22d46d5836b8e4d6abfb1b79e9e0 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-experiment-analysis/SKILL.md | artifact-template-experiment-analysis | 273 | strict YAML + required fields valid | 0b05effc47df0a14f8e0c3e3597e6722224747435546385d38a2cae279bd20b9 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-financial-budget/SKILL.md | artifact-template-financial-budget | 280 | strict YAML + required fields valid | c0b6b7a62a15597aaf2b1ec679e21da48f533b756127f0aef957cdfe9f3da738 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-investment-committee-memo/SKILL.md | artifact-template-investment-committee-memo | 281 | strict YAML + required fields valid | 68abd08cfe5e073e3c446a3f675f44c5bf98f57434dba679e8acd8a763379a8b |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-legal-memorandum/SKILL.md | artifact-template-legal-memorandum | 280 | strict YAML + required fields valid | 51fb9d21baf6119c4ccb1903638a6bac0e859210de63460fffa7025d52e997e0 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-market-trends-report/SKILL.md | artifact-template-market-trends-report | 278 | strict YAML + required fields valid | d58d019b89cb6f292ac3ab991d561489eef477ff53ce05fb024a0c936f5af26a |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-minimal-letterhead/SKILL.md | artifact-template-minimal-letterhead | 280 | strict YAML + required fields valid | 880ef094d4d0c89a7bde5ce9bbe4086625c186651e9e6efc8ba8bdd7cc77f9d5 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-operating-calendar/SKILL.md | artifact-template-operating-calendar | 277 | strict YAML + required fields valid | 33bb660791a0b9a21628a42c34934932220203b6aabd84e98cb1b45327d0384c |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-operating-review/SKILL.md | artifact-template-operating-review | 277 | strict YAML + required fields valid | 6d63c5cd025ffe936e7bab5db3023672bbaec26af55c2bb8b057d38c202c9c32 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-project-kickoff/SKILL.md | artifact-template-project-kickoff | 281 | strict YAML + required fields valid | aa893ebd89e7c8d1db4261d01cc2b1add35d78d00785871ccaaa5fc8db783ec9 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-project-tracker/SKILL.md | artifact-template-project-tracker | 283 | strict YAML + required fields valid | d97d5be20189b7f53dd269b6e1c5f694eaf53e5a72f6559fcb1578911b7cda82 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-sales-pipeline/SKILL.md | artifact-template-sales-pipeline | 280 | strict YAML + required fields valid | 15cfeeedf440021f16ed3f3ad8c7c1ef6d48898b9447741e223d2fb41cfc9800 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-simple-dark-mode/SKILL.md | artifact-template-simple-dark-mode | 278 | strict YAML + required fields valid | b7c8d0c05f75878b9bc21e56a57c41ec1aa29700aca0a24822be0f9f1bd53207 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-simple-light-mode/SKILL.md | artifact-template-simple-light-mode | 278 | strict YAML + required fields valid | 7c68430c6cf57b55b457d4735dbd1a46b889bef135a32222902dd0848b6e1752 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-strategy-memorandum/SKILL.md | artifact-template-strategy-memorandum | 278 | strict YAML + required fields valid | 51d7882ac94e8e57b323394825728c33925af878806e37277217c2dc12a912e5 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-system-design/SKILL.md | artifact-template-system-design | 274 | strict YAML + required fields valid | 87f7b7ed1b0d8410f5e5971cd7f7db9a4165e2f37069e97e52dbfb469b75a57c |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-team-alignment/SKILL.md | artifact-template-team-alignment | 279 | strict YAML + required fields valid | 26d7cafdcd1899a937b325c5d02ac57c162d45002153be33a934d35f81eb6110 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/openai-templates/0.1.1/skills/artifact-template-three-statement-forecast/SKILL.md | artifact-template-three-statement-forecast | 291 | strict YAML + required fields valid | 74f4a5cccec0107b861548b157e04c51d9b58ec13a990c86394b4c529b8ecf41 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/plugin-management/0.1.0/skills/plugin-management/SKILL.md | plugin-management | 585 | strict YAML + required fields valid | 653841cc21205269f08b0ce135891e1518dac616a766bcfb0b57d788d3f68b10 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/product-design/0.1.56/skills/audit/SKILL.md | audit | 2016 | strict YAML + required fields valid | 087f798c3fe02e91b4cca18cc0f42c358a4dc2c02ccf37a348b476fb19b64aa3 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/product-design/0.1.56/skills/design-qa/SKILL.md | design-qa | 2602 | strict YAML + required fields valid | 19303684c7c84e279f3582d784493a6f09d207d92a29e9b15b7056020bcf306e |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/product-design/0.1.56/skills/get-context/SKILL.md | get-context | 639 | strict YAML + required fields valid | 151267c873003b7b03715c0842ef798369420464844218492f732edd2f6f7fd1 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/product-design/0.1.56/skills/ideate/SKILL.md | ideate | 2631 | strict YAML + required fields valid | 649e8782ca93d5aece712964fae5be2b111cc3143577e1507b98df7f9d8e6bde |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/product-design/0.1.56/skills/image-to-code/SKILL.md | image-to-code | 2132 | strict YAML + required fields valid | 694b4102bc339e3038173f8063d83a19e08d2a2cfab1f2e478d6412870a61ff0 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/product-design/0.1.56/skills/index/SKILL.md | index | 2060 | strict YAML + required fields valid | 8e9916d9e5dc3b6a394bedcaa38cd9c8833a1f3b0c4538b75647cf9f62f779fc |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/product-design/0.1.56/skills/research/SKILL.md | research | 702 | strict YAML + required fields valid | bf824e72dd93941c8d591e4af13bb7e3a09380cd6ed7dd8c1f61a295648fa023 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/product-design/0.1.56/skills/share/SKILL.md | share | 494 | strict YAML + required fields valid | 19327c50a52f3b9e2ebfcef47d394d988bd6f4c64524c98f665d43bdf5f02c45 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/product-design/0.1.56/skills/url-to-code/SKILL.md | url-to-code | 1723 | strict YAML + required fields valid | 2624d0e2ec5f14ba2a4bf74fe05aaa23520b4fb76ca57973c9dadd54fd4b09d2 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/product-design/0.1.56/skills/user-context/SKILL.md | user-context | 1242 | strict YAML + required fields valid | 5690a7f99cf896970493f5d0bd7f35f62ab9cbe21744352acf84dc0ceea4194c |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/sites/1.1.4/skills/sites-remix/SKILL.md | sites-remix | 1376 | strict YAML + required fields valid | 34a249750d98e38f676fa391819593ab5c14e5f46f9137832a8c49180d47022d |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/sites/1.1.4/skills/sites/SKILL.md | sites | 2646 | strict YAML + required fields valid | f51bd813c224703a14eb2938cf813954cb546ed72392c842f834dee7dbc06ee6 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/work-pets/0.1.6/skills/create-pet/SKILL.md | create-pet | 3663 | strict YAML + required fields valid | 841354fb8116f8fdfd3b643b30828f5180196c594d3fed9b669b948b88892af1 |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/work-pets/0.1.6/skills/pets/SKILL.md | pets | 782 | strict YAML + required fields valid | 1bf5d45fd6a6390aab777229293fb05cef7cf898aac882f8955e40c378e52fcd |
| /home/misbahul45/.codex/plugins/cache/openai-curated-remote/work-pets/0.1.6/skills/update-pet/SKILL.md | update-pet | 922 | strict YAML + required fields valid | c63c98d67b6ad781a72a8f9837ba1fb5e2d2a8054a2562e4025890a97d8a0e67 |
### claude_plugins

| Path | Name | Tokens | Syntax status | SHA-256 |
|---|---|---|---|---|

## Validation coverage, limitations and next priorities

Representative tool-reference coverage exists in tests/governance/test_skill_tool_call_drift.py but regex matching only checks function-call syntax sharing a known prefix; metadata tool requirements and arbitrary prose references can remain unresolved. Required tool availability for every installed third-party skill is UNKNOWN; no plugin scripts or downloaded executables were run. Historical catalog counts are not reused as evidence.

P1: define scoped discovery for nested first-party skills, validate/reconcile their metadata without losing semantics, and evaluate multilingual intent routing. P1: gate skill eligibility on required tools and trust before ranking. P2: enforce the declared metadata context cap and measure actual runtime call sites. P2: regenerate canonical skill index and supported client parity. Existing duplicated legacy directories are preserved for compatibility assessment.

Files changed in this batch: the two skill tests described in PROMPT_CONFLICT_REPORT.md and these audit reports.14 focused tests pass; source runtime behavior and data are unchanged. No migration. Rollback only the reviewed file patch. This report is not a blanket security certification or a claim all installed skills are operational.
