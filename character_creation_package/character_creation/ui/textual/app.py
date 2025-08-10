from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import threading
import yaml

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, ListView, ListItem, Checkbox, Button

from ...loaders import (
    stats_loader,
    classes_loader,
    traits_loader,
    races_loader,
    slots_loader,
    appearance_loader,
    resources_loader,
)
from ...loaders import difficulty_loader
from . import state
from ...services.appearance_logic import get_enum_values, get_numeric_bounds
from ...loaders.yaml_utils import load_yaml
from ...loaders.content_packs_loader import (
    load_packs_config,
    load_and_merge_enabled_packs,
    merge_catalogs,
)
from ...services.live_reload import CatalogReloader
from ...services.balance import current_profile


DATA_DIR = Path(__file__).parent.parent.parent / "data"


class NameScreen(Screen):
    BINDINGS = [("escape", "app.quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Step 1: Enter Character Name"),
            Input(placeholder="Name", id="name_input"),
            Static(id="name_error"),
            Horizontal(
                Button("Next", id="next"),
                id="name_buttons",
            ),
            id="name_panel",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "next":
            name_input = self.query_one("#name_input", Input)
            name = (name_input.value or "").strip()
            if not name:
                self.query_one("#name_error", Static).update("Please enter a name.")
                return
            self.app.sel.name = name
            self.app.push_screen("race")


class RaceScreen(Screen):
    BINDINGS = [("escape", "app.quit", "Quit")]

    def compose(self) -> ComposeResult:
        races = state.list_races(self.app.race_catalog)
        items: List[ListItem] = []
        for r in races:
            label = r.get("name") or r.get("id") or "Unknown"
            items.append(ListItem(Static(label)))

        yield Vertical(
            Static("Step 2: Choose Race"),
            ListView(*items, id="race_list"),
            Static(id="race_error"),
            Horizontal(Button("Back", id="back"), Button("Next", id="next")),
        )

    def on_mount(self) -> None:
        lst = self.query_one("#race_list", ListView)
        if self.app.sel.race_index is not None:
            try:
                lst.index = int(self.app.sel.race_index)
            except Exception:
                pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id == "next":
            lst = self.query_one("#race_list", ListView)
            idx = lst.index
            if idx is None or idx < 0:
                self.query_one("#race_error", Static).update("Please select a race.")
                return
            self.app.sel.race_index = int(idx)
            self.app.push_screen("class")


class ClassScreen(Screen):
    BINDINGS = [("escape", "app.quit", "Quit")]

    def compose(self) -> ComposeResult:
        starters = self.app.starter_classes
        items: List[ListItem] = []
        for cls in starters:
            label = cls.get("name") or cls.get("id") or "Unknown"
            items.append(ListItem(Static(label)))

        yield Vertical(
            Static("Step 3: Choose Starting Class"),
            ListView(*items, id="class_list"),
            Static(id="class_error"),
            Horizontal(Button("Back", id="back"), Button("Next", id="next")),
        )

    def on_mount(self) -> None:
        lst = self.query_one("#class_list", ListView)
        # Restore selection if returning
        if 0 <= self.app.sel.class_index < len(self.app.starter_classes):
            try:
                lst.index = self.app.sel.class_index
            except Exception:
                pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id == "next":
            lst = self.query_one("#class_list", ListView)
            idx = lst.index
            if idx is None or idx < 0:
                self.query_one("#class_error", Static).update("Please select a class.")
                return
            self.app.sel.class_index = int(idx)
            self.app.push_screen("traits")


class TraitScreen(Screen):
    BINDINGS = [("escape", "app.quit", "Quit")]

    def compose(self) -> ComposeResult:
        traits = state.list_traits(self.app.trait_catalog)
        checkboxes: List[Checkbox] = []
        for tid, meta in traits:
            label = meta.get("name") or tid
            cb = Checkbox(label, value=False, id=tid)
            if tid in self.app.sel.trait_ids:
                cb.value = True
            checkboxes.append(cb)

        yield Vertical(
            Static(f"Step 4: Choose up to {self.app.traits_max} Traits"),
            Vertical(*checkboxes, id="trait_checks"),
            Static(id="trait_error"),
            Horizontal(Button("Back", id="back"), Button("Next", id="next")),
        )

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        # Enforce max selections from limits
        container = self.query_one("#trait_checks", Vertical)
        checked_ids = {cb.id for cb in container.query(Checkbox) if cb.value}
        max_allowed = int(getattr(self.app, "traits_max", 2))
        if len(checked_ids) > max_allowed:
            # Undo the latest toggle
            event.checkbox.value = False
            self.query_one("#trait_error", Static).update(
                f"You can select at most {max_allowed} traits."
            )
        else:
            self.query_one("#trait_error", Static).update("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id == "next":
            container = self.query_one("#trait_checks", Vertical)
            checked_ids = [cb.id for cb in container.query(Checkbox) if cb.value]
            max_allowed = int(getattr(self.app, "traits_max", 2))
            if len(checked_ids) > max_allowed:
                self.query_one("#trait_error", Static).update(
                    f"Please select at most {max_allowed} traits."
                )
                return
            self.app.sel.trait_ids = checked_ids
            self.app.push_screen("appearance")


class AppearanceScreen(Screen):
    BINDINGS = [("escape", "app.quit", "Quit")]

    def compose(self) -> ComposeResult:
        # Build dynamic inputs based on appearance_fields
        fields = self.app.appearance_fields.get("fields", self.app.appearance_fields)
        rows: List[Any] = []
        base_dir = DATA_DIR / "appearance"

        for fid, meta in fields.items():
            ftype = meta.get("type", "any")
            label = fid
            if ftype == "enum":
                values = get_enum_values(fid, self.app.appearance_fields, base_dir)
                list_items = [ListItem(Static(v)) for v in values]
                rows.append(Static(label))
                rows.append(ListView(*list_items, id=f"enum_{fid}"))
            elif ftype in {"float", "number", "int"}:
                bounds = get_numeric_bounds(fid, self.app.appearance_fields, base_dir)
                hint = ""
                if bounds:
                    hint = f" (min {bounds[0]}, max {bounds[1]})"
                rows.append(Static(label + hint))
                rows.append(Input(placeholder=str(meta.get("default", "")), id=f"num_{fid}"))
            else:
                # Opaque/any: show a readonly default
                rows.append(Static(f"{label}: {meta.get('default')}", id=f"any_{fid}"))

        yield Vertical(
            Static("Step 5: Appearance"),
            Vertical(*rows, id="appearance_rows"),
            Static(id="appearance_error"),
            Horizontal(Button("Back", id="back"), Button("Next", id="next")),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id == "next":
            # Collect selections
            fields = self.app.appearance_fields.get("fields", self.app.appearance_fields)
            base_dir = DATA_DIR / "appearance"
            selection: Dict[str, Any] = {}
            for fid, meta in fields.items():
                ftype = meta.get("type", "any")
                if ftype == "enum":
                    lst = self.query_one(f"#enum_{fid}", ListView)
                    idx = lst.index
                    values = get_enum_values(fid, self.app.appearance_fields, base_dir)
                    if idx is not None and 0 <= idx < len(values):
                        val = values[idx]
                        selection[fid] = None if val == "null" else val
                elif ftype in {"float", "number", "int"}:
                    inp = self.query_one(f"#num_{fid}", Input)
                    raw = (inp.value or "").strip()
                    if raw:
                        bounds = get_numeric_bounds(fid, self.app.appearance_fields, base_dir)
                        try:
                            num = float(raw)
                            if bounds:
                                lo, hi = bounds
                                if num < lo:
                                    num = lo
                                if num > hi:
                                    num = hi
                            selection[fid] = num
                        except Exception:
                            pass
            # Store on app for summary/save
            self.app.appearance_selection = selection
            self.app.push_screen("summary")


class SummaryScreen(Screen):
    BINDINGS = [("escape", "app.quit", "Quit")]

    def compose(self) -> ComposeResult:
        # Build a preview hero to summarize
        preview = state.build_character_from_selections(
            self.app.sel,
            self.app.stat_tmpl,
            self.app.slot_tmpl,
            self.app.appearance_fields,
            self.app.appearance_defaults,
            self.app.resources,
            self.app.class_catalog,
            self.app.trait_catalog,
            self.app.race_catalog,
        )

        # Apply balance to derived stats for preview if available
        try:
            if self.app.balance_profile:
                preview.difficulty = str(self.app.balance_cfg.get("current", "normal"))
                preview.refresh_derived(
                    formulas=self.app.formulas,
                    stat_template=self.app.stat_tmpl,
                    keep_percent=False,
                    balance=self.app.balance_profile,
                )
        except Exception:
            pass

        summary = state.summarize_character(
            preview,
            self.app.starter_classes,
            self.app.sel.class_index,
            self.app.trait_catalog,
            self.app.race_catalog,
        )

        # Short stat preview: first few stats only
        core_stats_items = list(summary.get("core_stats", {}).items())[:5]
        stats_lines = [f"{k}: {v}" for k, v in core_stats_items]
        stats_text = "\n".join(stats_lines)

        # Appearance peek lines
        peek = summary.get("appearance_peek", {}) or {}
        peek_lines = [f"{k}: {v}" for k, v in peek.items()]
        peek_text = "\n".join(peek_lines)

        difficulty_label = (
            str(self.app.balance_cfg.get("current", "")) if self.app.balance_cfg else ""
        )

        content = Vertical(
            Static("Step 6: Summary & Save"),
            Static(f"Name: {summary.get('name', '')}"),
            Static(f"Race: {summary.get('race_label', '')}"),
            Static(f"Class: {summary.get('class_label', '')}"),
            Static(f"Traits: {', '.join(summary.get('traits_labels', []))}"),
            Static(f"Difficulty: {difficulty_label}") if difficulty_label else Static(""),
            Static(f"HP: {summary.get('hp')}  Mana: {summary.get('mana')}"),
            Static("Stats:"),
            Static(stats_text),
            Static("Appearance:"),
            Static(peek_text),
            Static("Save Path (default hero.json):"),
            Input(value="hero.json", id="save_path"),
            Static(id="save_msg"),
            Horizontal(Button("Back", id="back"), Button("Save", id="save")),
        )
        yield content

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id == "save":
            path_input = self.query_one("#save_path", Input)
            path = (path_input.value or "hero.json").strip() or "hero.json"
            try:
                hero = state.build_character_from_selections(
                    self.app.sel,
                    self.app.stat_tmpl,
                    self.app.slot_tmpl,
                    self.app.appearance_fields,
                    self.app.appearance_defaults,
                    self.app.resources,
                    self.app.class_catalog,
                    self.app.trait_catalog,
                    self.app.race_catalog,
                )
                # Apply appearance selection before saving
                try:
                    state.apply_appearance_selection(
                        hero, getattr(self.app, "appearance_selection", {})
                    )
                except Exception:
                    pass
                # Apply balance to derived stats before saving if available
                try:
                    if self.app.balance_profile:
                        hero.difficulty = str(self.app.balance_cfg.get("current", "normal"))
                        hero.refresh_derived(
                            formulas=self.app.formulas,
                            stat_template=self.app.stat_tmpl,
                            keep_percent=False,
                            balance=self.app.balance_profile,
                        )
                except Exception:
                    pass
                hero.to_json(Path(path))
                self.query_one("#save_msg", Static).update(f"Saved to {path}")
            except Exception as exc:
                self.query_one("#save_msg", Static).update(f"Error: {exc}")


class CreationApp(App):
    CSS = ""
    TITLE = "Character Creation"

    def __init__(self) -> None:
        super().__init__()
        # Loaded data
        self.stat_tmpl: Dict[str, Any] = {}
        self.slot_tmpl: Dict[str, Any] = {}
        self.appearance_fields: Dict[str, Any] = {}
        self.appearance_defaults: Dict[str, Any] = {}
        self.resources: Dict[str, Any] = {}
        self.class_catalog: Dict[str, Any] = {}
        self.trait_catalog: Dict[str, Any] = {}
        self.race_catalog: Dict[str, Any] = {}
        # Balance & formulas
        self.balance_cfg: Dict[str, Any] = {}
        self.balance_profile: Dict[str, float] | None = None
        self.formulas: Dict[str, Any] = {}
        # Derived
        self.starter_classes: List[Dict[str, Any]] = []
        # User selections
        self.sel = state.CreationSelections(name="", class_index=0, trait_ids=[])
        self.appearance_selection: Dict[str, Any] = {}
        # Limits
        self.traits_max: int = 2

    def on_mount(self) -> None:
        # Load all YAML at startup
        stats_path = DATA_DIR / "stats" / "stats.yaml"
        classes_path = DATA_DIR / "classes.yaml"
        traits_path = DATA_DIR / "traits.yaml"
        races_path = DATA_DIR / "races.yaml"
        slots_path = DATA_DIR / "slots.yaml"
        fields_path = DATA_DIR / "appearance" / "fields.yaml"
        defaults_path = DATA_DIR / "appearance" / "defaults.yaml"
        resources_path = DATA_DIR / "resources.yaml"
        limits_path = DATA_DIR / "creation_limits.yaml"
        formulas_path = DATA_DIR / "formulas.yaml"
        difficulty_path = DATA_DIR / "difficulty.yaml"

        self.stat_tmpl = stats_loader.load_stat_template(stats_path)
        self.class_catalog = classes_loader.load_class_catalog(classes_path)
        self.trait_catalog = traits_loader.load_trait_catalog(traits_path)
        self.race_catalog = races_loader.load_race_catalog(races_path)
        self.slot_tmpl = slots_loader.load_slot_template(slots_path)
        self.appearance_fields = appearance_loader.load_appearance_fields(fields_path)
        self.appearance_defaults = appearance_loader.load_appearance_defaults(defaults_path)
        self.resources = resources_loader.load_resources(resources_path)
        # Formulas
        try:
            with open(formulas_path, "r", encoding="utf-8") as f:
                self.formulas = yaml.safe_load(f) or {}
        except Exception:
            self.formulas = {}
        # Difficulty profile
        try:
            self.balance_cfg = difficulty_loader.load_difficulty(difficulty_path)
            self.balance_profile = current_profile(self.balance_cfg)
        except Exception:
            self.balance_cfg = {"current": "normal", "difficulties": {}}
            self.balance_profile = None
        # Load creation limits (optional)
        try:
            if limits_path.exists():
                data = load_yaml(limits_path)
            else:
                data = {}
            lm = data.get("limits", data) if isinstance(data, dict) else {}
            self.traits_max = int(lm.get("traits_max", 2))
        except Exception:
            self.traits_max = 2

        # Apply content packs (if any)
        try:
            packs_cfg = load_packs_config(DATA_DIR / "content_packs.yaml")
            merged_overlay = load_and_merge_enabled_packs(DATA_DIR, packs_cfg)
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
                if "appearance_tables" in merged_overlay and isinstance(
                    self.appearance_fields, dict
                ):
                    self.appearance_fields = dict(self.appearance_fields)
                    self.appearance_fields["_extra_appearance_tables"] = merged_overlay[
                        "appearance_tables"
                    ]
        except Exception:
            pass

        self.starter_classes = state.list_starter_classes(self.class_catalog)

        # Register screens and start flow
        self.install_screen(NameScreen(), name="name")
        self.install_screen(RaceScreen(), name="race")
        self.install_screen(ClassScreen(), name="class")
        self.install_screen(TraitScreen(), name="traits")
        self.install_screen(AppearanceScreen(), name="appearance")
        self.install_screen(SummaryScreen(), name="summary")
        self.push_screen("name")

        # Dev live reload
        try:
            dev_cfg_path = DATA_DIR / "dev_config.yaml"
            live_reload_enabled = False
            debounce_ms = 300
            if dev_cfg_path.exists():
                with open(dev_cfg_path, "r", encoding="utf-8") as fh:
                    dev_cfg = yaml.safe_load(fh) or {}
                live_reload_enabled = bool(
                    ((dev_cfg or {}).get("dev") or {}).get("live_reload", False)
                )
                debounce_ms = int(((dev_cfg or {}).get("dev") or {}).get("debounce_ms", 300))
            if live_reload_enabled:
                self._reloader = CatalogReloader(DATA_DIR)

                def _apply_initial():
                    try:
                        cats = self._reloader.reload_once()
                        self.apply_catalogs(cats)
                    except Exception as exc:  # noqa: BLE001
                        print(f"[LiveReload] Initial load failed: {exc}")

                _apply_initial()

                def _watcher():
                    self._reloader.watch(self._on_catalogs_updated, debounce_ms=debounce_ms)

                t = threading.Thread(target=_watcher, daemon=True)
                t.start()
        except Exception:
            # Dev-only path; ignore failures silently
            pass

    # --- Live reload hooks ---
    def apply_catalogs(self, cats: Dict[str, Any]) -> None:
        # Update in-memory catalogs and derived caches
        self.stat_tmpl = cats.get("stats", self.stat_tmpl)
        self.slot_tmpl = cats.get("slots", self.slot_tmpl)
        self.appearance_fields = cats.get("appearance_fields", self.appearance_fields)
        self.appearance_defaults = cats.get("appearance_defaults", self.appearance_defaults)
        self.resources = cats.get("resources", self.resources)
        self.class_catalog = cats.get("class_catalog", self.class_catalog)
        self.trait_catalog = cats.get("trait_catalog", self.trait_catalog)
        self.race_catalog = cats.get("race_catalog", self.race_catalog)

        # Limits
        try:
            lm = cats.get("creation_limits", {})
            lm = lm.get("limits", lm)
            if isinstance(lm, dict):
                self.traits_max = int(lm.get("traits_max", self.traits_max))
        except Exception:
            pass

        # Derived starters
        self.starter_classes = state.list_starter_classes(self.class_catalog)

        # Refresh mounted lists if present
        try:
            # Race list
            race_list = self.screen.query_one("#race_list", ListView)
            race_items: List[ListItem] = []
            for r in state.list_races(self.race_catalog):
                lbl = r.get("name") or r.get("id") or "Unknown"
                race_items.append(ListItem(Static(lbl)))
            race_list.clear()
            race_list.extend(race_items)
        except Exception:
            pass
        try:
            # Class list
            class_list = self.screen.query_one("#class_list", ListView)
            class_items: List[ListItem] = []
            for cls in self.starter_classes:
                lbl = cls.get("name") or cls.get("id") or "Unknown"
                class_items.append(ListItem(Static(lbl)))
            class_list.clear()
            class_list.extend(class_items)
        except Exception:
            pass
        try:
            # Trait checks
            trait_checks = self.screen.query_one("#trait_checks", Vertical)
            trait_checks.remove_children()
            for tid, meta in state.list_traits(self.trait_catalog):
                label = meta.get("name") or tid
                cb = Checkbox(label, value=(tid in self.sel.trait_ids), id=tid)
                trait_checks.mount(cb)
        except Exception:
            pass

    def _on_catalogs_updated(
        self, cats: Dict[str, Any], version: int, changes: list
    ) -> None:  # noqa: ANN001
        try:
            self.call_from_thread(self.apply_catalogs, cats)
            self.call_from_thread(self.set_footer, f"Data reloaded (v{version})")
        except Exception:
            pass


def run() -> None:
    CreationApp().run()


if __name__ == "__main__":
    run()
