
# character_creation

## Overview
Character-Creation module for WorldSeedProject. This package provides a data-driven character creation system using YAML files for configuration and content.

### Status
- **Phase 0 (Repo skeleton & tooling):** Complete
- **Phase 1 (Data schema & YAML examples):** Complete

### Highlights
- All core YAML data files for stats, traits, slots, resources, classes, and appearance are in place.
- Loader utilities for each data type are implemented.
- Integrity tests validate schema and data consistency.

## Quick Start
```bash
# Install package (editable mode with dev tools)
pip install -e .[dev]

# Run tests
pytest
```

## Project Structure
```
character_creation_package/
├── pyproject.toml
├── README.md
├── .gitignore
├── .editorconfig
├── .pre-commit-config.yaml
├── .github/
│   └── workflows/
│       └── ci.yml
├── character_creation/
│   ├── __init__.py
│   ├── models/
│   │   └── __init__.py
│   ├── loaders/
│   │   ├── __init__.py
│   │   ├── stats_loader.py
│   │   ├── traits_loader.py
│   │   ├── slots_loader.py
│   │   ├── resources_loader.py
│   │   ├── classes_loader.py
│   │   ├── appearance_loader.py
│   │   └── yaml_utils.py
│   └── data/
│       ├── stats/
│       │   └── stats.yaml
│       ├── traits.yaml
│       ├── slots.yaml
│       ├── resources.yaml
│       ├── classes.yaml
│       └── appearance/
│           ├── fields.yaml
│           ├── defaults.yaml
│           ├── tables/
│           │   ├── eye_colors.yaml
│           │   ├── hair_colors.yaml
│           │   ├── genders.yaml
│           │   ├── pronouns.yaml
│           │   ├── species.yaml
│           │   ├── ancestries.yaml
│           │   ├── skin_tones.yaml
│           │   ├── body_types.yaml
│           │   ├── handedness.yaml
│           │   └── voice_profiles.yaml
│           └── ranges/
│               ├── height_human.yaml
│               └── weight_human.yaml
├── scripts/
│   └── .keep
└── tests/
    ├── __init__.py
    ├── test_data_integrity.py
    ├── test_placeholder.py
    └── test_sanity.py
```

## Phase Roadmap
1. Phase 0: Repo skeleton & tooling **(Complete)**
2. Phase 1: Data schema & YAML examples **(Complete)**
3. Phase 2: Models for stats, classes, traits
4. Phase 3: Appearance system
5. Phase 4: Inventory & equipment
6. Phase 5: Loader utilities
7. Phase 6: Validation & error handling
8. Phase 7: CLI tools
9. Phase 8: API integration
10. Phase 9: Documentation & examples
11. Phase 10: Release & maintenance
