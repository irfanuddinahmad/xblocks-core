.DEFAULT_GOAL := help

.PHONY: upgrade help requirements
.PHONY: extract_translations compile_translations
.PHONY: detect_changed_source_translations dummy_translations build_dummy_translations
.PHONY: validate_translations pull_translations push_translations install_transifex_clients

PACKAGE_NAME := xblocks_contrib
EXTRACT_DIR := conf/locale/en/LC_MESSAGES
COMBINED_LOCALE_DIR := $(PACKAGE_NAME)/conf/locale/en/LC_MESSAGES
JS_TARGET := $(PACKAGE_NAME)/public/js/translations

help:
	@perl -nle'print $& if m{^[\.a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

upgrade: ## update uv.lock and regenerate uv constraints from edx-lint
	uv run --with edx-lint edx_lint write_uv_constraints pyproject.toml
	uv lock --upgrade

requirements: ## install development environment requirements using uv
	uv sync --group dev

# XBlock directories
XBLOCKS=$(shell find $(shell pwd)/$(PACKAGE_NAME) -mindepth 2 -maxdepth 2 -type d -name 'conf' -exec dirname {} \;)

## Localization targets

extract_translations: ## extract strings to be translated, outputting .po files for each XBlock
	@for xblock in $(XBLOCKS); do \
		echo "Extracting translations for $$xblock..."; \
		cd $$xblock && i18n_tool extract --no-segment; \
		if [ -f $$xblock/$(EXTRACT_DIR)/djangojs.po ]; then \
			cd $$xblock/$(EXTRACT_DIR) && msgcat django.po djangojs.po -o django.po && rm -f djangojs.po; \
		fi; \
		if [ -f $$xblock/$(EXTRACT_DIR)/django.po ]; then \
			mv $$xblock/$(EXTRACT_DIR)/django.po $$xblock/$(EXTRACT_DIR)/text.po; \
		fi; \
	done
	@# Merge all per-xblock text.po files into a single combined file for the
	@# openedx-translations pipeline (OEP-58), which expects one conf/locale/en per repo.
	@mkdir -p $(COMBINED_LOCALE_DIR)
	@PO_FILES=""; \
	for xblock in $(XBLOCKS); do \
		if [ -f $$xblock/$(EXTRACT_DIR)/text.po ]; then \
			PO_FILES="$$PO_FILES $$xblock/$(EXTRACT_DIR)/text.po"; \
		fi; \
	done; \
	if [ -n "$$PO_FILES" ]; then \
		msgcat --use-first $$PO_FILES -o $(COMBINED_LOCALE_DIR)/django.po; \
		echo "Combined translation source file written to $(COMBINED_LOCALE_DIR)/django.po"; \
	fi

compile_translations: ## compile translation files, outputting .mo files for each supported language for each XBlock
	@for xblock in $(XBLOCKS); do \
		echo "Compiling translations for $$xblock..."; \
		cd $$xblock && django-admin compilemessages --locale en; \
	done

detect_changed_source_translations:
	@for xblock in $(XBLOCKS); do \
		echo "Detecting changed translations for $$xblock..."; \
		cd $$xblock && i18n_tool changed; \
	done

dummy_translations: ## generate dummy translation (.po) files for each XBlock
	@for xblock in $(XBLOCKS); do \
		echo "Generating dummy translations for $$xblock..."; \
		cd $$xblock && i18n_tool dummy; \
	done

build_dummy_translations: extract_translations dummy_translations compile_translations ## generate and compile dummy translation files

validate_translations: build_dummy_translations detect_changed_source_translations ## validate translations

pull_translations: ## pull translations from Transifex for each XBlock
	@for xblock in $(XBLOCKS); do \
		echo "Pulling translations for $$xblock..."; \
		cd $$xblock && i18n_tool transifex pull; \
	done

push_translations: extract_translations ## push translations to Transifex for each XBlock
	@for xblock in $(XBLOCKS); do \
		echo "Pushing translations for $$xblock..."; \
		cd $$xblock && i18n_tool transifex push; \
	done

install_transifex_client: ## Install the Transifex client
	# Instaling client will skip CHANGELOG and LICENSE files from git changes
	# so remind the user to commit the change first before installing client.
	git diff -s --exit-code HEAD || { echo "Please commit changes first."; exit 1; }
	curl -o- https://raw.githubusercontent.com/transifex/cli/master/install.sh | bash
	git checkout -- LICENSE README.md ## overwritten by Transifex installer

selfcheck: ## check that the Makefile is well-formed
	@echo "The Makefile is well-formed."
