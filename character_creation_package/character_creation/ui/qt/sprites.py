# character_creation/ui/qt/sprites.py
from __future__ import annotations
from typing import Tuple
from PySide6.QtGui import QImage, QPainter, QColor, QPixmap
from PySide6.QtCore import Qt, QSize

SCALE = 6  # upscale factor for chunky SNES-like pixels


def _qcolor(rgb: Tuple[int, int, int], a: int = 255) -> QColor:
    r, g, b = rgb
    return QColor(r, g, b, a)


# Palette
INK = _qcolor((62, 39, 35))
SKIN = _qcolor((245, 214, 187))
HAIR = _qcolor((68, 44, 28))
STEEL = _qcolor((168, 174, 186))
LEATHER = _qcolor((120, 80, 40))
CLOTH_PURPLE = _qcolor((113, 69, 179))
CLOTH_BLUE = _qcolor((40, 82, 160))
GOLD = _qcolor((212, 175, 55))
WOOD = _qcolor((99, 68, 38))


def _make_canvas(px_w=24, px_h=32) -> QImage:
    img = QImage(px_w, px_h, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    return img


def _fill(p: QPainter, x: int, y: int, w: int, h: int, c: QColor) -> None:
    p.fillRect(x, y, w, h, c)


def _outline(p: QPainter, x: int, y: int, w: int, h: int, c: QColor = INK) -> None:
    p.setPen(c)
    p.drawRect(x, y, w, h)


def _scale_to_pixmap(img: QImage, scale: int = SCALE) -> QPixmap:
    return QPixmap.fromImage(img).scaled(
        img.width() * scale, img.height() * scale, Qt.KeepAspectRatio, Qt.FastTransformation
    )


def _draw_base(p: QPainter) -> None:
    # head
    _fill(p, 10, 2, 4, 4, SKIN)
    # neck
    _fill(p, 11, 6, 2, 1, SKIN)
    # torso base (tunic)
    _fill(p, 8, 7, 8, 9, CLOTH_BLUE)
    # legs
    _fill(p, 9, 16, 2, 6, CLOTH_BLUE)
    _fill(p, 13, 16, 2, 6, CLOTH_BLUE)
    # boots
    _fill(p, 9, 22, 2, 2, LEATHER)
    _fill(p, 13, 22, 2, 2, LEATHER)
    # arms (neutral)
    _fill(p, 6, 8, 2, 5, SKIN)
    _fill(p, 18, 8, 2, 5, SKIN)
    # hair fringe
    _fill(p, 10, 1, 4, 1, HAIR)


def _fighter(p: QPainter) -> None:
    # helmet
    _fill(p, 9, 1, 6, 2, STEEL)
    _fill(p, 9, 3, 1, 1, STEEL)
    _fill(p, 14, 3, 1, 1, STEEL)
    # chestplate
    _fill(p, 8, 7, 8, 6, STEEL)
    # belt
    _fill(p, 10, 13, 4, 2, LEATHER)
    # pauldrons
    _fill(p, 6, 7, 2, 2, STEEL)
    _fill(p, 18, 7, 2, 2, STEEL)
    # sword (right)
    _fill(p, 19, 5, 1, 6, STEEL)
    _fill(p, 19, 4, 1, 1, GOLD)
    # shield (left)
    _fill(p, 4, 9, 2, 4, WOOD)
    _outline(p, 4, 9, 2, 4, INK)


def _wizard(p: QPainter) -> None:
    # hat
    _fill(p, 8, 0, 8, 2, CLOTH_PURPLE)
    _fill(p, 9, 2, 6, 1, CLOTH_PURPLE)
    # robe
    _fill(p, 7, 7, 10, 12, CLOTH_PURPLE)
    # sash
    _fill(p, 10, 13, 4, 2, GOLD)
    # staff (left hand)
    _fill(p, 5, 5, 1, 12, WOOD)
    _fill(p, 4, 4, 3, 1, GOLD)


def sprite_for_class(class_id_or_name: str) -> QPixmap:
    """
    Return a QPixmap for the given class id/name. Supports 'fighter' and 'wizard'.
    Defaults to 'fighter' if unknown.
    """
    key = (class_id_or_name or "").strip().lower()
    if "fight" in key or key in {"fighter", "warrior", "soldier", "knight"}:
        variant = "fighter"
    elif "wiz" in key or key in {"mage", "wizard", "sorcerer"}:
        variant = "wizard"
    else:
        variant = "fighter"

    img = _make_canvas()
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, False)
    _draw_base(p)
    if variant == "fighter":
        _fighter(p)
    else:
        _wizard(p)
    p.end()
    return _scale_to_pixmap(img, SCALE)


def sample_size() -> QSize:
    return QSize(24 * SCALE, 32 * SCALE)
