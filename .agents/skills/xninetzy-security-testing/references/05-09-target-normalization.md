# xninetzy-security-testing — §5–9

Contents: 5. Target Normalization; 6. DNS Rebinding Protection; 7. Authentication and Secrets; 8. MCP Security Layer; 9. Security Testing Layers

## 5. Target Normalization

Before any scanner runs:

### URL normalization

Normalize:

* scheme
* hostname
* lowercase hostname
* explicit port
* default port
* path
* trailing slash
* fragments
* percent encoding
* punycode
* userinfo

Reject:

```text
javascript:
data:
file:
ftp:
gopher:
file://
```

unless a separate explicitly authorized test profile supports them.

### DNS normalization

Resolve hostname and record:

```text
hostname
A records
AAAA records
CNAME chain
resolution timestamp
resolved IPs
```

The resolved addresses become part of the scan evidence.

If the hostname later resolves to an address outside the authorized scope:

```text
STOP
```

Do not automatically continue.

### Redirect normalization

Every HTTP redirect target must be checked against the ScopeManifest.

Allowed:

```text
scope.example.com
www.scope.example.com
api.scope.example.com
```

Blocked:

```text
attacker.example
169.254.169.254
localhost
10.0.0.1
```

A redirect never grants authorization to a new host.

---

## 6. DNS Rebinding Protection

Network scanners must defend against time-of-check/time-of-use target changes.

For each target:

1. Resolve.
2. Record resolved addresses.
3. Validate against scope.
4. Start scan.
5. Re-resolve at bounded checkpoints.
6. Compare resolution set.
7. Stop on unexpected transition.

Unexpected transition:

```text
allowed public IP
        ->
private IP
metadata IP
protected domain
out-of-scope IP
```

results in:

```text
SCOPE_DRIFT
```

---

## 7. Authentication and Secrets

Authenticated testing may be supported only through secure secret references.

Never accept raw credentials in normal prompt content.

Allowed model:

```yaml
auth:
  mode: secret_ref
  username_ref: secret://security/test-user
  session_cookie_ref: secret://security/staging-session
```

Disallowed model:

```text
username=admin
password=SuperSecret123
cookie=session=abcdef...
```

Secrets must be:

* injected into subprocess environment or isolated secret store
* excluded from stdout
* excluded from stderr
* redacted from reports
* redacted from debug output
* excluded from audit persistence
* excluded from model context whenever possible

Never print:

```text
Authorization: Bearer ...
Cookie: ...
Set-Cookie: ...
X-API-Key: ...
AWS_SECRET_ACCESS_KEY=...
```

Evidence should instead say:

```text
Authenticated request used.
Credential material intentionally redacted.
```

---

## 8. MCP Security Layer

Xninetzy itself is an MCP system and therefore the security layer must assess MCP-specific controls.

The MCP security model must be treated as a first-class domain.

MCP architecture separates host, client, and server responsibilities, while authorization and permissions are critical boundaries. Current MCP guidance also emphasizes that tool annotations are hints rather than hard security enforcement.

Test:

### Server authorization

* unauthenticated request
* expired token
* wrong issuer
* wrong audience
* wrong scope
* token for another user
* token for another server
* insufficient privilege
* revoked credential

### Tool authorization

For every protected tool:

```text
public?
authenticated?
role allowed?
scope allowed?
resource allowed?
environment allowed?
destructive capability?
```

### Capability exposure

Inventory:

```text
tools/list
resources/list
prompts/list
completion endpoints
sampling capability
elicitation capability
tasks/extensions
```

Check whether sensitive capability is exposed unnecessarily.

### Tool annotations

Treat:

```text
readOnlyHint
destructiveHint
idempotentHint
openWorldHint
```

as metadata rather than enforcement.

The server implementation itself must enforce behavior. MCP documentation explicitly warns that untrusted servers can misrepresent annotations.

### MCP-specific abuse classes

Detect:

```text
tool confusion
cross-tool privilege escalation
confused deputy
scope laundering
authorization boundary mismatch
resource URI traversal
unsafe remote resource retrieval
untrusted tool instructions
prompt injection via tool results
secret exfiltration paths
unexpected network egress
unsafe sampling permissions
cross-server context leakage
```

Resource URI inputs must be validated and sensitive resources must have access controls.

---

## 9. Security Testing Layers

The engine operates across these layers:

```text
L0 Governance / Scope
L1 Asset Discovery
L2 Network / Service Enumeration
L3 Web Surface Discovery
L4 HTTP Security
L5 API Security
L6 Authentication / Session
L7 Authorization
L8 Business-Logic Controls
L9 DAST
L10 SAST
L11 Dependency / SCA
L12 Secret Detection
L13 Container Security
L14 IaC Security
L15 Kubernetes Security
L16 Cloud Security
L17 TLS / Cryptography
L18 Mobile Security
L19 Supply Chain
L20 Correlation / Validation
L21 Regression / Continuous Security
```

---
