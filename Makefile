PYTHON ?= python
VENV_DIR ?= .venv
VENV_PYTHON := $(VENV_DIR)\Scripts\python.exe

.DEFAULT_GOAL := help

.PHONY: help install-dev test lint format

help:
	@echo "make install-dev"
	@echo "make test"
	@echo "make lint"
	@echo "make format"

install-dev:
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -e ".[dev]"

test:
	$(VENV_PYTHON) -m pytest governance

lint:
	$(VENV_PYTHON) -m ruff check governance

format:
	$(VENV_PYTHON) -m ruff format governance

