COMPARE_BRANCH ?= dev-v0.2.0
PYTHON ?= python3

.PHONY: all pyright-diff pyright-full lint format security markdown precommit build-linux build-windows docs-refresh docs-check

all: pyright-diff lint format security markdown build-linux build-windows

precommit:
	pre-commit run --all-files

pyright-full:
	pyright . -p pyrightconfig.json

pyright-diff:
	COMPARE_BRANCH=$(COMPARE_BRANCH) bash .pre-commit-hooks/pyright-diff.sh

lint:
	ruff check .

format:
	ruff format --check --diff .

security:
	bandit -r . -c pyproject.toml

markdown:
	markdownlint '**/*.md'

docs-refresh:
	$(PYTHON) scripts/generate_project_index.py

docs-check:
	$(PYTHON) scripts/generate_project_index.py --check

build-linux-docker:
	sh scripts/linux_build.sh

build-windows:
	python scripts/build_windows.py