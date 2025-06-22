COMPARE_BRANCH ?= dev-v0.2.0

.PHONY: all pyright-diff pyright-full lint format security markdown precommit build-linux build-windows

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

build-linux-docker:
	sh scripts/linux_build.sh

build-windows:
	python scripts/build_windows.py