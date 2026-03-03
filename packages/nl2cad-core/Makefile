# nl2cad-core — Developer Makefile
.PHONY: install test test-v clean
PYTHON := python3
install:
	pip install -e ".[dev]"
test:
	$(PYTHON) -m pytest tests/ --tb=short -q
test-v:
	$(PYTHON) -m pytest tests/ --tb=short -v
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
