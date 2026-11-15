# AGENTS.md — §1

Part of the AGENTS.md policy; binds equally.

## 1. Human Intervention Is an Exception

Human intervention is required only when the workflow reaches an actual authorization or trust boundary.

Examples:

```text
OWNER AUTHENTICATION REQUIRED
EXPLICIT EXTERNAL PUBLICATION
EXPLICIT MESSAGE SEND
PAYMENT
LEGAL ACCEPTANCE
ACCOUNT OWNERSHIP CHANGE
IRREVERSIBLE EXTERNAL DELETION
SECURITY SCOPE AMBIGUITY
CAPTCHA REQUIRING HUMAN VERIFICATION
MFA / OTP
UNKNOWN AUTHORIZATION STATE
```

Everything before that boundary should continue autonomously.

Preferred behavior:

```text
AUTONOMOUS PREPARATION
        ↓
AUTONOMOUS EXECUTION
        ↓
AUTHORIZATION BOUNDARY
        ↓
PAUSE ONLY IF REQUIRED
        ↓
OWNER ACTION
        ↓
AUTOMATIC RESUME
        ↓
VERIFY
        ↓
CHECKPOINT
```

Do not restart the workflow after human intervention.

Resume from the latest valid checkpoint.

---
