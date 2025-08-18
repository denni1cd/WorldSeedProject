install:
	pip install -e ".[dev]"; pre-commit install
test:
	pytest -q
fmt:
	black .; ruff check . --fix
lint:
	ruff check .; black --check .
