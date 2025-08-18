from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QCheckBox,
    QFileDialog,
    QMessageBox,
    QScrollArea,
)

from .theme import STYLE
from .widgets import ParchmentCard, HeroViewport, StatGrid, ClassCardList

# from .parchment import ParchmentCard, HeroViewport, StatGrid, ClassCardList
from .sprites import sprite_for_class

# data & model
from character_creation.loaders import (
    stats_loader,
    slots_loader,
    classes_loader,
    traits_loader,
    appearance_loader,
    resources_loader,
    progression_loader,
    races_loader,
)
from character_creation.models.factory import create_new_character

# optional difficulty
try:
    from character_creation.loaders import difficulty_loader
    from character_creation.services.balance import current_profile
except Exception:  # pragma: no cover
    difficulty_loader = None
    current_profile = None


class WizardWindow(QMainWindow):
    def __init__(self, data_root: Path):
        super().__init__()
        self.setWindowTitle("WorldSeed — Hero Forge")
        self.resize(1320, 840)
        self.setStyleSheet(STYLE)

        # --- load data ---
        self.data_root = data_root
        self.stat_tmpl = stats_loader.load_stat_template(
            data_root / "stats" / "stats.yaml"
        )
        self.slot_tmpl = slots_loader.load_slot_template(data_root / "slots.yaml")
        self.class_catalog = classes_loader.load_class_catalog(
            data_root / "classes.yaml"
        )
        self.trait_catalog = traits_loader.load_trait_catalog(data_root / "traits.yaml")
        self.appearance_fields = appearance_loader.load_appearance_fields(
            data_root / "appearance" / "fields.yaml"
        )
        self.appearance_defaults = appearance_loader.load_appearance_defaults(
            data_root / "appearance" / "defaults.yaml"
        )
        self.resources = resources_loader.load_resources(data_root / "resources.yaml")
        self.progression = progression_loader.load_progression(
            data_root / "progression.yaml"
        )
        self.race_catalog = races_loader.load_race_catalog(data_root / "races.yaml")
        import yaml

        self.formulas = yaml.safe_load(
            open(data_root / "formulas.yaml", "r", encoding="utf-8")
        )

        self.balance_cfg = {}
        self.balance_prof = None
        if difficulty_loader and current_profile:
            try:
                self.balance_cfg = difficulty_loader.load_difficulty(
                    data_root / "difficulty.yaml"
                )
                self.balance_prof = current_profile(self.balance_cfg)
            except Exception:
                pass

        # --- selections ---
        self.sel_name = ""
        self.sel_race_idx = -1
        self.sel_class_idx = -1
        self.sel_trait_ids: List[str] = []

        # ---------- Top chrome ----------
        banner = QLabel("On the Parchment: Record Thy Hero")
        banner.setObjectName("banner")
        banner.setAlignment(Qt.AlignCenter)
        stepbar = QLabel("Origin  •  Race  •  Class  •  Traits  •  Summary")
        stepbar.setObjectName("stepbar")
        stepbar.setAlignment(Qt.AlignCenter)

        # ---------- Left: Summary card ----------
        self.summary_card = ParchmentCard()
        llay = QVBoxLayout(self.summary_card)
        llay.setContentsMargins(12, 12, 12, 12)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Hero name")
        self.name_edit.textChanged.connect(self._update_summary)
        self.race_list = QListWidget()
        for r in self.race_catalog.get("races", []):
            self.race_list.addItem(r.get("name") or r.get("id"))
        self.race_list.currentRowChanged.connect(self._on_race_changed)

        self.stat_grid = StatGrid("Attributes")
        llay.addWidget(QLabel("Name"))
        llay.addWidget(self.name_edit)
        llay.addWidget(QLabel("Race"))
        llay.addWidget(self.race_list)
        llay.addWidget(self.stat_grid)

        # ---------- Center: Hero viewport ----------
        center_card = ParchmentCard()
        cv = QVBoxLayout(center_card)
        cv.setContentsMargins(12, 12, 12, 12)
        self.viewport = HeroViewport()
        cv.addWidget(self.viewport)

        # ---------- Right: Class cards + traits ----------
        right_card = ParchmentCard()
        rv = QVBoxLayout(right_card)
        rv.setContentsMargins(12, 12, 12, 12)
        self.starters: List[Dict[str, Any]] = [
            c for c in self.class_catalog.get("classes", []) if not c.get("prereq")
        ]
        self.class_cards = ClassCardList(self.starters, self._on_class_changed)
        trait_area = QScrollArea()
        trait_area.setWidgetResizable(True)
        trait_host = QWidget()
        trait_layout = QVBoxLayout(trait_host)
        self.trait_boxes: List[QCheckBox] = []
        tmap = self.trait_catalog.get("traits", {})
        for tid, meta in sorted(tmap.items()):
            cb = QCheckBox(meta.get("name") or tid)
            cb.setToolTip(meta.get("desc", ""))
            cb.stateChanged.connect(self._limit_traits)
            self.trait_boxes.append(cb)
            trait_layout.addWidget(cb)
        trait_layout.addStretch(1)
        trait_area.setWidget(trait_host)
        rv.addWidget(QLabel("Select Class"))
        rv.addWidget(self.class_cards)
        rv.addWidget(QLabel("Traits (max 2)"))
        rv.addWidget(trait_area, 1)

        # ---------- Bottom: Save / action bar ----------
        save_btn = QPushButton("Save Hero 💾")
        save_btn.clicked.connect(self._save_hero)
        action_bar = QHBoxLayout()
        action_bar.addStretch(1)
        action_bar.addWidget(save_btn)

        # ---------- Root layout ----------
        root = QWidget()
        self.setCentralWidget(root)
        grid = QVBoxLayout(root)
        grid.setContentsMargins(10, 10, 10, 10)
        grid.addWidget(banner)
        grid.addWidget(stepbar)

        body = QHBoxLayout()
        body.setSpacing(10)
        body.addWidget(self.summary_card, 22)
        body.addWidget(center_card, 38)
        body.addWidget(right_card, 32)

        grid.addLayout(body, 1)
        grid.addLayout(action_bar)

        # initial summary + sprite
        self._update_summary()
        self._on_class_changed(0)

    # ---------- Callbacks ----------
    def _on_race_changed(self, row: int):
        self.sel_race_idx = row
        self._update_summary()

    def _on_class_changed(self, row: int):
        if row < 0 and self.starters:
            row = 0
        self.sel_class_idx = row
        # sprite preview
        label = self.starters[row].get("name") or self.starters[row].get("id")
        self.viewport.set_sprite(sprite_for_class(label))
        self._update_summary()

    def _limit_traits(self, _state):
        # enforce max 2
        checked = [b for b in self.trait_boxes if b.isChecked()]
        if len(checked) > 2:
            # uncheck the last one toggled (rough but fine for now)
            sender = self.sender()
            if isinstance(sender, QCheckBox):
                sender.blockSignals(True)
                sender.setChecked(False)
                sender.blockSignals(False)
        self._update_summary()

    def _collect_trait_ids(self) -> List[str]:
        tmap = self.trait_catalog.get("traits", {})
        name_to_id = {(m.get("name") or k): k for k, m in tmap.items()}
        chosen_names = [b.text() for b in self.trait_boxes if b.isChecked()]
        return [name_to_id.get(n, n) for n in chosen_names]

    def _update_summary(self):
        # create a temp hero to show base stats (without saving)
        name = self.name_edit.text().strip() or "Unnamed"
        hero = create_new_character(
            name,
            self.stat_tmpl,
            self.slot_tmpl,
            self.appearance_fields,
            self.appearance_defaults,
            self.resources,
            progression=self.progression,
            formulas=self.formulas,
        )
        # apply chosen race & class & traits for preview
        races = self.race_catalog.get("races", [])
        if 0 <= self.sel_race_idx < len(races):
            hero.set_race(races[self.sel_race_idx]["id"], self.race_catalog)
        if 0 <= self.sel_class_idx < len(self.starters):
            hero.add_class(self.starters[self.sel_class_idx])
        tidz = self._collect_trait_ids()
        if tidz:
            hero.add_traits(tidz, self.trait_catalog)

        if self.balance_prof:
            hero.refresh_derived(
                self.formulas,
                self.stat_tmpl,
                keep_percent=False,
                balance=self.balance_prof,
            )

        self.stat_grid.set_stats(hero.stats)

    # ---------- Save ----------
    def _save_hero(self):
        name = self.name_edit.text().strip() or "Hero"
        races = self.race_catalog.get("races", [])
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Hero", f"saves/{name}.yaml", "YAML files (*.yaml)"
        )
        if not path:
            return
        try:
            hero = create_new_character(
                name,
                self.stat_tmpl,
                self.slot_tmpl,
                self.appearance_fields,
                self.appearance_defaults,
                self.resources,
                progression=self.progression,
                formulas=self.formulas,
            )
            if 0 <= self.sel_race_idx < len(races):
                hero.set_race(races[self.sel_race_idx]["id"], self.race_catalog)
            if 0 <= self.sel_class_idx < len(self.starters):
                hero.add_class(self.starters[self.sel_class_idx])
            tidz = self._collect_trait_ids()
            if tidz:
                hero.add_traits(tidz, self.trait_catalog)
            if self.balance_prof:
                hero.refresh_derived(
                    self.formulas,
                    self.stat_tmpl,
                    keep_percent=False,
                    balance=self.balance_prof,
                )
            hero.save(path)
            QMessageBox.information(self, "Saved", f"Hero saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))


def run():
    import sys

    app = QApplication.instance() or QApplication(sys.argv)
    win = WizardWindow(Path(__file__).parents[2] / "data")
    win.show()
    app.exec()
