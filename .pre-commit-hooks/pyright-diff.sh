#!/bin/bash

set -euo pipefail

# Get staged Python files
files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

# Filter: only keep files that still exist
existing_files=()
for file in $files; do
    if [ -f "$file" ]; then
        existing_files+=("$file")
    fi
done

# If no files, exit cleanly
if [ ${#existing_files[@]} -eq 0 ]; then
    echo "No Python files to check with pyright."
    exit 0
fi

# Run pyright on the existing files
pyright "${existing_files[@]}"
