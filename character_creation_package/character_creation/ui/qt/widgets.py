# character_creation/ui/qt/widgets.py
from __future__ import annotations
from typing import Dict, Any, List, Callable, Optional
from PySide6.QtCore import Qt, QTimer, QRectF, QSize
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QPen, QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
)
from .sprites import sample_size
from .theme import PALETTE


class ParchmentCard(QFrame):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)


class HeroViewport(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._sprite: Optional[QPixmap] = None
        self._t = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    def set_sprite(self, pm: Optional[QPixmap]):
        self._sprite = pm
        self.update()

    def _tick(self):
        self._t = (self._t + 1) % 2000
        self.update()

    def sizeHint(self) -> QSize:
        s = sample_size()
        return QSize(max(420, s.width() + 80), max(520, s.height() + 140))

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()

        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(240, 232, 210))
        grad.setColorAt(0.7, QColor(229, 216, 188))
        grad.setColorAt(1.0, QColor(221, 205, 176))
        p.fillRect(0, 0, w, h, grad)

        ground = QColor(193, 168, 126)
        p.fillRect(0, int(h * 0.78), w, int(h * 0.22), ground)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(20, 12, 7, 55))
        p.drawRect(0, 0, w, 18)
        p.drawRect(0, h - 18, w, 18)
        p.drawRect(0, 0, 18, h)
        p.drawRect(w - 18, 0, 18, h)

        if self._sprite:
            import math

            bob = int(6 * math.sin(self._t / 15.0))
            sw, sh = self._sprite.width(), self._sprite.height()
            x = (w - sw) // 2
            y = int(h * 0.78) - sh - 12 + bob
            p.drawPixmap(x, y, self._sprite)

        pen = QPen(QColor(PALETTE["border"]))
        pen.setWidth(2)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 12, 12)


class StatGrid(QWidget):
    def __init__(self, title: str, parent: QWidget | None = None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lbl = QLabel(title)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-weight: 700;")
        lay.addWidget(lbl)
        self.body = QLabel("")
        self.body.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.body.setStyleSheet("padding:6px;")
        lay.addWidget(self.body)

    def set_stats(self, stats: Dict[str, Any]):
        keys = [
            k
            for k in [
                "STR",
                "STA",
                "WIS",
                "INT",
                "AUT",
                "CHA",
                "DEX",
                "Placeholder1",
                "Placeholder2",
                "Placeholder3",
                "Placeholder4",
            ]
            if k in stats
        ]
        lines = []
        for k in keys[:8]:
            v = stats[k]
            if isinstance(v, dict) and "base" in v:
                val = v["base"]
            else:
                val = v
            lines.append(f"{k:<4} {val:.2f}" if isinstance(val, (int, float)) else f"{k:<4} {val}")
        self.body.setText("\n".join(lines))


class ClassCardList(QWidget):
    def __init__(
        self, starters: List[Dict[str, Any]], on_selected: Callable[[int], None], parent=None
    ):
        super().__init__(parent)
        self.starters = starters
        self.on_selected = on_selected
        self.list = QListWidget()
        for c in starters:
            name = c.get("name") or c.get("id")
            desc = c.get("desc") or self._fallback_desc(name)
            item = QListWidgetItem()
            item.setSizeHint(QSize(280, 84))
            self.list.addItem(item)
            card = ParchmentCard()
            v = QVBoxLayout(card)
            v.setContentsMargins(10, 8, 10, 8)
            title = QLabel(name)
            title.setStyleSheet("font-weight: 800;")
            body = QLabel(desc)
            body.setWordWrap(True)
            v.addWidget(title)
            v.addWidget(body)
            self.list.setItemWidget(item, card)
        lay = QVBoxLayout(self)
        lay.addWidget(self.list)
        self.list.currentRowChanged.connect(self.on_selected)

    @staticmethod
    def _fallback_desc(name: str) -> str:
        n = (name or "").lower()
        if "fight" in n or "war" in n or "knight" in n:
            return "A stalwart melee specialist clad in steel."
        if "wiz" in n or "mage" in n or "sorc" in n:
            return "A wielder of arcane might and forbidden lore."
        if "rog" in n or "thief" in n:
            return "A swift opportunist striking from the shadows."
        return "A seasoned adventurer."
