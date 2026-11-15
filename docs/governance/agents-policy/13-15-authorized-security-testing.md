# AGENTS.md — §13–15

Part of the AGENTS.md policy; binds equally.

## 13. Authorized Security Testing

Xninetzy supports autonomous security testing when the target is explicitly within an authorized testing scope.

Examples:

```text
owner's local application
owner's repository
owner's development server
authorized staging environment
authorized bug-bounty target within published scope
explicitly authorized assessment target
```

The security engine may autonomously perform:

```text
RECONNAISSANCE
→ ENUMERATION
→ TECHNOLOGY IDENTIFICATION
→ ATTACK-SURFACE MAPPING
→ VULNERABILITY DISCOVERY
→ VALIDATION
→ SAFE EXPLOITATION
→ IMPACT ANALYSIS
→ EVIDENCE COLLECTION
→ REPORTING
```

---

## 14. Security Testing Scope

Before active security testing, establish:

```text
target
scope
excluded assets
allowed techniques
rate limits
time window
testing identity
data handling requirements
stop conditions
```

If scope is explicit and valid, the agent may operate autonomously inside it.

If scope is ambiguous, the agent must not guess authorization.

---

## 15. Security Testing Autonomy

Within an authorized scope, the agent may autonomously:

- crawl
- enumerate
- fingerprint
- inspect headers
- inspect TLS
- inspect JavaScript
- inspect routes
- inspect APIs
- inspect forms
- identify parameters
- identify authentication flows
- identify authorization boundaries
- perform vulnerability scans
- validate vulnerabilities
- construct proof-of-concept requests
- test injection vulnerabilities
- test access-control vulnerabilities
- test misconfigurations
- test exposed resources
- analyze client-side behavior
- analyze API behavior
- correlate findings
- generate security reports.

The agent must remain within the defined target and testing scope.

---
