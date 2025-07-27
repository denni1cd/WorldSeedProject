install:
	pip install -e .[dev]

lint:
	pre-commit run --all-files

test:
	pytest -q

fmt:
	black .
	ruff --fix .
