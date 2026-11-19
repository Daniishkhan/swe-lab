# Common tasks. Run `make` or `make help` to list them.
PY ?= python3
VENV := .venv
BIN := $(VENV)/bin

.PHONY: help setup test one progress build serve open

help:
	@echo "make setup      create .venv and install pytest"
	@echo "make test       run every exercise's tests"
	@echo "make one K=lru  run tests whose name matches K (e.g. K=hash_map)"
	@echo "make progress   run tests and show pass counts on the chapter pages"
	@echo "make build      refresh assets/curriculum.js after adding pages or exercises"
	@echo "make serve      serve the site at http://localhost:8000 (file:// works too)"

setup:
	$(PY) -m venv $(VENV)
	$(BIN)/pip install -q -r requirements-dev.txt
	@echo "Done. Activate with: source $(VENV)/bin/activate"

test:
	$(PY) -m pytest

one:
	$(PY) -m pytest -k "$(K)"

progress:
	$(PY) tools/build.py --run-tests

build:
	$(PY) tools/build.py

serve:
	@echo "Open http://localhost:8000"
	$(PY) -m http.server 8000

open:
	open index.html
