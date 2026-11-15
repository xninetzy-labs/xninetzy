# cli-creator — §21–29

Contents: 21. JSON Success Shape; 22. JSON Error Shape; 23. Exit Codes; 24. Human vs Machine Output; 25. Global Flags; 26. Doctor; 27. Init; 28. Authentication Precedence; 29. Authentication Sources

## 21. JSON Success Shape

Pick one convention and use it consistently.

Example:

```json
{
  "ok": true,
  "data": {
    "id": "proj_123",
    "name": "My Project"
  }
}
```

For lists:

```json
{
  "ok": true,
  "data": [
    {
      "id": "proj_123",
      "name": "My Project"
    }
  ],
  "pagination": {
    "next_cursor": "abc"
  }
}
```

Do not alternate randomly between:

```text
[]
{}
{"items":[]}
{"data":[]}
```

without a documented reason.

---

## 22. JSON Error Shape

Errors must also be machine-readable.

Example:

```json
{
  "ok": false,
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "Authentication is not configured.",
    "retryable": false
  }
}
```

Possible error codes:

```text
AUTH_REQUIRED
AUTH_INVALID
FORBIDDEN
NOT_FOUND
AMBIGUOUS
INVALID_ARGUMENT
RATE_LIMITED
NETWORK_ERROR
TIMEOUT
API_ERROR
CONFIG_ERROR
NOT_SUPPORTED
WRITE_REQUIRES_APPROVAL
```

Never place raw credentials in error output.

---

## 23. Exit Codes

Use deterministic exit codes.

Suggested classes:

```text
0  success
1  generic failure
2  invalid CLI usage
3  authentication/configuration failure
4  permission failure
5  resource not found
6  network/API failure
7  timeout/rate limit
8  write approval required
9  ambiguous resolution
10 unsupported capability
```

Document the mapping.

Do not use successful exit code `0` for a failed API operation merely because JSON was printed.

---

## 24. Human vs Machine Output

Default output may be human-friendly.

`--json` must be machine-friendly.

Example:

```text
default:
Project: My Project
ID: proj_123
Status: active

--json:
{"ok":true,"data":{"id":"proj_123","status":"active"}}
```

Never mix human prose into `--json`.

---

## 25. Global Flags

Prefer a minimal global surface:

```text
--json
--quiet
--verbose
--config
--profile
--timeout
--no-color
--help
--version
```

Do not create dozens of global flags unless the service requires them.

---

## 26. Doctor

Every durable CLI should provide:

```bash
tool-name doctor
```

and:

```bash
tool-name --json doctor
```

Doctor checks:

```text
CLI version
config path
auth availability
auth source category
base URL
API reachability
dependency health
runtime environment
offline mode
fixture mode
missing setup
```

Example:

```json
{
  "ok": true,
  "cli_version": "1.2.0",
  "auth": {
    "configured": true,
    "source": "env"
  },
  "endpoint": {
    "reachable": true
  }
}
```

Never return the actual token.

---

## 27. Init

When environment variables are inconvenient, provide:

```bash
tool-name init
```

Possible configuration:

```toml
base_url = "https://api.example.com"
profile = "default"
```

Sensitive values should use:

```text
OS credential store
secure secret reference
environment variable
file permission 0600
```

rather than plaintext configuration where practical.

---

## 28. Authentication Precedence

Use:

```text
1. explicit one-off flag
2. environment variable
3. config
4. provider/system credential
5. missing
```

But for normal usage recommend:

```text
environment
or
config/credential store
```

Flags are less desirable for secrets because they may appear in:

```text
shell history
process listings
debugging tools
```

---

## 29. Authentication Sources

`doctor --json` should report only the source category:

```text
flag
env
config
provider
missing
```

Never:

```text
token value
full token
partial token
credential header
```

Prefer:

```json
{
  "configured": true,
  "source": "env"
}
```

---
