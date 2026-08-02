---
layout: ../../layouts/DocsLayout.astro
title: HEBAT and Moodle
description: Safe login, course sync, original material downloads, PDF reading, and confirmed submission.
section: Integrations
---

The HEBAT integration uses Playwright for authenticated browser sessions and a
Moodle client for courses, activities, resources, and assignments.

## Configuration

```dotenv
HEBAT_USERNAME=
HEBAT_PASSWORD=
HEBAT_BASE_URL=https://hebat.elearning.unair.ac.id
HEBAT_LOGIN_URL=https://hebat.elearning.unair.ac.id/login/index.php
HEBAT_BROWSER_HEADLESS=true
HEBAT_AUTO_LOGIN=false
HEBAT_REQUIRE_CONFIRMATION=true
HEBAT_ALLOW_AUTO_SUBMIT=false
```

Keep credentials only in a local `.env` with mode `600`. Never commit browser
profiles, cookies, storage state, or course downloads.

## Browser setup

```bash
cd services/ai
uv sync
uv run playwright install chromium
```

The AI Docker image already installs the required browser dependencies.

## Example workflow

```text
log in to HEBAT
sync HEBAT courses
list HEBAT courses
open the Machine Learning course and list its activities
download every PDF from Machine Learning
read the PDFs and create a complete roadmap in Obsidian
```

Use a sufficiently specific course name. After sync, tools can search the local
course cache.

## Assignments become tasks and reminders

`hebat_sync_assignments` projects each assignment idempotently into shared OS
state:

```text
HEBAT assignment → high-priority task → deadline reminder
```

Later syncs update the same title, instructions, deadline, and task status rather
than creating duplicates. Reminders store `source=hebat`, a source reference,
a deadline, and a structured offset. This installation-global state is visible
from WhatsApp, MCP, Codex, Claude Code, and OpenCode.

When Moodle reports a submitted assignment, the linked task is completed.
Uploading a file still requires submission confirmation.

## Download materials

Files are stored under:

```text
services/ai/data/hebat/downloads/<course-id>/<activity>/<filename>
```

The downloader follows Moodle resource pages to the original `pluginfile.php`
URL. It validates content type, magic bytes, and extension so a login page or
HTML redirect cannot be stored as a PDF.

## Read materials

The PDF reader uses native text first and OCR for scanned pages. After
extraction, the agent can summarize each resource, order prerequisites, create a
roadmap, write concept notes, or ingest chunks into the knowledge base.

## Assignment submission

Submission is a high-risk action. Guards include:

- administrator identity;
- extension allowlist;
- file-size limits;
- allowed-path confinement;
- a confirmation token;
- `HEBAT_ALLOW_AUTO_SUBMIT=false` by default.

Do not disable confirmation for convenience. Review the file preview, course,
and assignment before approval.

## Safe debugging

From WhatsApp:

```text
/hebat-debug
```

Or inspect service logs:

```bash
docker compose logs --tail=200 ai
```

Logs must not print passwords or cookies. Check the base and login URLs,
credential whitespace, Chromium installation, profile permissions, session
expiry, maintenance, and selector changes.

## Responsible use

This is a personal integration. Respect institutional policy and rate limits.
Never share a session, cookie, licensed material, or automate final submission
without owner review.
