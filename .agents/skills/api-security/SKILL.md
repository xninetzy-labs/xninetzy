---
name: "api-security"
description: "Evidence-driven API security assessment for authorized HTTP, REST, GraphQL, MCP, WebSocket, and gRPC surfaces. Audits authentication, authorization, object/property/ function access, input validation, rate limiting, CORS, security headers, TLS, SSRF exposure, injection boundaries, resource exhaustion, API inventory drift, schema enforcement, business-logic controls, secret exposure, and trust boundaries. Use when an API, MCP tool, WebSocket route, gRPC method, authentication middleware, authorization policy, schema, CORS policy, rate limiter, security header, or trust boundary is added or changed, or when the operator requests an API security review. Never expands authorized scope, never bypasses authentication or human verification, never performs destructive testing, and never treats a scanner signal as a verified vulnerability without supporting evidence."

metadata:
author: "xninetzy"
owner: "misbahul45"
version: "2.0.0"
scope: "domain"
priority: "P1"
domain: "xninetzy.domains.security"
lifecycle: >
scope -> inventory -> classify -> map-controls -> model-trust ->
analyze -> validate -> correlate -> prioritize -> regress -> report

required_tools:

* security_api_inventory
* security_headers
* security_threat_model
* security_scope
* security_sast
* security_validate_finding
* lightning_record_action

optional_tools:

* repo_search
* repo_symbol
* repo_architecture
* hitl_request_approval
* os_inbox
* memory_security_store
* security_run_nuclei
* security_run_zap
* security_run_schemathesis
* security_dependency_scan
* security_attack_surface
* security_mcp_inventory

trigger_conditions:

* a new HTTP endpoint is added
* an existing HTTP endpoint changes
* a REST route changes
* an OpenAPI schema changes
* a GraphQL schema changes
* a gRPC service or method changes
* a WebSocket route changes
* an MCP server/tool/resource changes
* authentication middleware changes
* authorization middleware changes
* role or permission policy changes
* CORS policy changes
* CSP or security-header policy changes
* rate-limit policy changes
* request validation changes
* file-upload handling changes
* URL-fetching behavior changes
* trust boundaries change
* the operator asks whether an endpoint is secure
* the operator requests an API security review

prerequisites:

* explicit authorized scope for live probing
* route inventory, route table, OpenAPI, GraphQL schema, gRPC descriptor,
  MCP inventory, or equivalent endpoint source
* repository/source evidence when code-level analysis is requested
* test identity or secure credential reference when authenticated behavior is assessed

non_goals:

* credential brute force
* credential stuffing
* CAPTCHA bypass
* OTP bypass
* MFA bypass
* destructive testing
* production data modification
* unauthorized target discovery
* unrestricted fuzzing
* exploit weaponization

references:
core_security:
file: "../xninetzy-security-testing/SKILL.md"
use_when:
- scope
- authorization
- scanner execution
- evidence
- validation
- reporting
workflow:
file: "../xninetzy-security-testing/references/workflow.md"
use_when:
- live assessment
- scanner orchestration
- DAST
- API testing
- correlation
- regression
installation:
file: "../xninetzy-security-testing/references/install.md"
use_when:
- scanner availability
- installation
- runtime
- version compatibility
-----------------------

# api-security

API security assessment layer for HTTP, REST, GraphQL, MCP, WebSocket, and gRPC boundaries.

This skill complements:

```text
security-review
xninetzy-security-testing
security-threat-model
security-api-inventory
security-sast
```

The primary principle is:

> **Control presence is not control effectiveness.**

A middleware existing in source code does not prove that the endpoint is actually protected.
---


# 1. Security Model

Every API review must analyze:

```text
Asset
  ↓
Entry Point
  ↓
Identity
  ↓
Authorization Context
  ↓
Input
  ↓
Validation
  ↓
Business Logic
  ↓
Sensitive Sink
  ↓
External Dependency
  ↓
Response / State Change
```

The review must distinguish:

```text
PRESENT
EFFECTIVE
VERIFIED
UNKNOWN
```

---

# 2. Core Invariants

1. Scope must be established before live probing.
2. Every live target must belong to the authorized scope.
3. Schema evidence and runtime evidence must remain distinguishable.
4. Authentication presence does not prove authentication correctness.
5. Authorization middleware presence does not prove authorization correctness.
6. An HTTP `401` or `403` alone does not prove secure authorization.
7. CORS configuration does not replace authentication or authorization.
8. A security header is not automatically effective merely because it exists.
9. Rate-limit configuration does not prove an effective runtime limit.
10. Input validation configuration does not prove sink safety.
11. Scanner output is evidence, not final truth.
12. High-impact findings should be independently corroborated where feasible.
13. Unknown must not become safe merely because no scanner reported a finding.
14. Unknown must not become vulnerable merely because a scanner raised an alert.
15. No destructive request.
16. No credential attack.
17. No bypass of CAPTCHA, OTP, MFA, or anti-bot controls.
18. No scope expansion through redirects, DNS, API references, or imported schemas.
19. No secrets in findings, logs, or model output.
20. Every confirmed exploitable condition should generate a regression candidate.

---

# 3. Assessment Pipeline

```text
SCOPE
  ↓
INVENTORY
  ↓
PROTOCOL CLASSIFICATION
  ↓
AUTHENTICATION MAP
  ↓
AUTHORIZATION MAP
  ↓
INPUT / OUTPUT MAP
  ↓
RATE-LIMIT MAP
  ↓
HEADER / CORS MAP
  ↓
TRUST-BOUNDARY MAP
  ↓
THREAT MODEL
  ↓
STATIC ANALYSIS
  ↓
RUNTIME ANALYSIS
  ↓
CORRELATION
  ↓
SAFE VALIDATION
  ↓
RISK TRIAGE
  ↓
REGRESSION
  ↓
REPORT
```

---

# 4. Phase 0 — Scope

Use:

```text
security_scope
```

Required:

```text
target
protocol
environment
allowed methods
allowed paths
allowed identities
testing profile
rate budget
time budget
```

Example:

```yaml
scope:
  target: https://api.example.test
  environment: staging

  methods:
    - GET
    - HEAD
    - OPTIONS

  paths:
    - /api/*
    - /graphql

  profiles:
    - api-baseline
    - authorization

  limits:
    requests_per_second: 5
    concurrency: 5
```

Any live assessment outside the manifest is blocked.

---

# 5. Phase 1 — Inventory

Use:

```text
security_api_inventory
```

Accept inventory sources:

```text
route table
OpenAPI
GraphQL schema
protobuf/gRPC descriptors
MCP tool inventory
WebSocket route registry
source code
observed application calls
```

Normalize to:

```yaml
route:
  protocol:
  method:
  path:
  operation_id:
  authentication:
  authorization:
  input_schema:
  output_schema:
  rate_limit:
  security_headers:
  owner:
  source:
```

---

# 6. Protocol Classification

Every endpoint must be classified:

```text
HTTP
REST
GraphQL
WebSocket
gRPC
MCP
```

Then select protocol-specific controls.

```text
REST
 -> route + resource + method

GraphQL
 -> operation + resolver + object + field

WebSocket
 -> connection + message + event + channel

gRPC
 -> service + method + message + metadata

MCP
 -> server + capability + tool/resource + caller
```

---

# 7. API Surface Completeness

Compare multiple inventory sources:

```text
route table
      +
OpenAPI
      +
frontend/network calls
      +
source symbols
      +
runtime observations
```

Classify differences:

```text
DOCUMENTED_ONLY
IMPLEMENTED_ONLY
RUNTIME_ONLY
DEPRECATED
SHADOW_ENDPOINT
DRIFT
UNKNOWN
```

An undocumented live endpoint is a security finding candidate even when it is not obviously vulnerable.

---

# 8. Phase 2 — Authentication Map

For every protected operation identify:

```text
authentication mechanism
credential location
issuer
audience
token type
session type
expiration
refresh behavior
revocation
required scopes
```

Test, where authorized:

```text
anonymous
missing credential
invalid credential
expired credential
revoked credential
wrong audience
wrong issuer
insufficient scope
wrong authentication scheme
```

Do not test credential guessing.

---

# 9. Authentication Effectiveness

Model:

```text
Expected:
GET /api/profile
  requires authenticated user

Observed:
GET /api/profile
  anonymous -> 200
```

Finding:

```text
AUTHN_BYPASS
```

But:

```text
middleware_exists = true
```

is not enough to prove:

```text
authentication_effective = true
```

Evidence must come from actual enforcement or equivalent strong source evidence.

---

# 10. Phase 3 — Authorization Map

Build:

```yaml
authorization:
  actors:
    - anonymous
    - user
    - manager
    - admin

  resources:
    - user
    - project
    - document
    - invoice

  actions:
    - read
    - create
    - update
    - delete
```

Then derive expected policy.

---

# 11. Authorization Dimensions

Test:

```text
same-user
other-user
same-tenant
other-tenant
lower privilege
higher privilege
anonymous
expired identity
wrong scope
```

Also distinguish:

```text
object-level
property-level
function-level
tenant-level
field-level
workflow-level
```

---

# 12. IDOR / BOLA

A finding requires more than:

```text
object ID appears in URL
```

Required evidence:

```text
authorized principal
target object
authorization expectation
request
observed result
```

Example:

```text
User A
  ↓
GET /api/projects/123

Project 123 belongs to User B

Observed:
HTTP 200
resource returned

Expected:
HTTP 403
```

Finding:

```text
BROKEN_OBJECT_AUTHORIZATION
```

Never expose unrelated user's sensitive data in the report.

Use the smallest necessary proof.

---

# 13. Property-Level Authorization

Check whether clients can modify fields they are not authorized to control.

Example:

```json
{
  "name": "Project",
  "role": "admin",
  "ownerId": "..."
}
```

Ask:

```text
Which properties are client-controlled?
Which properties are server-controlled?
Which role may modify each field?
```

Test only safe fields/environment.

Potential class:

```text
MASS_ASSIGNMENT
BROKEN_PROPERTY_AUTHORIZATION
OVERPOSTING
```

---

# 14. Function-Level Authorization

Verify:

```text
ordinary user
    ->
admin function
```

and:

```text
anonymous
    ->
protected function
```

Examples:

```text
/admin/*
/manage/*
/internal/*
/billing/*
/users/:id/role
```

Do not confuse hidden frontend navigation with authorization.

The server must enforce authorization independently.

---

# 15. Tenant Isolation

For multi-tenant systems model:

```text
principal
    ↓
tenant
    ↓
resource
```

Test:

```text
tenant A -> tenant A resource
tenant A -> tenant B resource
tenant B -> tenant A resource
```

Check:

```text
read
write
list
search
export
aggregation
background jobs
file references
webhooks
```

Tenant isolation is a first-class control.

---

# 16. GraphQL Security

Inspect:

```text
schema
query
mutation
subscription
resolver
field
object
```

Check:

```text
field authorization
resolver authorization
nested object authorization
introspection policy
query depth
query complexity
alias abuse
batching
resource exhaustion
sensitive mutation access
```

A field hidden from documentation is not secure unless resolver enforcement exists.

---

# 17. WebSocket Security

Model:

```text
connection
  ↓
authentication
  ↓
channel
  ↓
message
  ↓
action
```

Check:

```text
authentication on connection
authorization per channel
authorization per message
origin policy
session expiration
reconnect behavior
tenant isolation
message validation
resource limits
subscription access
```

Do not assume connection authentication automatically authorizes every channel.

---

# 18. gRPC Security

Model:

```text
service
  ↓
method
  ↓
metadata
  ↓
identity
  ↓
authorization
```

Check:

```text
TLS
authentication metadata
authorization interceptor
method-level authorization
message validation
reflection exposure
resource limits
error leakage
```

Each sensitive RPC must be individually authorized.

---

# 19. MCP Security

For MCP:

```text
server
  ↓
capability
  ↓
tool/resource/prompt
  ↓
caller identity
  ↓
authorization
```

Check:

```text
tools/list
resources/list
prompts/list
tool authorization
resource authorization
scope propagation
tenant isolation
URI validation
annotation consistency
unexpected network access
secret exposure
cross-tool privilege escalation
```

An advertised tool capability is not proof that the capability is safely enforced.

---

# 20. MCP Tool Authorization Matrix

Example:

```yaml
actor:
  anonymous:
    tools:
      read_public: allow
      admin_action: deny

  user:
    tools:
      read_public: allow
      read_own_data: allow
      read_other_data: deny
      admin_action: deny

  admin:
    tools:
      admin_action: allow
```

Compare:

```text
expected authorization
       vs
observed behavior
```

---

# 21. Phase 4 — Input Validation

For each input:

```text
path
query
header
cookie
body
JSON
form
multipart
GraphQL argument
gRPC field
WebSocket message
MCP tool argument
```

map:

```text
source
validator
normalizer
sink
```

Pipeline:

```text
UNTRUSTED INPUT
   ↓
PARSER
   ↓
NORMALIZER
   ↓
VALIDATOR
   ↓
BUSINESS LOGIC
   ↓
SINK
```

---

# 22. Input Boundary Classes

Check for:

```text
type confusion
missing required field
unexpected property
oversized input
nested object depth
array explosion
string length
numeric bounds
encoding ambiguity
duplicate parameters
content-type confusion
path normalization
```

Focus on security-relevant validation rather than simply generating arbitrary payload volume.

---

# 23. Injection Boundaries

Identify sinks:

```text
SQL
NoSQL
command
template
HTML
JavaScript
LDAP
XPath
expression
log
filesystem
URL
HTTP
```

Source-to-sink analysis should combine:

```text
Semgrep
repo_symbol
repo_search
threat model
runtime evidence
```

Do not call something exploitable solely because an input eventually reaches a sink; establish the relevant escaping/parameterization boundary.

---

# 24. SSRF

Identify URL-fetching sinks:

```text
webhook
URL preview
image import
document fetch
proxy
callback
remote file import
integration endpoint
```

Safe validation may use:

```text
controlled callback endpoint
scope-approved canary
```

Evidence should establish:

```text
application made the outbound request
target was controlled
callback was observed
```

Do not request:

```text
cloud metadata
production internal services
credential endpoints
```

as part of validation.

Do not place internal response bodies containing sensitive data in findings.

---

# 25. Rate Limiting

Distinguish:

```text
configured limit
observed limit
effective limit
```

For each protected route record:

```yaml
rate_limit:
  configured:
  observed:
  window:
  burst:
  identity_key:
  response:
  retry_after:
```

A rate-limit finding requires reproducible evidence that the effective control is weaker than intended.

Do not run unrestricted high-volume traffic.

Use a bounded test budget.

---

# 26. Rate-Limit Dimensions

Determine whether limits are based on:

```text
IP
user
API key
tenant
session
route
resource
global
```

Check for inconsistent enforcement:

```text
per-IP limit
but unlimited authenticated requests

or

per-route limit
but expensive operation bypasses route limiter
```

---

# 27. Security Headers

Use:

```text
security_headers
```

Check relevant headers according to the endpoint/application context:

```text
Strict-Transport-Security
Content-Security-Policy
X-Content-Type-Options
Referrer-Policy
Permissions-Policy
Cache-Control
Set-Cookie attributes
CORS response headers
```

Never report:

```text
missing header
```

without explaining:

```text
expected policy
actual policy
affected resource
security consequence
```

Example:

```text
Expected:
Secure + HttpOnly + SameSite policy

Observed:
Secure absent

Impact:
session cookie may be exposed over an unintended transport path
```

Only claim the impact supported by evidence.

---

# 28. CORS

Check:

```text
origin reflection
wildcard origin
credentialed requests
preflight behavior
method restrictions
header restrictions
null origin
subdomain trust
```

Important:

```text
Access-Control-Allow-Origin: *
```

is not automatically a vulnerability.

Determine whether:

```text
credentials
sensitive response data
browser-readable endpoints
```

make the policy dangerous.

CORS is not an authorization control.

---

# 29. HTTP Method Security

Inventory:

```text
GET
HEAD
OPTIONS
POST
PUT
PATCH
DELETE
TRACE
CONNECT
```

Check:

```text
unexpected enabled methods
authorization consistency
method override
X-HTTP-Method-Override
routing differences
```

A method must be tested against the same authorization model as its resource.

---

# 30. Content-Type and Parser Boundaries

Check:

```text
application/json
multipart/form-data
application/x-www-form-urlencoded
text/plain
XML
GraphQL
protobuf
WebSocket messages
```

Look for parser inconsistencies:

```text
frontend validation
      !=
backend validation

proxy interpretation
      !=
application interpretation
```

Potential class:

```text
REQUEST_SMUGGLING_INDICATOR
PARSER_CONFUSION
VALIDATION_BYPASS
```

Do not escalate into destructive exploitation.

---

# 31. File Upload Security

For file-upload endpoints check:

```text
authentication
authorization
extension validation
MIME validation
content validation
size limit
filename normalization
storage location
download authorization
public exposure
virus/malware scanning
processing pipeline
```

Test only benign controlled files.

Never upload real malware.

---

# 32. Resource Exhaustion

Check bounded controls for:

```text
request size
response size
pagination
query complexity
GraphQL depth
batch size
file size
concurrent connections
expensive operations
background jobs
```

Use small safe test budgets.

Do not intentionally take services offline.

---

# 33. Error Handling

Check whether API errors reveal:

```text
stack traces
filesystem paths
SQL/database information
internal service names
cloud identifiers
tokens
debug state
framework internals
```

Classify:

```text
expected client error
operational error
security-sensitive leakage
```

Do not preserve secrets found in error messages.

---

# 34. Sensitive Data Exposure

Inventory:

```text
PII
tokens
credentials
internal identifiers
financial information
authorization metadata
security configuration
debug information
```

Check:

```text
response
logs
headers
error messages
OpenAPI examples
GraphQL schema
MCP tool output
gRPC errors
WebSocket events
```

Findings must use minimal evidence.

---

# 35. Business Logic

API security must not stop at transport controls.

For important workflows model:

```text
precondition
  ↓
action
  ↓
state transition
  ↓
postcondition
```

Test safe indicators for:

```text
workflow skipping
replay
duplicate action
state confusion
authorization inconsistency
price/quantity manipulation
approval bypass
resource ownership transition
```

Do not execute irreversible transactions.

---

# 36. API Schema Enforcement

Compare declared schema with implementation.

Check:

```text
required fields
types
enum restrictions
maximum values
minimum values
unknown fields
response shape
additionalProperties
nullable fields
authentication requirements
security schemes
```

Potential issue:

```text
schema says field is restricted
implementation accepts arbitrary value
```

---

# 37. Schema Drift

Create:

```text
DOCUMENTED
IMPLEMENTED
OBSERVED
```

matrix.

Example:

```text
OpenAPI:
POST /users/{id}

Runtime:
POST /users/{id}/admin

Source:
POST /users/{id}/admin

Result:
SHADOW_ENDPOINT / DOCUMENTATION_DRIFT
```

Drift should be reviewed because undocumented routes often escape normal security testing.

---

# 38. Threat Model

Use:

```text
security_threat_model
```

Required matrix:

```yaml
threat:
  asset:
  entry_point:
  actor:
  trust_boundary:
  input:
  sink:
  control:
  failure_mode:
  evidence:
  impact:
  mitigation:
```

At minimum model:

```text
internet
reverse proxy
gateway
API
service
database
queue
third-party service
browser
MCP server
```

---

# 39. Static + Runtime Correlation

Preferred:

```text
route inventory
      +
source analysis
      +
threat model
      +
runtime evidence
```

Example:

```text
Route:
PATCH /users/:id

Semgrep:
authorization middleware absent

Runtime:
other-user update -> 200

Conclusion:
strong / verified finding
```

This is substantially stronger than either source-only or scanner-only analysis.

---

# 40. Finding Confidence

```text
SUSPECTED
INDICATED
STRONG
VERIFIED
```

### SUSPECTED

Single heuristic.

### INDICATED

Multiple independent signals.

### STRONG

Direct source/configuration evidence exists.

### VERIFIED

Safe runtime behavior directly confirms the security condition.

---

# 41. SecurityFinding Schema

Every finding must contain:

```yaml
finding:
  id:
  title:
  category:
  severity:
  confidence:
  evidence_level:

asset:
  protocol:
  host:
  endpoint:
  operation:

control:
  expected:
  observed:
  effectiveness:

evidence:
  source:
  runtime:
  timestamps:
  redacted_request:
  redacted_response:

impact:
  confidentiality:
  integrity:
  availability:

mapping:
  cwe:
  owasp:
  asvs:
  api_top_10:
  wstg:

remediation:
  root_cause:
  recommendation:
  validation_method:

regression:
  exists:
  test_stub:

status:
  open
  false_positive
  duplicate
  accepted_risk
  mitigated
  resolved
  regressed
```

---

# 42. One Finding Per Control Failure

Do not create one giant finding:

```text
"API is insecure"
```

Prefer:

```text
SEC-001
Broken object authorization

SEC-002
Missing rate-limit enforcement

SEC-003
Sensitive response exposure
```

This makes:

```text
triage
ownership
remediation
regression
```

precise.

---

# 43. Evidence Requirements by Finding

## IDOR/BOLA

Required:

```text
actor
resource ownership
request shape
observed authorization failure
```

## Rate limiting

Required:

```text
expected limit
observed behavior
bounded test window
identity dimension
```

## Header

Required:

```text
expected policy
actual header
affected resource
security consequence
```

## CORS

Required:

```text
Origin
response headers
credential behavior
data sensitivity
browser-relevant impact
```

## SSRF

Required:

```text
controlled target
controlled callback evidence
request correlation
```

## Injection

Required:

```text
source
validation/encoding path
sink
safe evidence
```

---

# 44. Validation

Use:

```text
security_validate_finding
```

Validation must check:

```text
scope
target
repeatability
evidence quality
non-destructive nature
```

If validation is incomplete:

```text
confidence = UNCERTAIN
```

Do not promote findings merely because the scanner severity is high.

---

# 45. Correlation

Correlate:

```text
security_api_inventory
security_headers
security_sast
Nuclei
ZAP
Schemathesis
source analysis
threat model
runtime evidence
```

Example:

```text
ZAP:
  missing authorization signal

Semgrep:
  route missing authorization guard

Runtime:
  unauthorized object accepted

=> one correlated finding
```

---

# 46. Deduplication

Fingerprint from:

```text
protocol
host
endpoint
operation
control
rule
resource
parameter
```

Do not merge findings solely based on:

```text
title
severity
CVE
scanner
```

---

# 47. API Top-Level Coverage

Every review should report coverage across:

```text
Authentication
Authorization
Object-level authorization
Property-level authorization
Function-level authorization
Tenant isolation
Input validation
Injection
SSRF
Rate limiting
Resource exhaustion
CORS
Security headers
TLS
Error handling
Sensitive data
File upload
Business logic
Schema enforcement
Inventory drift
MCP capabilities
```

---

# 48. Regression Generation

For every exploitable finding generate:

```text
security regression candidate
```

Example:

```text
Finding:
BOLA on GET /api/projects/{id}

Regression:

anonymous -> 401
user A own object -> 200
user A other-user object -> 403
admin -> 200
```

For rate limiting:

```text
within budget -> allowed
above configured threshold -> limited
after retry window -> allowed
```

For headers:

```text
response -> required policy present
```

---

# 49. Change-Aware Review

When an endpoint changes, prioritize:

```text
changed route
changed middleware
changed schema
changed authorization policy
changed sink
changed dependency
changed headers
changed rate limiter
```

Then assess adjacent trust boundaries.

Example:

```text
auth middleware changed
    ↓
all protected routes using middleware
    ↓
authorization regression set
```

---

# 50. Risk Prioritization

Consider:

```text
severity
confidence
internet exposure
authentication boundary
authorization boundary
tenant impact
data sensitivity
preconditions
affected population
environment
remediation availability
```

Do not automatically equate:

```text
scanner severity = confirmed impact
```

---

# 51. Output

Required outputs:

```text
route_inventory.json
control_matrix.json
threat_model.json
security_findings.json
api-security-report.md
regression-tests.md
coverage.json
```

Optional:

```text
SARIF
HTML
PDF
```

---

# 52. Final Report Structure

```text
1. Scope
2. API inventory
3. Protocol coverage
4. Authentication model
5. Authorization model
6. Tenant isolation
7. Input validation
8. Rate limiting
9. CORS
10. Security headers
11. SSRF
12. Injection
13. Business logic
14. GraphQL
15. WebSocket
16. gRPC
17. MCP
18. Schema drift
19. Sensitive data
20. Findings
21. Evidence
22. Coverage
23. Limitations
24. Remediation
25. Regression tests
```

---

# 53. Routing

```text
endpoint security review
    -> api-security

overall web security assessment
    -> xninetzy-security-testing

secure coding review
    -> security-review
    -> security-sast

architecture threat model
    -> security-threat-model

dependency vulnerability
    -> xninetzy-security-testing

MCP-specific surface
    -> api-security
    -> xninetzy-security-testing
```

---

# 54. Reference Loading

When this skill is invoked:

```text
IF installation/tool availability is required
    -> read ../xninetzy-security-testing/references/install.md

IF live scanner orchestration is required
    -> read ../xninetzy-security-testing/references/workflow.md

IF scope/authorization/evidence policy is required
    -> read ../xninetzy-security-testing/SKILL.md

IF all are required
    -> read all three
```

Precedence:

```text
SKILL.md security policy
    >
this api-security skill
    >
workflow reference
    >
generic assumptions
```

This skill must never override the security domain's authorization and scope policy.

---

# 55. Completion Contract

An API security review is complete only when:

```text
[ ] scope validated
[ ] endpoint inventory available
[ ] protocol classified
[ ] authentication mapped
[ ] authorization mapped
[ ] tenant boundary considered
[ ] input boundaries mapped
[ ] rate limiting assessed
[ ] security headers assessed
[ ] CORS assessed where relevant
[ ] SSRF sinks considered
[ ] schema drift assessed
[ ] business logic considered
[ ] applicable protocol-specific controls assessed
[ ] static evidence correlated
[ ] runtime evidence validated where authorized
[ ] findings deduplicated
[ ] confidence assigned
[ ] limitations recorded
[ ] regression candidates produced
[ ] report generated
```

---

# 56. Final Principle

The purpose of this skill is not to answer:

```text
"Does this API have security middleware?"
```

It is to answer:

```text
What is exposed?
Who can access it?
What are they allowed to do?
What inputs are trusted?
Where does that input flow?
What controls are supposed to enforce the boundary?
Do those controls actually work?
What evidence proves the result?
Can the finding be reproduced safely?
Can the fix become a permanent regression test?
```

The desired outcome is:

```text
inventory
+
control effectiveness
+
trust-boundary analysis
+
runtime evidence
+
correlation
+
regression
```

with:

```text
strict scope
+
safe execution
+
minimal evidence
+
no destructive behavior
```
