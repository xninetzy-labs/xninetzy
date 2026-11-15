# xninetzy-web-analysis — §18–27

Contents: 18. Human Verification Boundary; 19. Discovery Bounds; 20. Discovery Workflow; 21. Freshness; 22. Cache Model; 23. Discovery Artifact; 24. Historical Snapshots; 25. Change Detection; 26. Sensitive Content Filtering; 27. Query Parameter Safety

## 18. Human Verification Boundary

Human verification includes:

* CAPTCHA
* reCAPTCHA
* hCaptcha
* image challenges
* math challenges
* challenge-response login
* anti-bot interstitials
* equivalent human-presence mechanisms

When detected:

```text id="o9qv9k"
page identified
      ↓
verification detected
      ↓
record safe structural observation
      ↓
STOP
      ↓
return control to human/domain-specific authentication workflow
```

Never:

* solve CAPTCHA
* OCR CAPTCHA
* infer CAPTCHA answers
* automate challenge interaction
* bypass challenge endpoints
* poll challenge state repeatedly
* use another route to avoid the challenge

---

## 19. Discovery Bounds

Discovery must always be bounded.

Default controls:

```text id="z5z5c7"
depth_limit
max_pages
allowed_hosts
seed_urls
```

Do not crawl an entire portal unintentionally.

For public documentation sites, larger bounds may be justified when explicitly configured.

Bound:

* page count
* crawl depth
* retries
* request frequency
* response size where supported
* redirect chains

---

## 20. Discovery Workflow

Conceptually:

```text id="g0g5iy"
1. inspect status
2. determine freshness
3. refresh if necessary
4. discover from approved seeds
5. enforce host boundaries
6. enforce depth/page limits
7. classify pages
8. filter sensitive content
9. persist safe evidence
10. verify persistence
```

Do not perform unnecessary discovery.

---

## 21. Freshness

Track:

```text id="4p4o2u"
fresh
stale
unknown
```

Refresh when:

* user asks for current structure
* cache is stale
* portal may have changed
* important page is missing
* current navigation matters
* authenticated structure may have changed
* change detection is requested

Historical cache is useful but cannot be reported as current without qualification.

---

## 22. Cache Model

The analysis cache should contain structural information:

* site identity
* page identity
* routes
* modules
* navigation
* access classification
* structural metadata
* timestamps
* provenance

It should not contain:

* credentials
* cookies
* access tokens
* private academic records
* private form submissions
* session secrets

The cache is a structural model, not a private-record database.

---

## 23. Discovery Artifact

Persist discovery output under:

```text
<WEB_ANALYSIS_DATA_DIR>/discoveries/<site_slug>/latest.json
```

Treat `latest.json` as generated state.

After persistence:

1. verify file exists
2. verify it is readable
3. verify expected structure
4. verify site identity
5. verify timestamp/version

Do not report successful persistence solely because a write operation returned successfully.

---

## 24. Historical Snapshots

Where practical, preserve historical snapshots separately from `latest.json`.

Conceptually:

```text id="5d0q3f"
discoveries/
└── <site_slug>/
    ├── latest.json
    └── history/
        ├── <timestamp-1>.json
        ├── <timestamp-2>.json
        └── ...
```

Historical snapshots support:

* change detection
* regression analysis
* portal migration tracking
* navigation evolution

Do not destroy historical evidence merely because a new analysis exists.

---

## 25. Change Detection

Compare verified historical and current catalogs.

Possible changes:

```text id="1w6e8x"
page_added
page_removed
page_renamed
route_changed
navigation_changed
module_changed
access_class_changed
content_changed
```

Distinguish:

```text structural change
```

from:

```text content change
```

Do not claim that a page was removed merely because discovery failed once.

Require sufficient evidence.

---

## 26. Sensitive Content Filtering

Before persistence, inspect content for:

* credentials
* cookies
* tokens
* session identifiers
* private query parameters
* personal academic records
* private form values
* sensitive identifiers

Strip or exclude sensitive material.

When a page mixes public and sensitive information:

```text id="9g4w5c"
retain safe public structure/content
discard sensitive values
```

Never persist an entire authenticated page merely because part of it is structurally useful.

---

## 27. Query Parameter Safety

Treat query parameters as potentially sensitive.

Potentially sensitive examples:

```text
token
session
auth
code
key
signature
student_id
user_id
record_id
```

Do not persist sensitive parameter values.

Where possible, normalize URLs before persistence:

```text
/path/resource?token=<redacted>
```

rather than storing the actual secret.

---
