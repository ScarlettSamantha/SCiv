COMPARE_BRANCH ?= dev-v0.2.0
PYTHON ?= python3
CHANGELOG_SECTION ?= Unreleased
CHANGELOG_CATEGORY ?= Changed
CHANGELOG_MESSAGE ?=
CHANGELOG_EMOJI ?=
CHANGELOG_GITMOJI ?=
CHANGELOG_TICKET ?=
RELEASE_VERSION ?=
RELEASE_DATE ?=
RELEASE_TAG_PREFIX ?= v
RELEASE_TAG_NAME ?=
RELEASE_TAG_MESSAGE ?=
APP_VERSION ?=
VERSION_NAME ?=

CHANGELOG_HELPER_ARGS = $(if $(strip $(CHANGELOG_EMOJI)),--emoji "$(CHANGELOG_EMOJI)",) $(if $(strip $(CHANGELOG_GITMOJI)),--gitmoji "$(CHANGELOG_GITMOJI)",) $(if $(strip $(CHANGELOG_TICKET)),--ticket "$(CHANGELOG_TICKET)",)
RELEASE_HELPER_ARGS = $(if $(strip $(RELEASE_DATE)),--date "$(RELEASE_DATE)",)
TAG_HELPER_ARGS = --tag-prefix "$(RELEASE_TAG_PREFIX)" $(if $(strip $(RELEASE_TAG_NAME)),--tag-name "$(RELEASE_TAG_NAME)",) $(if $(strip $(RELEASE_TAG_MESSAGE)),--tag-message "$(RELEASE_TAG_MESSAGE)",)

.PHONY: all pyright-diff pyright-full lint format security markdown precommit build-linux build-windows docs-refresh docs-check changelog-help changelog-preview changelog-add changelog-unreleased changelog-categories changelog-gitmojis changelog-status version-show version-set release-preview release-cut release-tag-preview release-tag release-publish

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
	$(PYTHON) scripts/index.py generate

docs-check:
	$(PYTHON) scripts/index.py check

changelog-help:
	$(PYTHON) changelog.py --help

changelog-preview:
	@if [ -z "$(CHANGELOG_MESSAGE)" ]; then echo "Set CHANGELOG_MESSAGE=..."; exit 1; fi
	$(PYTHON) changelog.py add --section "$(CHANGELOG_SECTION)" --category "$(CHANGELOG_CATEGORY)" --message "$(CHANGELOG_MESSAGE)" $(CHANGELOG_HELPER_ARGS) --dry-run

changelog-add:
	@if [ -z "$(CHANGELOG_MESSAGE)" ]; then echo "Set CHANGELOG_MESSAGE=..."; exit 1; fi
	$(PYTHON) changelog.py add --section "$(CHANGELOG_SECTION)" --category "$(CHANGELOG_CATEGORY)" --message "$(CHANGELOG_MESSAGE)" $(CHANGELOG_HELPER_ARGS)

changelog-unreleased:
	$(PYTHON) changelog.py unreleased

changelog-categories:
	$(PYTHON) changelog.py categories

changelog-gitmojis:
	$(PYTHON) changelog.py gitmojis

changelog-status:
	$(PYTHON) changelog.py status

version-show:
	$(PYTHON) changelog.py version-show

version-set:
	@if [ -z "$(APP_VERSION)" ]; then echo "Set APP_VERSION=..."; exit 1; fi
	$(PYTHON) changelog.py version-set --version "$(APP_VERSION)" $(if $(strip $(VERSION_NAME)),--version-name "$(VERSION_NAME)",)

release-preview:
	@if [ -z "$(RELEASE_VERSION)" ]; then echo "Set RELEASE_VERSION=..."; exit 1; fi
	$(PYTHON) changelog.py release --version "$(RELEASE_VERSION)" $(RELEASE_HELPER_ARGS) --dry-run

release-cut:
	@if [ -z "$(RELEASE_VERSION)" ]; then echo "Set RELEASE_VERSION=..."; exit 1; fi
	$(PYTHON) changelog.py release --version "$(RELEASE_VERSION)" $(RELEASE_HELPER_ARGS)

release-tag-preview:
	@if [ -z "$(RELEASE_VERSION)" ]; then echo "Set RELEASE_VERSION=..."; exit 1; fi
	$(PYTHON) changelog.py tag --version "$(RELEASE_VERSION)" $(TAG_HELPER_ARGS) --dry-run

release-tag:
	@if [ -z "$(RELEASE_VERSION)" ]; then echo "Set RELEASE_VERSION=..."; exit 1; fi
	$(PYTHON) changelog.py tag --version "$(RELEASE_VERSION)" $(TAG_HELPER_ARGS)

release-publish:
	@if [ -z "$(RELEASE_VERSION)" ]; then echo "Set RELEASE_VERSION=..."; exit 1; fi
	$(PYTHON) changelog.py release --version "$(RELEASE_VERSION)" $(RELEASE_HELPER_ARGS)
	$(PYTHON) changelog.py tag --version "$(RELEASE_VERSION)" $(TAG_HELPER_ARGS)

build-linux-docker:
	sh scripts/linux_build.sh

build-windows:
	python scripts/build_windows.py