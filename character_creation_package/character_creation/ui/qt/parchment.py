from __future__ import annotations
import random
from PySide6.QtGui import (
    QImage,
    QPixmap,
    QColor,
    QPainter,
    QRadialGradient,
    QLinearGradient,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget


def generate_parchment(size: QSize) -> QPixmap:
    w, h = size.width(), size.height()
    img = QImage(w, h, QImage.Format_ARGB32)
    base = QColor(238, 224, 200)
    img.fill(base)

    p = QPainter(img)
    # subtle noise speckles
    p.setPen(Qt.NoPen)
    for _ in range(int(w * h * 0.003)):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        a = random.randint(15, 35)
        c = QColor(120, 90, 50, a)
        p.setBrush(c)
        p.drawRect(x, y, 1, 1)

    # vignette
    vg = QRadialGradient(w / 2, h / 2, max(w, h) / 1.2)
    vg.setColorAt(0.75, QColor(0, 0, 0, 0))
    vg.setColorAt(1.0, QColor(30, 20, 10, 55))
    p.setBrush(vg)
    p.setPen(Qt.NoPen)
    p.drawRect(0, 0, w, h)

    # top/bottom darker edges
    lg = QLinearGradient(0, 0, 0, h)
    lg.setColorAt(0.0, QColor(0, 0, 0, 40))
    lg.setColorAt(0.15, QColor(0, 0, 0, 0))
    lg.setColorAt(0.85, QColor(0, 0, 0, 0))
    lg.setColorAt(1.0, QColor(0, 0, 0, 40))
    p.setBrush(lg)
    p.drawRect(0, 0, w, h)

    p.end()
    return QPixmap.fromImage(img)


def apply_parchment_background(widget: QWidget) -> None:
    # Use palette background so it scales with window
    pm = generate_parchment(widget.size() if widget.size().isValid() else QSize(1200, 800))
    pal = widget.palette()
    pal.setBrush(widget.backgroundRole(), pm)
    widget.setPalette(pal)
    widget.setAutoFillBackground(True)
