# WorldSeed Combat (Standalone) 
Deterministic, data-driven combat engine. No XP logic (story grants XP).
- Pure Python core (no UI); CLI demo script exists.
- Same stat block for PCs/NPCs/enemies.
- YAML loaders ready; damage/effects/narration to be added in C1+.

## Dev quickstart
Windows: `.\.venv\Scripts\Activate.ps1; pip install -e ".[dev]"; pre-commit install; pytest -q`
macOS/Linux: `source .venv/bin/activate && pip install -e ".[dev]" && pre-commit install && pytest -q`
