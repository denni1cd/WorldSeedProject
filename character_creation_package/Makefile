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

npc-demo:
	python scripts/generate_npcs.py

run-tui:
	python scripts/run_tui.py

xp-demo:
	python scripts/grant_xp.py

regen-demo:
	python scripts/sim_regen.py

effects-demo:
	python scripts/sim_status_effects.py

save-demo:
	python -m scripts.demo_save_load

dev-watch:
	python scripts/dev_watch.py
