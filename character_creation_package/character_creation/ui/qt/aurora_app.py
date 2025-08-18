from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...services.live_reload import CatalogReloader
from .sprites import sprite_for_class, sample_size


def _stem_from_ref(ref: Any) -> str | None:
    # Accept either string path or dict with key 'file'
    if isinstance(ref, str):
        return Path(ref).stem
    if isinstance(ref, dict):
        file_val = ref.get("file")
        if isinstance(file_val, str):
            return Path(file_val).stem
    return None


def _load_numeric_range_from_ref(data_root: Path, ref: Any) -> Tuple[float, float] | None:
    try:
        if isinstance(ref, str):
            p = (data_root / "appearance" / ref).resolve()
        elif isinstance(ref, dict) and isinstance(ref.get("file"), str):
            p = (data_root / "appearance" / ref["file"]).resolve()
        else:
            return None
        import yaml

        with p.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        mn = data.get("min")
        mx = data.get("max")
        if isinstance(mn, (int, float)) and isinstance(mx, (int, float)):
            return float(mn), float(mx)
        return None
    except Exception:
        return None


class AuroraWindow(QMainWindow):
    def __init__(self, loader: CatalogReloader):
        super().__init__()
        self.loader = loader
        self.setWindowTitle("WorldSeed Character Creator")
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.selected_class_id: str | None = None
        self.selected_race_id: str | None = None
        self._stat_widgets: Dict[str, QSpinBox] = {}
        # Summary and selection state widgets
        self.summary_class_label: QLabel | None = None
        self.summary_race_label: QLabel | None = None
        self.summary_traits_label: QLabel | None = None
        self.summary_items_label: QLabel | None = None
        self.summary_stats_form: QFormLayout | None = None
        self.class_list_widget: QListWidget | None = None
        self.race_list_widget: QListWidget | None = None
        self.class_detail_label: QLabel | None = None
        self.race_detail_label: QLabel | None = None
        self.traits_checkboxes: Dict[str, QCheckBox] = {}
        self.traits_counter_label: QLabel | None = None
        self.items_list_widget: QListWidget | None = None
        self.items_filter_combo: QComboBox | None = None
        self._all_items: List[Dict[str, Any]] = []

        # Menu / toolbar actions
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.reload_catalogs)  # type: ignore[arg-type]
        self.menuBar().addAction(refresh_action)

        # Apply basic styling / textures
        try:
            assets = Path(__file__).parent.parent / "assets"
            bg = assets / "scroll.png"
            # Use forward slashes for Qt stylesheets
            bg_url = bg.resolve().as_posix()
            self.setStyleSheet(
                f"""
                QMainWindow {{
                    background-image: url('{bg_url}');
                    background-attachment: fixed;
                    background-position: center;
                    background-repeat: no-repeat;
                }}
                QTabWidget::pane {{
                    border: 2px solid #5c4328;
                    border-radius: 6px;
                    background: rgba(255, 248, 235, 0.92);
                }}
                QGroupBox {{
                    border: 1px solid #7a5a3a;
                    border-radius: 4px;
                    margin-top: 8px;
                    background: rgba(255, 255, 255, 0.9);
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 2px 4px;
                    color: #3e2723;
                }}
                QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{
                    background: rgba(255, 248, 235, 0.9);
                }}
                QListWidget {{
                    background: rgba(255, 255, 255, 0.95);
                    color: #3e2723;
                    border: 1px solid #7a5a3a;
                    border-radius: 4px;
                }}
                QListWidget::item:selected {{
                    background: #ffe0b2;
                    color: #3e2723;
                }}
                QComboBox, QSpinBox, QLineEdit {{
                    background: rgba(255, 255, 255, 0.96);
                    color: #3e2723;
                    border: 1px solid #7a5a3a;
                    border-radius: 4px;
                    padding: 2px 4px;
                }}
                QComboBox QAbstractItemView {{
                    background: #ffffff;
                    color: #3e2723;
                    selection-background-color: #ffe0b2;
                    selection-color: #3e2723;
                }}
                QSpinBox:disabled {{
                    background: rgba(255, 255, 255, 0.96);
                    color: #3e2723;
                }}
                QPushButton {{
                    background-color: #8d6e63;
                    color: white;
                    border: 1px solid #5d4037;
                    border-radius: 4px;
                    padding: 6px 10px;
                }}
                QPushButton:hover {{
                    background-color: #a1887f;
                }}
                QLabel {{
                    color: #3e2723;
                }}
                """
            )
        except Exception:
            pass

        self.catalogs: Dict[str, Any] = {}
        self.reload_catalogs()

    # ---- Catalog and UI building ----
    def reload_catalogs(self) -> None:
        self.catalogs = self.loader.reload_once()
        self._rebuild_tabs()

    def _rebuild_tabs(self) -> None:
        self.tabs.clear()
        cats = self.catalogs

        # Name/summary always present
        if True:
            self.tabs.addTab(self._build_summary_tab(cats), "Summary")

        # Build known tabs if data present
        if cats.get("race_catalog"):
            self.tabs.addTab(self._build_races_tab(cats), "Race")
        if cats.get("class_catalog"):
            self.tabs.addTab(self._build_classes_tab(cats), "Class")
        if cats.get("trait_catalog"):
            self.tabs.addTab(self._build_traits_tab(cats), "Traits")
        if cats.get("appearance_fields"):
            self.tabs.addTab(self._build_appearance_tab(cats), "Appearance")
        if cats.get("items_catalog"):
            self.tabs.addTab(self._build_items_tab(cats), "Items")
        if cats.get("stats"):
            self.tabs.addTab(self._build_stats_tab(cats), "Stats")

        # Add generic tabs for any other available catalogs to keep UI extensible
        known = {
            "race_catalog",
            "class_catalog",
            "trait_catalog",
            "appearance_fields",
            "appearance_tables",
            "items_catalog",
            "stats",
        }
        for key, value in cats.items():
            if key in known:
                continue
            # Skip heavy raw data if needed; otherwise render read-only
            self.tabs.addTab(self._build_generic_tab(key, value), key.replace("_", " ").title())

    # ---- Individual tabs ----
    def _build_summary_tab(self, cats: Dict[str, Any]) -> QWidget:
        root = QWidget()
        layout = QVBoxLayout(root)
        title = QLabel("Create your hero. Tabs update automatically from data and content packs.")
        title.setWordWrap(True)
        layout.addWidget(title)

        # Basic actions
        actions_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh Data")
        refresh_btn.clicked.connect(self.reload_catalogs)  # type: ignore[arg-type]
        actions_layout.addWidget(refresh_btn)
        actions_layout.addStretch(1)
        layout.addLayout(actions_layout)

        # Live selection summary
        grid = QGridLayout()
        self.summary_race_label = QLabel("-")
        self.summary_class_label = QLabel("-")
        self.summary_traits_label = QLabel("0")
        self.summary_items_label = QLabel("0")
        grid.addWidget(QLabel("Race:"), 0, 0)
        grid.addWidget(self.summary_race_label, 0, 1)
        grid.addWidget(QLabel("Class:"), 1, 0)
        grid.addWidget(self.summary_class_label, 1, 1)
        grid.addWidget(QLabel("Traits Selected:"), 2, 0)
        grid.addWidget(self.summary_traits_label, 2, 1)
        grid.addWidget(QLabel("Items Selected:"), 3, 0)
        grid.addWidget(self.summary_items_label, 3, 1)
        layout.addLayout(grid)

        # Current Stats
        stats_group = QGroupBox("Current Stats")
        stats_form = QFormLayout(stats_group)
        self.summary_stats_form = stats_form
        layout.addWidget(stats_group)
        layout.addStretch(1)
        # Fill current stats snapshot
        self._update_summary()
        return root

    def _build_generic_tab(self, key: str, value: Any) -> QWidget:
        root = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        v = QVBoxLayout(container)
        lbl = QLabel(self._pretty(value))
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.setWordWrap(True)
        v.addWidget(lbl)
        v.addStretch(1)
        scroll.setWidget(container)
        outer = QVBoxLayout(root)
        outer.addWidget(scroll)
        return root

    def _pretty(self, value: Any) -> str:
        try:
            import json

            return json.dumps(value, indent=2, ensure_ascii=False)
        except Exception:
            return str(value)

    def _build_races_tab(self, cats: Dict[str, Any]) -> QWidget:
        root = QWidget()
        v = QVBoxLayout(root)
        lst = QListWidget()
        lst.setSelectionMode(QListWidget.SingleSelection)
        races = (cats.get("race_catalog") or {}).get("races", [])
        for r in races:
            if not isinstance(r, dict):
                continue
            name = r.get("name") or r.get("id", "race")
            item = QListWidgetItem(str(name))
            item.setData(Qt.UserRole, r.get("id") or name)
            lst.addItem(item)

        def _on_select() -> None:
            it = lst.currentItem()
            self.selected_race_id = it.data(Qt.UserRole) if it else None
            self._update_race_detail()
            self._recompute_stats()
            self._update_summary()

        lst.itemSelectionChanged.connect(_on_select)
        v.addWidget(lst)
        # Detail box
        detail = QGroupBox("Race Details")
        dlay = QVBoxLayout(detail)
        self.race_detail_label = QLabel("Select a race to see bonuses.")
        self.race_detail_label.setWordWrap(True)
        dlay.addWidget(self.race_detail_label)
        v.addWidget(detail)
        return root

    def _build_classes_tab(self, cats: Dict[str, Any]) -> QWidget:
        root = QWidget()
        v = QVBoxLayout(root)
        lst = QListWidget()
        lst.setViewMode(QListWidget.IconMode)
        lst.setResizeMode(QListWidget.Adjust)
        lst.setMovement(QListWidget.Static)
        lst.setSpacing(12)
        lst.setIconSize(sample_size())
        lst.setSelectionMode(QListWidget.SingleSelection)
        classes = (cats.get("class_catalog") or {}).get("classes", [])
        for idx, c in enumerate(classes):
            if not isinstance(c, dict):
                continue
            name = c.get("name") or c.get("id", f"class_{idx}")
            spx = sprite_for_class(str(name))
            item = QListWidgetItem(QIcon(spx), str(name))
            item.setData(Qt.UserRole, c.get("id") or name)
            lst.addItem(item)

        def _on_select() -> None:
            it = lst.currentItem()
            self.selected_class_id = it.data(Qt.UserRole) if it else None
            self._update_class_detail()
            self._recompute_stats()
            self._update_summary()

        lst.itemSelectionChanged.connect(_on_select)
        v.addWidget(lst)
        # Detail box
        detail = QGroupBox("Class Details")
        dlay = QVBoxLayout(detail)
        self.class_detail_label = QLabel("Select a class to see bonuses.")
        self.class_detail_label.setWordWrap(True)
        dlay.addWidget(self.class_detail_label)
        v.addWidget(detail)
        return root

    def _build_traits_tab(self, cats: Dict[str, Any]) -> QWidget:
        root = QWidget()
        v = QVBoxLayout(root)
        self.traits_checkboxes.clear()
        traits: Dict[str, Any] = (cats.get("trait_catalog") or {}).get("traits", {})
        limits = self.catalogs.get("creation_limits", {}) or {}
        max_traits = None
        if isinstance(limits, dict):
            max_traits = (
                ((limits.get("limits") or {}).get("traits_max"))
                if isinstance(limits.get("limits"), dict)
                else None
            )
        counter = QLabel("0")
        self.traits_counter_label = counter
        if isinstance(max_traits, int):
            v.addWidget(QLabel(f"Select up to {max_traits} traits:"))
        else:
            v.addWidget(QLabel("Select traits:"))
        v.addWidget(QLabel("Selected:"))
        v.addWidget(counter)
        for tid in sorted(traits.keys()):
            cb = QCheckBox(tid)

            def _make_handler(box: QCheckBox) -> Any:
                def _on_toggled(checked: bool) -> None:
                    self._enforce_trait_limit(max_traits, box, checked)
                    self._update_summary()

                return _on_toggled

            cb.toggled.connect(_make_handler(cb))
            self.traits_checkboxes[tid] = cb
            v.addWidget(cb)
        v.addStretch(1)
        return root

    def _build_items_tab(self, cats: Dict[str, Any]) -> QWidget:
        root = QWidget()
        v = QVBoxLayout(root)
        # Filter controls
        top = QHBoxLayout()
        filter_lbl = QLabel("Filter:")
        combo = QComboBox()
        combo.addItem("All")
        # Build type set
        items_raw = (cats.get("items_catalog") or {}).get("items", []) or []
        types: List[str] = []
        for it in items_raw:
            if isinstance(it, dict):
                t = str(it.get("type", "")).strip()
                if t and t not in types:
                    types.append(t)
        for t in sorted(types):
            combo.addItem(t)
        top.addWidget(filter_lbl)
        top.addWidget(combo, 1)
        v.addLayout(top)

        lst = QListWidget()
        self.items_list_widget = lst
        self.items_filter_combo = combo
        self._all_items = [it for it in items_raw if isinstance(it, dict)]

        # populate
        def _populate(filter_type: str | None = None) -> None:
            lst.clear()
            for it in self._all_items:
                t = str(it.get("type", ""))
                if filter_type and filter_type != "All" and t != filter_type:
                    continue
                name = it.get("name") or it.get("id") or "item"
                item = QListWidgetItem(str(name))
                item.setCheckState(Qt.Unchecked)
                item.setData(Qt.UserRole, it.get("id") or name)
                lst.addItem(item)

        _populate("All")

        def _on_filter(idx: int) -> None:
            _populate(combo.currentText())
            self._update_summary()

        combo.currentIndexChanged.connect(_on_filter)

        def _on_click(item: QListWidgetItem) -> None:
            item.setCheckState(Qt.Checked if item.checkState() == Qt.Unchecked else Qt.Unchecked)
            self._update_summary()

        lst.itemClicked.connect(_on_click)
        v.addWidget(lst)
        return root

    def _build_stats_tab(self, cats: Dict[str, Any]) -> QWidget:
        root = QWidget()
        form = QFormLayout(root)
        stats = cats.get("stats") or {}
        self._stat_widgets.clear()
        for key, meta in stats.items():
            if not isinstance(meta, dict):
                continue
            # Start all attributes at 1, as requested
            default = 1
            sp = QSpinBox()
            sp.setRange(1, 9999)
            sp.setValue(int(default))
            sp.setReadOnly(True)
            sp.setButtonSymbols(QSpinBox.NoButtons)
            form.addRow(str(key), sp)
            self._stat_widgets[str(key)] = sp
        # Recompute applying race and class bonuses
        self._recompute_stats()
        return root

    def _build_appearance_tab(self, cats: Dict[str, Any]) -> QWidget:
        root = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        form = QFormLayout(container)

        fields_block = cats.get("appearance_fields") or {}
        spec = fields_block.get("fields", fields_block)
        tables: Dict[str, List[Any]] = cats.get("appearance_tables", {}) or {}
        data_root: Path = self.loader.data_root

        for fid, meta in spec.items():
            if not isinstance(meta, dict):
                continue
            ftype = meta.get("type")
            default_val = meta.get("default")
            if ftype == "enum":
                values: List[str] = []
                # Prefer named tables from appearance_tables if table_ref present
                tname: str | None = None
                if "table_ref" in meta:
                    tname = _stem_from_ref(meta.get("table_ref"))
                if tname and tname in tables:
                    raw_vals = tables.get(tname, []) or []
                    values = [str(v) for v in raw_vals]
                else:
                    # Fall back to inline 'table'
                    inline = meta.get("table") or []
                    values = [str(v) for v in inline] if isinstance(inline, list) else []
                combo = QComboBox()
                for v in values:
                    combo.addItem(v)
                # Set default if available
                try:
                    if default_val is not None:
                        idx = max(0, values.index(str(default_val))) if values else 0
                        combo.setCurrentIndex(idx)
                except Exception:
                    pass
                form.addRow(str(fid), combo)
            elif ftype in {"float", "number", "int"}:
                # Determine range
                rng: Tuple[float, float] | None = None
                if "range" in meta and isinstance(meta["range"], dict):
                    r = meta["range"]
                    mn = r.get("min")
                    mx = r.get("max")
                    if isinstance(mn, (int, float)) and isinstance(mx, (int, float)):
                        rng = (float(mn), float(mx))
                if rng is None and "range_ref" in meta:
                    rng = _load_numeric_range_from_ref(data_root, meta["range_ref"]) or None
                slider = QSlider(Qt.Horizontal)
                slider.setMinimum(0)
                slider.setMaximum(1000)
                # Map range -> slider position
                mn, mx = (0.0, 100.0)
                if rng is not None:
                    mn, mx = rng
                val = float(default_val) if isinstance(default_val, (int, float)) else mn

                def _to_pos(x: float) -> int:
                    if mx <= mn:
                        return 0
                    return int((x - mn) / (mx - mn) * 1000)

                def _from_pos(p: int) -> float:
                    return mn + (mx - mn) * (p / 1000.0)

                slider.setValue(_to_pos(val))
                value_lbl = QLabel(f"{val:.2f}")

                def _on_change(p: int) -> None:
                    value_lbl.setText(f"{_from_pos(p):.2f}")

                slider.valueChanged.connect(_on_change)  # type: ignore[arg-type]
                row = QWidget()
                row_l = QHBoxLayout(row)
                row_l.addWidget(slider)
                row_l.addWidget(value_lbl)
                form.addRow(str(fid), row)
            else:
                # Generic text label for unknown/any
                form.addRow(str(fid), QLabel(str(default_val)))

        scroll.setWidget(container)
        outer = QVBoxLayout(root)
        outer.addWidget(scroll)
        return root

    # ---- Interactions ----
    def _recompute_stats(self) -> None:
        try:
            if not self._stat_widgets:
                return
            # Reset all to base 1
            for sb in self._stat_widgets.values():
                sb.blockSignals(True)
                sb.setValue(1)
                sb.blockSignals(False)

            # Apply race bonuses first
            if self.selected_race_id:
                races = (self.catalogs.get("race_catalog") or {}).get("races", [])
                race = next(
                    (
                        r
                        for r in races
                        if isinstance(r, dict) and r.get("id") == self.selected_race_id
                    ),
                    None,
                )
                if race and isinstance(race, dict):
                    for stat_key, bonus in (race.get("grants_stats") or {}).items():
                        sb = self._stat_widgets.get(str(stat_key))
                        if sb is not None:
                            try:
                                sb.setValue(max(1, int(sb.value() + float(bonus))))
                            except Exception:
                                pass

            # Then class bonuses
            if self.selected_class_id:
                classes = (self.catalogs.get("class_catalog") or {}).get("classes", [])
                clazz = next(
                    (
                        c
                        for c in classes
                        if isinstance(c, dict) and c.get("id") == self.selected_class_id
                    ),
                    None,
                )
                if clazz and isinstance(clazz, dict):
                    for stat_key, bonus in (clazz.get("grants_stats") or {}).items():
                        sb = self._stat_widgets.get(str(stat_key))
                        if sb is not None:
                            try:
                                sb.setValue(max(1, int(sb.value() + float(bonus))))
                            except Exception:
                                pass
            # Update summary snapshot after recompute
            self._update_summary()
        except Exception:
            pass

    def _update_class_detail(self) -> None:
        try:
            if not self.class_detail_label:
                return
            if not self.selected_class_id:
                self.class_detail_label.setText("Select a class to see bonuses.")
                return
            classes = (self.catalogs.get("class_catalog") or {}).get("classes", [])
            c = next(
                (
                    x
                    for x in classes
                    if isinstance(x, dict) and x.get("id") == self.selected_class_id
                ),
                None,
            )
            if not c:
                self.class_detail_label.setText("Select a class to see bonuses.")
                return
            grants = c.get("grants_stats", {}) or {}
            abilities = c.get("grants_abilities", []) or []
            parts: List[str] = []
            if grants:
                parts.append("Stat Bonuses: " + ", ".join(f"{k}+{v}" for k, v in grants.items()))
            if abilities:
                parts.append("Abilities: " + ", ".join(str(a) for a in abilities))
            self.class_detail_label.setText("\n".join(parts) if parts else "No bonuses.")
        except Exception:
            pass

    def _update_race_detail(self) -> None:
        try:
            if not self.race_detail_label:
                return
            if not self.selected_race_id:
                self.race_detail_label.setText("Select a race to see bonuses.")
                return
            races = (self.catalogs.get("race_catalog") or {}).get("races", [])
            r = next(
                (x for x in races if isinstance(x, dict) and x.get("id") == self.selected_race_id),
                None,
            )
            if not r:
                self.race_detail_label.setText("Select a race to see bonuses.")
                return
            grants = r.get("grants_stats", {}) or {}
            abilities = r.get("grants_abilities", []) or []
            parts: List[str] = []
            if grants:
                parts.append("Stat Bonuses: " + ", ".join(f"{k}+{v}" for k, v in grants.items()))
            if abilities:
                parts.append("Abilities: " + ", ".join(str(a) for a in abilities))
            self.race_detail_label.setText("\n".join(parts) if parts else "No bonuses.")
        except Exception:
            pass

    def _enforce_trait_limit(self, max_traits: Any, toggled_box: QCheckBox, checked: bool) -> None:
        # Update counter and enforce maximum if provided
        try:
            selected = sum(1 for cb in self.traits_checkboxes.values() if cb.isChecked())
            # If toggled on and exceeds max, revert
            if isinstance(max_traits, int) and checked and selected > max_traits:
                toggled_box.blockSignals(True)
                toggled_box.setChecked(False)
                toggled_box.blockSignals(False)
                selected -= 1
            if self.traits_counter_label:
                if isinstance(max_traits, int):
                    self.traits_counter_label.setText(f"{selected} / {max_traits}")
                else:
                    self.traits_counter_label.setText(str(selected))
        except Exception:
            pass

    def _update_summary(self) -> None:
        try:
            if self.summary_race_label is not None:
                self.summary_race_label.setText(self.selected_race_id or "-")
            if self.summary_class_label is not None:
                self.summary_class_label.setText(self.selected_class_id or "-")
            if self.summary_traits_label is not None:
                selected = sum(1 for cb in self.traits_checkboxes.values() if cb.isChecked())
                self.summary_traits_label.setText(str(selected))
            if self.summary_items_label is not None and self.items_list_widget is not None:
                count = 0
                for i in range(self.items_list_widget.count()):
                    it = self.items_list_widget.item(i)
                    if it.checkState() == Qt.Checked:
                        count += 1
                self.summary_items_label.setText(str(count))
            # Update stats snapshot
            if self.summary_stats_form is not None and self._stat_widgets:
                while self.summary_stats_form.rowCount():
                    self.summary_stats_form.removeRow(0)
                for k, sb in self._stat_widgets.items():
                    self.summary_stats_form.addRow(QLabel(str(k)), QLabel(str(sb.value())))
        except Exception:
            pass


def run_aurora() -> None:  # pragma: no cover - UI runner
    # Initialize catalogs from package data dir by default; CatalogReloader will fallback
    data_root = Path(__file__).parents[2] / "data"
    loader = CatalogReloader(data_root)
    app = QApplication.instance() or QApplication([])
    win = AuroraWindow(loader)
    win.resize(1000, 700)
    win.show()
    app.exec()
