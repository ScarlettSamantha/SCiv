#!/bin/bash
set -e

COMPARE_BRANCH="${COMPARE_BRANCH:-dev-v0.2.0}"

git fetch origin "$COMPARE_BRANCH"

changed_files=$(git diff --diff-filter=ACMR --name-only origin/$COMPARE_BRANCH...HEAD -- '*.py')

if [[ -n "$changed_files" ]]; then
    echo "Running Pyright on changed files:"
    echo "$changed_files"
    pyright $changed_files -p pyrightconfig.json
else
    echo "No Python files changed. Skipping Pyright."
fi
