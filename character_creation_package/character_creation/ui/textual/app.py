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
    slots_loader,
    appearance_loader,
    resources_loader,
)
from . import state


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
            Static("Step 2: Choose Starting Class"),
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
            Static("Step 3: Choose up to 2 Traits"),
            Vertical(*checkboxes, id="trait_checks"),
            Static(id="trait_error"),
            Horizontal(Button("Back", id="back"), Button("Next", id="next")),
        )

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        # Enforce max 2 selections
        container = self.query_one("#trait_checks", Vertical)
        checked_ids = {cb.id for cb in container.query(Checkbox) if cb.value}
        if len(checked_ids) > 2:
            # Undo the latest toggle
            event.checkbox.value = False
            self.query_one("#trait_error", Static).update("You can select at most 2 traits.")
        else:
            self.query_one("#trait_error", Static).update("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
            return
        if event.button.id == "next":
            container = self.query_one("#trait_checks", Vertical)
            checked_ids = [cb.id for cb in container.query(Checkbox) if cb.value]
            if len(checked_ids) > 2:
                self.query_one("#trait_error", Static).update("Please select at most 2 traits.")
                return
            self.app.sel.trait_ids = checked_ids
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
        )

        summary = state.summarize_character(
            preview, self.app.starter_classes, self.app.sel.class_index, self.app.trait_catalog
        )

        # Short stat preview: first few stats only
        core_stats_items = list(summary.get("core_stats", {}).items())[:5]
        stats_lines = [f"{k}: {v}" for k, v in core_stats_items]
        stats_text = "\n".join(stats_lines)

        content = Vertical(
            Static("Step 4: Summary & Save"),
            Static(f"Name: {summary.get('name', '')}"),
            Static(f"Class: {summary.get('class_label', '')}"),
            Static(f"Traits: {', '.join(summary.get('traits_labels', []))}"),
            Static(f"HP: {summary.get('hp')}  Mana: {summary.get('mana')}"),
            Static("Stats:"),
            Static(stats_text),
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
                )
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
        # Derived
        self.starter_classes: List[Dict[str, Any]] = []
        # User selections
        self.sel = state.CreationSelections(name="", class_index=0, trait_ids=[])

    def on_mount(self) -> None:
        # Load all YAML at startup
        stats_path = DATA_DIR / "stats" / "stats.yaml"
        classes_path = DATA_DIR / "classes.yaml"
        traits_path = DATA_DIR / "traits.yaml"
        slots_path = DATA_DIR / "slots.yaml"
        fields_path = DATA_DIR / "appearance" / "fields.yaml"
        defaults_path = DATA_DIR / "appearance" / "defaults.yaml"
        resources_path = DATA_DIR / "resources.yaml"

        self.stat_tmpl = stats_loader.load_stat_template(stats_path)
        self.class_catalog = classes_loader.load_class_catalog(classes_path)
        self.trait_catalog = traits_loader.load_trait_catalog(traits_path)
        self.slot_tmpl = slots_loader.load_slot_template(slots_path)
        self.appearance_fields = appearance_loader.load_appearance_fields(fields_path)
        self.appearance_defaults = appearance_loader.load_appearance_defaults(defaults_path)
        self.resources = resources_loader.load_resources(resources_path)

        self.starter_classes = state.list_starter_classes(self.class_catalog)

        # Register screens and start flow
        self.install_screen(NameScreen(), name="name")
        self.install_screen(ClassScreen(), name="class")
        self.install_screen(TraitScreen(), name="traits")
        self.install_screen(SummaryScreen(), name="summary")
        self.push_screen("name")


def run() -> None:
    CreationApp().run()


if __name__ == "__main__":
    run()
