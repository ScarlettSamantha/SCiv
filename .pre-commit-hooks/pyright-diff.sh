#!/bin/bash
set -euo pipefail

# 1. find the repo root (so Pyright can load your config properly)
cd "$(git rev-parse --show-toplevel)"

# 2. get all staged .py files
files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

# 3. drop any that no longer exist on disk
existing=()
for f in $files; do
    [[ -f "$f" ]] && existing+=("$f")
done

# 4. exit early if nothing to do
if [ ${#existing[@]} -eq 0 ]; then
    echo "No staged Python files to check."
    exit 0
fi

# 5. invoke Pyright on *only* those files
pyright "${existing[@]}"
