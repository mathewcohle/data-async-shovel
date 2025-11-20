.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
SHELL := /bin/bash
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

.DEFAULT_GOAL := help

.PHONY: help
help: ## Display this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Variables
IMAGE_NAME := das
CONTAINER_NAME := das-app
PROJECT_ROOT := $(shell pwd)

uv.lock: pyproject.toml .python-version
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  🔒 Generating uv.lock..."
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	uv lock

# Dependency tracking
.build-image: Dockerfile pyproject.toml uv.lock .python-version
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  🔨 Building container image..."
	@printf "  \033[90m\$$\033[0m \033[90mpodman build -t $(IMAGE_NAME) .\033[0m\n"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	podman build -t $(IMAGE_NAME) .
	touch .build-image

.PHONY: check
check: ## Run linter and type checker
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  🔍 Running code checks..."
	@printf "  \033[90m\$$\033[0m \033[90muv run ruff check .\033[0m\n"
	@printf "  \033[90m\$$\033[0m \033[90muv run pyright .\033[0m\n"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	uv run ruff check .
	uv run pyright .

.PHONY: run-graceful
run-graceful: .build-image ## Run application with graceful shutdown (writes to data/out.txt)
	@rm -f $(PROJECT_ROOT)/data/*
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  🚀 Running application (GRACEFUL mode)..."
	@echo "  Output: data/out.txt"
	@echo "  Run make stop to terminate"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	podman run --rm -it --name $(CONTAINER_NAME) \
		-v $(PROJECT_ROOT)/src:/app/src:ro \
		-v $(PROJECT_ROOT)/data:/app/data:rw \
		$(IMAGE_NAME) \
		uv run --no-dev python -m das data/out.txt
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  📁 Contents of data/ directory:"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@ls -lh data/

.PHONY: run-buggy
run-buggy: .build-image ## Run buggy application (writes to data/out.txt)
	@rm -f $(PROJECT_ROOT)/data/*
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  🐛 Running BUGGY application..."
	@echo "  Output: data/out.txt"
	@echo "  Run make stop to terminate"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	podman run --rm -it --name $(CONTAINER_NAME) \
		-v $(PROJECT_ROOT)/src:/app/src:ro \
		-v $(PROJECT_ROOT)/data:/app/data:rw \
		$(IMAGE_NAME) \
		uv run --no-dev python -m das --buggy data/out.txt || true \
	echo ""; \
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	echo "  📁 Contents of data/ directory:"; \
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	ls -lh data/; \

.PHONY: stop
stop: ## Send SIGTERM to running container
	@echo "  📡 Sending SIGTERM to $(CONTAINER_NAME)..."
	podman kill --signal TERM $(CONTAINER_NAME)

.PHONY: clean
clean: ## Remove container and image
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  🧹 Cleaning up..."
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	podman rm -f $(CONTAINER_NAME) 2>/dev/null || true
	podman rmi $(IMAGE_NAME) 2>/dev/null || true
	rm -f .build-image
	@echo "  ✓ Cleanup complete"
