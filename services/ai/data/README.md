# Local runtime data

This directory is private, installation-specific runtime state. Its contents
must never be committed or distributed with the open-source repository.

At runtime Xninetzy creates data here, including:

- `xninetzy.sqlite3` and its WAL/SHM files;
- FAISS indexes and source mappings;
- HEBAT browser state, downloads, and debug artifacts;
- web-analysis snapshots and reports;
- WhatsApp media shared with the AI service;
- backup snapshots.

Each clone starts with its own empty database. The AI service creates and
migrates tables during startup. Use the documented backup/restore command when
moving one owner's installation; never use Git as the migration mechanism.

If private runtime files were pushed previously, deleting them from the latest
commit does not remove them from Git history. Rotate exposed sessions or secrets
and sanitize history before publishing the repository.
