from __future__ import annotations

PALETTE = {
    "ink": "#2d2018",
    "ink_soft": "#4e342e",
    "paper": "#efe3cc",
    "paper_card": "rgba(255,255,255,0.75)",
    "border": "#8b6e46",
    "gold": "#d4b483",
    "gold_dark": "#a17b49",
    "accent": "#6a4e23",
    "select_bg": "#dec8a0",
    "select_fg": "#24170f",
}

STYLE = f"""
/* Global ink on parchment */
* {{ color: {PALETTE['ink']}; }}
QMainWindow, QWidget {{
  background: {PALETTE['paper']};
}}
QLabel#banner {{
  font-size: 28px;
  font-weight: 900;
  color: {PALETTE['ink']};
}}
QLabel#stepbar {{
  color: {PALETTE['ink_soft']};
  letter-spacing: 0.5px;
}}
/* Buttons */
QPushButton {{
  background: #e7d3b1;
  border: 1px solid {PALETTE['border']};
  padding: 6px 12px;
  border-radius: 6px;
}}
QPushButton:hover {{ background: #f2e3c9; }}
QPushButton:disabled {{ color: #7a6a58; background: #e9dbc2; }}
/* Lists / Inputs */
QListWidget {{
  background: {PALETTE['paper_card']};
  border: 1px solid {PALETTE['border']};
  outline: none;
}}
QListWidget::item {{ padding: 6px 8px; }}
QListWidget::item:selected {{
  background: {PALETTE['select_bg']};
  color: {PALETTE['select_fg']};
}}
QLineEdit, QTextEdit {{
  background: rgba(255,255,255,0.92);
  border: 1px solid {PALETTE['border']};
  padding: 6px 8px;
  border-radius: 4px;
  selection-background-color: {PALETTE['select_bg']};
  selection-color: {PALETTE['select_fg']};
}}
QFrame#Card {{
  background: {PALETTE['paper_card']};
  border: 1px solid {PALETTE['border']};
  border-radius: 10px;
}}
"""
