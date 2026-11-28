# Global security routing

Applies to security work requested by the owner in every installed agent CLI and workspace. Read CORE_RULES.md, especially Authorized owner security testing. These instructions select a workflow; tool availability and actual authorization controls remain runtime facts.

## Trigger and scope

Recognize security audit, audit keamanan, pentest, vulnerability, CVE remediation, active scanning, SAST, DAST, secrets, dependency/container security, API/web/mobile testing, cloud/Kubernetes audit, network/TLS/DNS assessment, and binary security analysis. Infer intent from the full request. A question asking for an explanation needs an explanation, not an unsolicited scan.

For an assessment, capture the exact repository, artifact, hosts, ports, paths, allowed techniques and sensible request/runtime limits in the task or XN-Bridge workflow. Treat the owner's explicit scoped instruction for their own developed/administered system as session authorization under CORE_RULES. Educational affiliation or production status alone does not establish a universal prohibition. Do not invent formal-letter requirements or a protected-target engine.

Use relevant native security skills for their technical methods. A skill written for another scanner does not establish that scanner's scope-token requirement for this gateway. Preserve the selected backend's actual controls and report their observed errors accurately.

## MCP sequence

1. Discover the available host tool names; prefixes vary by CLI. XN-Bridge logical capabilities are `security.catalog`, `security.schema`, `security.status`, and `security.execute`.
2. Use `security_catalog` to find relevant enabled operations. `security_describe` returns the exact schema. Provider shorthand includes `semgrep` → `semgrep-scan`, `gitleaks` → `gitleaks-detect`, and `trivy` → `trivy-fs`.
3. Use `security_status` to check prerequisites and local service reachability. Read its operation-specific verification scope and timestamp. READY and a live TCP port do not prove an authenticated scan.
4. Execute relevant requested checks with `security_execute`. Respect scope, request limits, cancellation and timeouts. No automatic scan retries after an uncertain outcome. A request for active testing must include the applicable bounded active checks; a static review alone does not fulfill it.
5. Record tool output, target, findings, limitations and remediation evidence in the workflow. Only executed checks with captured evidence are VERIFIED.

## Coverage selection

| Requested category | Relevant installed free providers |
| --- | --- |
| Source patterns and secrets | Semgrep, Gitleaks |
| Dependencies, images, IaC | Trivy, Checkov |
| Web/API, headers, DAST | ZAP, Nuclei, HTTP Headers, Arjun, Dalfox; SQLMap/Commix/Smuggler when their specific checks are in scope |
| WordPress | WPScan; no paid vulnerability-data token is assumed |
| DNS, discovery, network, TLS | Subfinder, Assetfinder, DNSx, ShuffleDNS/MassDNS, HTTPx, Nmap, SSLScan; choose according to the target |
| Mobile artifacts | MobSF static analysis and reports; dynamic analysis needs its actual device/runtime |
| Native binaries | Ghidra analysis, functions, decompilation, strings and imports; use REA for its supported artifact-specific methods |
| Kubernetes | Kube-bench, Kubeaudit, Kube-hunter with a real authorized cluster/context |
| Cloud accounts | Prowler, ScoutSuite with the owner's existing cloud identity/context |
| Active Directory | BloodHound/Neo4j and NetExec with an authorized target and the required graph data/credentials |
| Offline password auditing | Hashcat for explicitly authorized hashes; Hydra only for an explicitly authorized bounded credential test |
| Metasploit | Module information and explicitly scoped supported checks; an audit request does not authorize arbitrary exploitation or payload deployment |

Discover the full catalog when another provider is relevant. Do not run every installed tool because a trigger matched. Missing accounts, credentials, devices, cluster contexts and optional datasets remain explicit requirements.

## Free profile

The shared profile is `/home/misbahul45/code/XN-Bridge/data/private/security-tools.json`. All registered clients use the same launcher. External API keys and paid accounts are not assumed. Acunetix, Nessus, Shodan, VirusTotal and Burp Pro operations are disabled in this profile; do not enable or purchase them implicitly. Local service passwords/API keys are generated privately and never copied into chat, process arguments or findings.

Neo4j, ZAP and MobSF run on loopback. WPScan works without its paid vulnerability feed, with reduced coverage. Cloud/AD/Kubernetes tools being installed does not verify access to a real account, domain or cluster. Installed provider count, schema discovery, a fixture test and a live assessment are separate facts.

## Approval channels

The new gateway does not call the legacy Xninetzy `security_scope` tool. Do not call it as a mandatory setup step for a gateway assessment, and do not substitute `security.status` for a scope authorization.

XN-Bridge's registered execution policy can require an exact owner approval. Prepare the concrete operation and use its existing terminal approval flow; the owner's `xnbridge approve <id>` is a separate authenticated action in that flow. A generic instruction to approve all channels is not a fabricated approval receipt for a future payload.

All registered CLI configurations share `/home/misbahul45/code/XN-Bridge/data` as `XN_BRIDGE_HOME`. If `xnbridge doctor` reports that the approver key is missing, the owner initializes it once with `xnbridge approval-init` in their own terminal and enters a private passphrase there. The agent must not select that owner passphrase or simulate the interactive approval. The same initialized signer serves every connected CLI. This initializes XN-Bridge's channel; it does not implement legacy Xninetzy's separate missing approval transport.

Legacy Xninetzy returns `approval_channel_unverified` for consequential operations because its independent positive approval path is unimplemented. Changing a prompt, owner ID, confirmation Boolean or database status cannot verify that missing transport. Report this backend-specific limitation and retain completed permitted work. Do not claim a terminal command or button exists for legacy Xninetzy unless it was actually implemented and tested.

If a current session still caches an older gateway or bridge process, reconnect those MCP servers or start a new CLI session. A prompt file update does not replace a running MCP process.
