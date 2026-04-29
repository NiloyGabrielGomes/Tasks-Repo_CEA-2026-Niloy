# SAM Makefile builds — called by `sam build` for each Lambda function.
#
# PREREQUISITES (Windows):
#   Run from Git Bash with make installed: choco install make
#   OR: sam build --use-container  (requires Docker, Linux environment)
#
# SAM sets ARTIFACTS_DIR before calling each target.
# Third-party packages are provided by SharedDepsLayer — no pip install here.

SHELL := bash

.PHONY: build-InteractionFunction build-GoogleChatFunction build-DiscordAuthorizerFunction

# ── Ingress Lambdas ───────────────────────────────────────────────────────────
# Both route every command in-process and need the full src/ tree.

build-InteractionFunction:
	cp -r src $(ARTIFACTS_DIR)/

build-GoogleChatFunction:
	cp -r src $(ARTIFACTS_DIR)/

build-DiscordAuthorizerFunction:
	mkdir -p $(ARTIFACTS_DIR)/src/handlers
	cp src/__init__.py $(ARTIFACTS_DIR)/src/
	cp src/handlers/discord_authorizer.py $(ARTIFACTS_DIR)/src/handlers/
