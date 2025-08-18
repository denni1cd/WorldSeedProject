from __future__ import annotations

"""
Launcher for the new Aurora Qt UI.

Usage (worldseed env):
  python scripts/run_qt_aurora.py
"""


def main() -> None:  # pragma: no cover
    from character_creation.ui.qt.aurora_app import run_aurora

    run_aurora()


if __name__ == "__main__":  # pragma: no cover
    main()
