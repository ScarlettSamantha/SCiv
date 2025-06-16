#!/bin/bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

existing=()
for f in $files; do
    [[ -f "$f" ]] && existing+=("$f")
done

if [ ${#existing[@]} -eq 0 ]; then
    echo "No staged Python files to check."
    exit 0
fi

pyright "${existing[@]}"
