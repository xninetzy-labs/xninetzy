# xninetzy-web-analysis — §6–15

Contents: 6. Scope Enforcement; 7. Domain Boundary; 8. Portal Isolation; 9. Source-of-Truth Hierarchy; 10. Evidence Model; 11. Evidence Levels; 12. Structural Analysis Model; 13. Access Classification; 14. Session Check; 15. Session Security

## 6. Scope Enforcement

Before every discovery operation:

1. resolve target host
2. normalize URL
3. compare host against allowlist
4. classify access mode
5. verify operation is permitted
6. apply depth limit
7. apply page limit
8. reject out-of-scope targets

The analyzer must fail closed.

If scope cannot be determined:

```text id="g4d2ly"
STOP
→ mark target as unknown
→ do not crawl
→ report configuration/authorization ambiguity
```

---

## 7. Domain Boundary

Every discovered link must be classified.

```text id="qz6h2v"
same_allowlisted_domain
allowed_related_domain
external_unknown
```

Default behavior:

```text
same_allowlisted_domain → may continue
allowed_related_domain  → continue only if explicitly configured
external_unknown        → do not crawl
```

A link appearing on an allowlisted page does not automatically authorize crawling its destination.

---

## 8. Portal Isolation

Every portal is an independent security and state domain.

Never mix:

* cookies
* credentials
* access tokens
* encrypted sessions
* browser profiles
* identities
* challenge state
* cache namespaces
* screenshots
* analysis records
* academic records

between portals.

Conceptually:

```text id="9p4s7x"
Portal A
├── session A
├── cache A
├── graph evidence A
└── visual evidence A

Portal B
├── session B
├── cache B
├── graph evidence B
└── visual evidence B
```

A common user does not make portal state interchangeable.

---

## 9. Source-of-Truth Hierarchy

Use:

```text id="2ox8v1"
Current verified portal response
        ↓
Current typed analyzer result
        ↓
Verified analysis cache
        ↓
Verified Graph RAG state
        ↓
Verified knowledge state
        ↓
Checkpoint/memory
        ↓
Historical analysis
```

Historical information supports comparison and change detection.

It does not override current verified state.

---

## 10. Evidence Model

Every material structural observation should have provenance.

Represent evidence conceptually as:

```text id="3q6p5z"
Observation
├── source URL
├── page identity
├── access class
├── retrieval timestamp
├── portal/site identity
├── discovery method
├── evidence level
└── version/checkpoint where applicable
```

Never create a factual relationship without an observable source.

---

## 11. Evidence Levels

Classify observations as:

```text id="x4v6cb"
direct
derived
historical
unknown
```

#### direct

Observed in the current analysis.

#### derived

Reasoned from current observations.

#### historical

Observed during an earlier verified analysis.

#### unknown

Insufficient evidence exists.

Never present:

```text
derived
historical
unknown
```

as equivalent to current direct observation.

---

## 12. Structural Analysis Model

The analyzer should conceptually model:

```text id="h3qv4j"
Site
├── Host
├── Page
├── Route
├── Module
├── Navigation
├── Link
├── Access Class
└── Structural Metadata
```

Possible relationships:

```text id="4c7x0d"
page
  └── links_to → page

module
  └── contains → page

page
  └── belongs_to → module
```

Only create relationships supported by observed navigation or verified analyzer output.

Do not infer relationships solely from:

* URL similarity
* page-name similarity
* embeddings
* search ranking
* semantic similarity
* guessed conventions

---

## 13. Access Classification

Every page should be classified as:

```text id="2j4f1k"
public
login
authenticated
unknown
```

#### public

Accessible without authentication.

#### login

Authentication entry/challenge page.

#### authenticated

Requires an authenticated session.

#### unknown

Access classification cannot be reliably established.

If access classification is unknown, default to the more restrictive interpretation.

---

## 14. Session Check

Authenticated analysis may occur only when:

* authenticated analysis is explicitly allowed
* a valid approved session exists
* the session belongs to the intended portal
* the session is isolated
* the analyzer is permitted to inspect the requested scope

If the required session is unavailable:

```text id="0d1p4t"
STOP
→ authentication_missing
```

Do not silently fall back to an unrelated session.

---

## 15. Session Security

Never persist or expose:

* passwords
* cookies
* bearer tokens
* session IDs
* CSRF tokens
* authentication headers
* refresh tokens
* browser storage secrets
* raw authenticated request payloads

Encrypted session material must remain inside the approved authentication/session mechanism.

The analysis layer consumes authorization state; it must not extract or reveal its secrets.

---
