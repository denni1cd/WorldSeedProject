from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

# Import PySide6 only in this optional GUI module
try:  # noqa: SIM105
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QApplication,
        QWidget,
        QLabel,
        QLineEdit,
        QPushButton,
        QVBoxLayout,
        QHBoxLayout,
        QListWidget,
        QListWidgetItem,
        QStackedWidget,
        QComboBox,
        QCheckBox,
        QScrollArea,
        QFileDialog,
        QDoubleSpinBox,
    )
except Exception as _e:  # pragma: no cover - optional dependency
    QApplication = None  # type: ignore[assignment]

from ...loaders import (
    stats_loader,
    classes_loader,
    traits_loader,
    races_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
)
from ...loaders.content_packs_loader import (
    load_packs_config,
    load_and_merge_enabled_packs,
    merge_catalogs,
)
from ...loaders import difficulty_loader
from ...services.balance import current_profile
from ...services.appearance_logic import get_enum_values, get_numeric_bounds
from ...models.factory import create_new_character


GUI_STYLE = """
QWidget { background: #0f0f17; color: #e0d8b0; font-size: 14px; }
QLabel#banner { background: #2a1f1a; color: #e0d8b0; font-weight: bold; padding: 8px; }
QLabel#stepbar { background: #1b1b2f; color: #9ec1a3; padding: 4px; }
QFrame#frame, QWidget#frame { border: 2px solid #7a5b2e; background: #151525; border-radius: 6px; }
QPushButton { background: #3b2e20; color: #e3c77a; padding: 6px 10px; border: 1px solid #7a5b2e; }
QPushButton:hover { background: #4a3a29; }
QLineEdit, QComboBox, QDoubleSpinBox { background: #231f2e; color: #e0d8b0; border: 1px solid #7a5b2e; padding: 4px; }
QListWidget { background: #231f2e; border: 1px solid #7a5b2e; }
QCheckBox { padding: 2px; }
QLabel.error { color: #ff6b6b; font-weight: bold; }
QLabel.hint { color: #9ec1a3; }
"""


class WizardWindow(QWidget):  # pragma: no cover - UI wiring
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("WorldSeed Character Creation")
        self.setStyleSheet(GUI_STYLE)

        # Data
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.stat_tmpl: Dict[str, Any] = {}
        self.slot_tmpl: Dict[str, Any] = {}
        self.appearance_fields: Dict[str, Any] = {}
        self.appearance_defaults: Dict[str, Any] = {}
        self.resources: Dict[str, Any] = {}
        self.class_catalog: Dict[str, Any] = {}
        self.trait_catalog: Dict[str, Any] = {}
        self.race_catalog: Dict[str, Any] = {}
        self.formulas: Dict[str, Any] = {}
        self.balance_cfg: Dict[str, Any] = {}
        self.balance_profile: Dict[str, float] | None = None
        self.traits_max: int = 2

        self._load_all()

        # Selections
        self.sel_name: str = ""
        self.sel_race_idx: int | None = None
        self.sel_class_idx: int = 0
        self.sel_trait_ids: List[str] = []
        self.appearance_selection: Dict[str, Any] = {}

        # UI Layout
        root = QVBoxLayout()
        banner = QLabel("WorldSeed: Character Creation")
        banner.setObjectName("banner")
        banner.setAlignment(Qt.AlignCenter)
        root.addWidget(banner)

        self.stepbar = QLabel(self._render_stepbar("Name"))
        self.stepbar.setObjectName("stepbar")
        self.stepbar.setAlignment(Qt.AlignCenter)
        root.addWidget(self.stepbar)

        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        # Pages
        self.page_name = self._build_name_page()
        self.page_diff = self._build_diff_page()
        self.page_race = self._build_race_page()
        self.page_class = self._build_class_page()
        self.page_traits = self._build_traits_page()
        self.page_appearance = self._build_appearance_page()
        self.page_summary = self._build_summary_page()

        for p in [
            self.page_name,
            self.page_diff,
            self.page_race,
            self.page_class,
            self.page_traits,
            self.page_appearance,
            self.page_summary,
        ]:
            self.stack.addWidget(p)

        self.setLayout(root)
        self.resize(900, 700)

    # --- Data ---
    def _load_all(self) -> None:
        stats_path = self.data_dir / "stats" / "stats.yaml"
        classes_path = self.data_dir / "classes.yaml"
        traits_path = self.data_dir / "traits.yaml"
        races_path = self.data_dir / "races.yaml"
        slots_path = self.data_dir / "slots.yaml"
        fields_path = self.data_dir / "appearance" / "fields.yaml"
        defaults_path = self.data_dir / "appearance" / "defaults.yaml"
        resources_path = self.data_dir / "resources.yaml"
        formulas_path = self.data_dir / "formulas.yaml"
        difficulty_path = self.data_dir / "difficulty.yaml"

        import yaml

        self.stat_tmpl = stats_loader.load_stat_template(stats_path)
        self.class_catalog = classes_loader.load_class_catalog(classes_path)
        self.trait_catalog = traits_loader.load_trait_catalog(traits_path)
        self.race_catalog = races_loader.load_race_catalog(races_path)
        self.slot_tmpl = slots_loader.load_slot_template(slots_path)
        self.appearance_fields = appearance_loader.load_appearance_fields(fields_path)
        self.appearance_defaults = appearance_loader.load_appearance_defaults(defaults_path)
        self.resources = resources_loader.load_resources(resources_path)
        with open(formulas_path, "r", encoding="utf-8") as fh:
            self.formulas = yaml.safe_load(fh) or {}
        # Creation limits (optional)
        try:
            limits_path = self.data_dir / "creation_limits.yaml"
            if limits_path.exists():
                with open(limits_path, "r", encoding="utf-8") as fh:
                    lm = yaml.safe_load(fh) or {}
                lm = lm.get("limits", lm)
                if isinstance(lm, dict) and "traits_max" in lm:
                    self.traits_max = int(lm["traits_max"])  # type: ignore[arg-type]
        except Exception:
            self.traits_max = 2

        # Content packs merge
        packs_cfg = load_packs_config(self.data_dir / "content_packs.yaml")
        merged_overlay = load_and_merge_enabled_packs(self.data_dir, packs_cfg)
        if merged_overlay:
            policy = packs_cfg.get("merge", {}).get("on_conflict", "skip")
            base = {
                "classes": self.class_catalog.get("classes", self.class_catalog),
                "traits": self.trait_catalog.get("traits", self.trait_catalog),
                "races": self.race_catalog.get("races", self.race_catalog),
            }
            merged_all = merge_catalogs(base, merged_overlay, on_conflict=policy)
            if "classes" in merged_all:
                self.class_catalog = {"classes": merged_all["classes"]}
            if "traits" in merged_all:
                self.trait_catalog = {"traits": merged_all["traits"]}
            if "races" in merged_all:
                self.race_catalog = {"races": merged_all["races"]}
            if "appearance_tables" in merged_overlay and isinstance(self.appearance_fields, dict):
                self.appearance_fields = dict(self.appearance_fields)
                self.appearance_fields["_extra_appearance_tables"] = merged_overlay[
                    "appearance_tables"
                ]

        # Difficulty
        self.balance_cfg = difficulty_loader.load_difficulty(difficulty_path)
        self.balance_profile = current_profile(self.balance_cfg)

    # --- Pages ---
    def _build_name_page(self) -> QWidget:
        w = QWidget(objectName="frame")
        lay = QVBoxLayout(w)
        title = QLabel("Enter Character Name")
        title.setAlignment(Qt.AlignCenter)
        inp = QLineEdit()
        hint = QLabel("Please enter a character name.")
        hint.setObjectName("hint")
        hint.setProperty("class", "hint")
        btn = QPushButton("Next")
        btn.setEnabled(False)

        def on_text_changed(text: str) -> None:
            ok = bool(text.strip())
            btn.setEnabled(ok)
            hint.setText("") if ok else hint.setText("Please enter a character name.")

        def go_next() -> None:
            self.sel_name = inp.text().strip()
            if not self.sel_name:
                return
            self.stepbar.setText(self._render_stepbar("Difficulty"))
            self.stack.setCurrentWidget(self.page_diff)

        inp.textChanged.connect(on_text_changed)
        btn.clicked.connect(go_next)
        lay.addWidget(title)
        lay.addWidget(inp)
        lay.addWidget(hint)
        lay.addWidget(btn, alignment=Qt.AlignRight)
        return w

    def _build_diff_page(self) -> QWidget:
        w = QWidget(objectName="frame")
        lay = QVBoxLayout(w)
        title = QLabel("Choose Difficulty")
        title.setAlignment(Qt.AlignCenter)
        cb = QComboBox()
        diffs = list((self.balance_cfg or {}).get("difficulties", {}).keys())
        cb.addItems(diffs)
        if diffs:
            current = str(self.balance_cfg.get("current", diffs[0]))
            try:
                cb.setCurrentIndex(diffs.index(current))
            except Exception:
                pass
        btn_next = QPushButton("Next")
        btn_back = QPushButton("Back")

        def go_back() -> None:
            self.stepbar.setText(self._render_stepbar("Name"))
            self.stack.setCurrentWidget(self.page_name)

        def go_next() -> None:
            chosen = cb.currentText()
            if chosen:
                self.balance_cfg["current"] = chosen
                self.balance_profile = current_profile(self.balance_cfg)
            self.stepbar.setText(self._render_stepbar("Race"))
            self.stack.setCurrentWidget(self.page_race)

        btn_back.clicked.connect(go_back)
        btn_next.clicked.connect(go_next)
        lay.addWidget(title)
        lay.addWidget(cb)
        hb = QHBoxLayout()
        hb.addWidget(btn_back)
        hb.addWidget(btn_next)
        lay.addLayout(hb)
        return w

    def _build_race_page(self) -> QWidget:
        w = QWidget(objectName="frame")
        lay = QVBoxLayout(w)
        title = QLabel("Choose Race")
        title.setAlignment(Qt.AlignCenter)
        lst = QListWidget()
        for r in self.race_catalog.get("races", []) or []:
            label = r.get("name") or r.get("id") or "Unknown"
            item = QListWidgetItem(label)
            lst.addItem(item)
        error = QLabel("")
        error.setProperty("class", "error")

        def go_next() -> None:
            idx = lst.currentRow()
            if idx < 0:
                error.setText("Please select a race to continue.")
                return
            self.sel_race_idx = idx
            self.stepbar.setText(self._render_stepbar("Class"))
            self.stack.setCurrentWidget(self.page_class)

        btn_next = QPushButton("Next")
        btn_next.clicked.connect(go_next)
        lay.addWidget(title)
        lay.addWidget(lst)
        lay.addWidget(error)
        lay.addWidget(btn_next, alignment=Qt.AlignRight)
        return w

    def _build_class_page(self) -> QWidget:
        w = QWidget(objectName="frame")
        lay = QVBoxLayout(w)
        title = QLabel("Choose Starting Class")
        title.setAlignment(Qt.AlignCenter)
        starters = [c for c in self.class_catalog.get("classes", []) if not c.get("prereq")]
        lst = QListWidget()
        for c in starters:
            label = c.get("name") or c.get("id") or "Unknown"
            lst.addItem(QListWidgetItem(label))
        error = QLabel("")
        error.setProperty("class", "error")

        def go_next() -> None:
            idx = lst.currentRow()
            if idx < 0:
                error.setText("Please select a class to continue.")
                return
            self.sel_class_idx = idx
            self.stepbar.setText(self._render_stepbar("Traits"))
            self.stack.setCurrentWidget(self.page_traits)

        btn_next = QPushButton("Next")
        btn_next.clicked.connect(go_next)
        lay.addWidget(title)
        lay.addWidget(lst)
        lay.addWidget(error)
        lay.addWidget(btn_next, alignment=Qt.AlignRight)
        return w

    def _build_traits_page(self) -> QWidget:
        w = QWidget(objectName="frame")
        lay = QVBoxLayout(w)
        title = QLabel("Choose Traits")
        title.setAlignment(Qt.AlignCenter)

        scroller = QScrollArea()
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        scroller.setWidget(inner)
        scroller.setWidgetResizable(True)

        self._trait_checks: List[QCheckBox] = []
        traits = sorted((self.trait_catalog.get("traits", {}) or {}).items(), key=lambda kv: kv[0])
        for tid, meta in traits:
            label = f"{tid}: {meta.get('name') or tid}"
            cb = QCheckBox(label)
            cb.setObjectName(tid)
            self._trait_checks.append(cb)
            inner_lay.addWidget(cb)

        counter = QLabel(f"0/{self.traits_max} selected")
        counter.setProperty("class", "hint")
        error = QLabel("")
        error.setProperty("class", "error")
        btn_next = QPushButton("Next")
        btn_next.setEnabled(True)

        def refresh_state() -> None:
            chosen_ids = [cb.objectName() for cb in self._trait_checks if cb.isChecked()]
            count = len(chosen_ids)
            counter.setText(f"{count}/{self.traits_max} selected")
            if count > self.traits_max:
                error.setText(f"You can select at most {self.traits_max} traits.")
                btn_next.setEnabled(False)
            else:
                error.setText("")
                btn_next.setEnabled(True)

        for cb in self._trait_checks:
            cb.stateChanged.connect(lambda _state: refresh_state())

        def go_next() -> None:
            max_allowed = self.traits_max
            chosen_ids = [cb.objectName() for cb in self._trait_checks if cb.isChecked()]
            chosen_ids = list(dict.fromkeys(chosen_ids))
            if len(chosen_ids) > max_allowed:
                error.setText(f"You can select at most {max_allowed} traits.")
                return
            self.sel_trait_ids = chosen_ids
            self.stepbar.setText(self._render_stepbar("Appearance"))
            self.stack.setCurrentWidget(self.page_appearance)

        btn_next.clicked.connect(go_next)
        lay.addWidget(title)
        lay.addWidget(scroller)
        lay.addWidget(counter)
        lay.addWidget(error)
        lay.addWidget(btn_next, alignment=Qt.AlignRight)
        refresh_state()
        return w

    def _build_appearance_page(self) -> QWidget:
        w = QWidget(objectName="frame")
        lay = QVBoxLayout(w)
        title = QLabel("Appearance")
        title.setAlignment(Qt.AlignCenter)

        self._appearance_controls: Dict[str, QWidget] = {}
        fields = self.appearance_fields.get("fields", self.appearance_fields)
        base_dir = self.data_dir / "appearance"
        for fid, meta in fields.items():
            ftype = meta.get("type", "any")
            if ftype == "enum":
                row = QHBoxLayout()
                row.addWidget(QLabel(fid))
                cb = QComboBox()
                values = get_enum_values(fid, self.appearance_fields, base_dir)
                cb.addItems([str(v) for v in values])
                row.addWidget(cb)
                lay.addLayout(row)
                self._appearance_controls[fid] = cb
            elif ftype in {"float", "number", "int"}:
                row = QHBoxLayout()
                row.addWidget(QLabel(fid))
                spin = QDoubleSpinBox()
                bounds = get_numeric_bounds(fid, self.appearance_fields, base_dir)
                if bounds:
                    spin.setMinimum(float(bounds[0]))
                    spin.setMaximum(float(bounds[1]))
                spin.setDecimals(2)
                row.addWidget(spin)
                lay.addLayout(row)
                self._appearance_controls[fid] = spin

        btn_next = QPushButton("Next")

        def go_next() -> None:
            sel: Dict[str, Any] = {}
            for fid, ctrl in self._appearance_controls.items():
                if isinstance(ctrl, QComboBox):
                    text = ctrl.currentText()
                    sel[fid] = None if text == "null" else text
                elif isinstance(ctrl, QDoubleSpinBox):
                    sel[fid] = float(ctrl.value())
            self.appearance_selection = sel
            self.stepbar.setText(self._render_stepbar("Summary"))
            self.stack.setCurrentWidget(self.page_summary)

        btn_next.clicked.connect(go_next)
        lay.addWidget(title)
        lay.addWidget(btn_next, alignment=Qt.AlignRight)
        return w

    def _build_summary_page(self) -> QWidget:
        w = QWidget(objectName="frame")
        lay = QVBoxLayout(w)
        title = QLabel("Summary & Save")
        title.setAlignment(Qt.AlignCenter)
        self._summary = QLabel("")
        self._summary.setWordWrap(True)
        path_btn = QPushButton("Choose Save Path…")
        save_btn = QPushButton("Save")

        def refresh_preview() -> None:
            hero = self._build_hero()
            # Apply difficulty and derived
            try:
                if self.balance_profile:
                    hero.difficulty = str(self.balance_cfg.get("current", "normal"))
                    hero.refresh_derived(
                        formulas=self.formulas,
                        stat_template=self.stat_tmpl,
                        keep_percent=False,
                        balance=self.balance_profile,
                    )
            except Exception:
                pass
            txt = (
                f"Name: {hero.name}\n"
                f"Race: {hero.race}\n"
                f"Class: {', '.join(hero.classes)}\n"
                f"Traits: {', '.join(hero.traits)}\n"
                f"Difficulty: {getattr(hero, 'difficulty', '')}\n"
                f"HP: {hero.hp:.1f}/{hero.hp_max:.1f}  Mana: {hero.mana:.1f}/{hero.mana_max:.1f}\n"
            )
            self._summary.setText(txt)

        def pick_path() -> None:
            QFileDialog.getSaveFileName(self, "Save Character", "hero.json", "JSON (*.json)")

        def save_now() -> None:
            hero = self._build_hero()
            try:
                if self.balance_profile:
                    hero.difficulty = str(self.balance_cfg.get("current", "normal"))
                    hero.refresh_derived(
                        formulas=self.formulas,
                        stat_template=self.stat_tmpl,
                        keep_percent=False,
                        balance=self.balance_profile,
                    )
            except Exception:
                pass
            # Apply appearance
            try:
                hero.appearance.update(self.appearance_selection)
            except Exception:
                pass
            # Save JSON next to app by default
            hero.to_json(Path("hero.json"))
            refresh_preview()

        path_btn.clicked.connect(pick_path)
        save_btn.clicked.connect(save_now)
        lay.addWidget(title)
        lay.addWidget(self._summary)
        hb = QHBoxLayout()
        hb.addWidget(path_btn)
        hb.addWidget(save_btn)
        lay.addLayout(hb)

        # Update preview when page is shown
        w.showEvent = lambda e: (refresh_preview(), None)
        return w

    # --- Helpers ---
    def _render_stepbar(self, current: str) -> str:
        steps = ["Name", "Difficulty", "Race", "Class", "Traits", "Appearance", "Summary"]
        parts: List[str] = []
        for s in steps:
            if s == current:
                parts.append(f"▶ {s}")
            else:
                parts.append(s)
        return "  »  ".join(parts)

    def _build_hero(self):
        # Build hero with current selections
        fields_spec = self.appearance_fields.get("fields", self.appearance_fields)
        hero = create_new_character(
            self.sel_name or "Hero",
            self.stat_tmpl,
            self.slot_tmpl,
            fields_spec,
            self.appearance_defaults,
            self.resources,
        )
        # Apply race
        if self.sel_race_idx is not None:
            races = list(self.race_catalog.get("races", []))
            if 0 <= self.sel_race_idx < len(races):
                rid = races[self.sel_race_idx].get("id")
                if rid:
                    hero.set_race(rid, self.race_catalog)
        # Apply starting class
        starters = [c for c in self.class_catalog.get("classes", []) if not c.get("prereq")]
        if 0 <= self.sel_class_idx < len(starters):
            hero.add_class(starters[self.sel_class_idx])
        # Apply traits
        hero.add_traits(self.sel_trait_ids, self.trait_catalog)
        return hero


def run() -> None:  # pragma: no cover - UI entry
    if QApplication is None:
        raise RuntimeError(
            "PySide6 is not installed. Please install it to run the GUI: pip install PySide6"
        )
    app = QApplication([])
    # nicer default font
    f = QFont("Georgia", 11)
    app.setFont(f)
    win = WizardWindow()
    win.show()
    app.exec()
