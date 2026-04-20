# SAM Makefile builds — called by `sam build` for each Lambda function.
#
# PREREQUISITES (Windows):
#   Run from Git Bash with make installed: choco install make
#   OR: sam build --use-container  (requires Docker, Linux environment)
#
# SAM sets ARTIFACTS_DIR before calling each target.
# Third-party packages are provided by SharedDepsLayer — no pip install here.

SHELL := bash

.PHONY: build-MealFunction build-LocationFunction build-OverrideFunction \
        build-HeadcountFunction build-InteractionFunction build-GoogleChatFunction

# ── Feature Lambdas ──────────────────────────────────────────────────────────
# Each target copies: shared src files + its own handler + its own service(s).
# The Google Chat adapter is intentionally excluded from feature Lambdas.

build-MealFunction:
	mkdir -p $(ARTIFACTS_DIR)/src/handlers $(ARTIFACTS_DIR)/src/services $(ARTIFACTS_DIR)/src/adapters
	cp src/__init__.py src/models.py src/config.py src/utils.py $(ARTIFACTS_DIR)/src/
	cp -r src/storage $(ARTIFACTS_DIR)/src/
	cp src/adapters/__init__.py src/adapters/base.py src/adapters/normalized.py $(ARTIFACTS_DIR)/src/adapters/
	cp -r src/adapters/discord $(ARTIFACTS_DIR)/src/adapters/
	cp src/services/__init__.py src/services/discord_helpers.py src/services/team_helpers.py src/services/policy_service.py $(ARTIFACTS_DIR)/src/services/
	cp src/handlers/auth.py src/handlers/meal_handler.py $(ARTIFACTS_DIR)/src/handlers/
	cp src/services/meal_service.py src/services/location_service.py $(ARTIFACTS_DIR)/src/services/

build-LocationFunction:
	mkdir -p $(ARTIFACTS_DIR)/src/handlers $(ARTIFACTS_DIR)/src/services $(ARTIFACTS_DIR)/src/adapters
	cp src/__init__.py src/models.py src/config.py src/utils.py $(ARTIFACTS_DIR)/src/
	cp -r src/storage $(ARTIFACTS_DIR)/src/
	cp src/adapters/__init__.py src/adapters/base.py src/adapters/normalized.py $(ARTIFACTS_DIR)/src/adapters/
	cp -r src/adapters/discord $(ARTIFACTS_DIR)/src/adapters/
	cp src/services/__init__.py src/services/discord_helpers.py src/services/team_helpers.py src/services/policy_service.py $(ARTIFACTS_DIR)/src/services/
	cp src/handlers/auth.py src/handlers/location_handler.py $(ARTIFACTS_DIR)/src/handlers/
	cp src/services/meal_service.py src/services/location_service.py $(ARTIFACTS_DIR)/src/services/

build-OverrideFunction:
	mkdir -p $(ARTIFACTS_DIR)/src/handlers $(ARTIFACTS_DIR)/src/services $(ARTIFACTS_DIR)/src/adapters
	cp src/__init__.py src/models.py src/config.py src/utils.py $(ARTIFACTS_DIR)/src/
	cp -r src/storage $(ARTIFACTS_DIR)/src/
	cp src/adapters/__init__.py src/adapters/base.py src/adapters/normalized.py $(ARTIFACTS_DIR)/src/adapters/
	cp -r src/adapters/discord $(ARTIFACTS_DIR)/src/adapters/
	cp src/services/__init__.py src/services/discord_helpers.py src/services/team_helpers.py src/services/policy_service.py $(ARTIFACTS_DIR)/src/services/
	cp src/handlers/auth.py src/handlers/override_handler.py $(ARTIFACTS_DIR)/src/handlers/
	cp src/services/meal_service.py src/services/location_service.py src/services/override_service.py $(ARTIFACTS_DIR)/src/services/

build-HeadcountFunction:
	mkdir -p $(ARTIFACTS_DIR)/src/handlers $(ARTIFACTS_DIR)/src/services $(ARTIFACTS_DIR)/src/adapters
	cp src/__init__.py src/models.py src/config.py src/utils.py $(ARTIFACTS_DIR)/src/
	cp -r src/storage $(ARTIFACTS_DIR)/src/
	cp src/adapters/__init__.py src/adapters/base.py src/adapters/normalized.py $(ARTIFACTS_DIR)/src/adapters/
	cp -r src/adapters/discord $(ARTIFACTS_DIR)/src/adapters/
	cp src/services/__init__.py src/services/discord_helpers.py src/services/team_helpers.py src/services/policy_service.py $(ARTIFACTS_DIR)/src/services/
	cp src/handlers/auth.py src/handlers/headcount_handler.py $(ARTIFACTS_DIR)/src/handlers/
	cp src/services/meal_service.py src/services/location_service.py src/services/headcount_service.py $(ARTIFACTS_DIR)/src/services/

# ── Ingress Lambdas ───────────────────────────────────────────────────────────
# Both route every command in-process and need the full src/ tree.

build-InteractionFunction:
	cp -r src $(ARTIFACTS_DIR)/

build-GoogleChatFunction:
	cp -r src $(ARTIFACTS_DIR)/
