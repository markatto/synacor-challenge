.PHONY: all run check test clean fix format lint typecheck

PYTHON = python3

all: check

run:
	$(PYTHON) interpreter.py

# Check everything - linting, formatting, types, and tests
check:
	ruff check interpreter.py disassembler.py
	ruff format --check interpreter.py disassembler.py
	mypy interpreter.py disassembler.py
	$(PYTHON) -m pytest tests/ -v

# Individual checks
test:
	$(PYTHON) -m pytest tests/ -v

typecheck:
	mypy interpreter.py disassembler.py

lint:
	ruff check interpreter.py disassembler.py

format:
	ruff format interpreter.py disassembler.py

# Fix what can be fixed automatically
fix:
	ruff check --fix interpreter.py disassembler.py
	ruff format interpreter.py disassembler.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true