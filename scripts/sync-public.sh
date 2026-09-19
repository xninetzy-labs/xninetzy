#!/usr/bin/env bash
# Mirror the canonical `origin` (xninetzy-labs/xninetzy) to the public
# `public` remote (misbahul45/xninetzy).
#
# Pushes main + every tag. Use after a release.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

if ! git remote get-url public >/dev/null 2>&1; then
  echo "error: remote 'public' is not configured" >&2
  echo "  add it with:" >&2
  echo "    git remote add public https://github.com/misbahul45/xninetzy.git" >&2
  exit 1
fi

echo "Fetching origin..."
git fetch --prune --tags origin

echo "Pushing main to public..."
git push public origin/main:main

echo "Pushing tags to public..."
git push public --tags

echo "Done. main + tags mirrored from origin to public."
