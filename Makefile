# nl2cad monorepo — Developer Makefile

.PHONY: install test test-v test-all clean help

PYTHON := python3
PIP    := pip

SUBPACKAGES := nl2cad-core nl2cad-areas nl2cad-brandschutz nl2cad-gaeb nl2cad-nlp

help:
	@echo "Targets:"
	@echo "  install    — pip install -e '.[dev]' (root package)"
	@echo "  test       — pytest root package (quiet)"
	@echo "  test-v     — pytest root package (verbose)"
	@echo "  test-all   — pytest root + all sub-packages"
	@echo "  clean      — remove __pycache__ + .pytest_cache everywhere"

install:
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest tests/ --tb=short -q

test-v:
	$(PYTHON) -m pytest tests/ --tb=short -v

test-all: test
	@for pkg in $(SUBPACKAGES); do \
		echo "\n=== $$pkg ==="; \
		(cd packages/$$pkg && pip install -e ".[dev]" -q && $(PYTHON) -m pytest tests/ --tb=short -q); \
	done
	@echo "\nAll tests done."

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name '*.pyc' -delete 2>/dev/null || true
	@echo "Cleaned."
