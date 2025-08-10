from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

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
from . import state
from ...services.appearance_logic import get_enum_values, get_numeric_bounds
from ...loaders.yaml_utils import load_yaml
from ...loaders.content_packs_loader import (
    load_packs_config,
    load_and_merge_enabled_packs,
    merge_catalogs,
)


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

        content = Vertical(
            Static("Step 6: Summary & Save"),
            Static(f"Name: {summary.get('name', '')}"),
            Static(f"Race: {summary.get('race_label', '')}"),
            Static(f"Class: {summary.get('class_label', '')}"),
            Static(f"Traits: {', '.join(summary.get('traits_labels', []))}"),
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

        self.stat_tmpl = stats_loader.load_stat_template(stats_path)
        self.class_catalog = classes_loader.load_class_catalog(classes_path)
        self.trait_catalog = traits_loader.load_trait_catalog(traits_path)
        self.race_catalog = races_loader.load_race_catalog(races_path)
        self.slot_tmpl = slots_loader.load_slot_template(slots_path)
        self.appearance_fields = appearance_loader.load_appearance_fields(fields_path)
        self.appearance_defaults = appearance_loader.load_appearance_defaults(defaults_path)
        self.resources = resources_loader.load_resources(resources_path)
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


def run() -> None:
    CreationApp().run()


if __name__ == "__main__":
    run()
