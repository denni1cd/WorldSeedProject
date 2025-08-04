items-test:
	pytest -q -k items
install:
	pip install -e .[dev]

lint:
	pre-commit run --all-files

test:
	pytest -q

fmt:
	black .
	ruff --fix .

cov:
	pytest --cov=character_creation --cov-report=term-missing
run-wizard:
	python scripts/create_character.py
