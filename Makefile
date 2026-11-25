PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
export PYTHONPATH := src

.PHONY: help venv install install-dev lint test eval run mcp docker-build clean

help:
	@echo "Targets:"
	@echo "  install       Create .venv and install the package"
	@echo "  install-dev   Install package plus pytest/ruff (and optional extras)"
	@echo "  lint          Run ruff check"
	@echo "  test          Run pytest"
	@echo "  eval          Run the eval harness (dummy agent until you wire yours)"
	@echo "  run           Launch the CLI"
	@echo "  mcp           Start the MCP server stub (TODO until you implement it)"
	@echo "  docker-build  Build the Docker image"
	@echo "  clean         Remove venv and caches"

venv:
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip

install: venv
	$(BIN)/pip install -e .

install-dev: venv
	$(BIN)/pip install -e ".[dev]"

lint:
	$(BIN)/ruff check src tests
	$(BIN)/ruff format --check src tests

test:
	$(BIN)/pytest

eval:
	$(BIN)/python -m shopping_agent.evals.runner

run:
	$(BIN)/harbour-basket $(ARGS)

mcp:
	$(BIN)/harbour-basket-mcp

docker-build:
	docker build -t harbour-basket-agent:local .

clean:
	rm -rf $(VENV) .pytest_cache .ruff_cache src/*.egg-info *.egg-info
