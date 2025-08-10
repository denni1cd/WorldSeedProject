from __future__ import annotations

"""
Optional launcher for the PySide6 GUI wizard. Does not run in tests.

Usage (worldseed env):
  python scripts/run_qt.py
"""


def main() -> None:  # pragma: no cover - launcher
    from character_creation.ui.qt.app import run

    run()


if __name__ == "__main__":  # pragma: no cover
    main()
