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
CLOTH_GREEN = _qcolor((36, 120, 72))
CLOTH_RED = _qcolor((160, 48, 48))
CLOTH_WHITE = _qcolor((240, 240, 240))
CLOTH_DARK = _qcolor((44, 44, 56))
ROBE_ORANGE = _qcolor((214, 120, 32))
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


def _thief(p: QPainter) -> None:
    # hooded cloak
    _fill(p, 8, 0, 8, 3, CLOTH_DARK)
    # dark tunic
    _fill(p, 8, 7, 8, 9, CLOTH_DARK)
    # belt
    _fill(p, 10, 13, 4, 2, LEATHER)
    # dagger (right hand)
    _fill(p, 19, 6, 1, 4, STEEL)
    # pouch (left)
    _fill(p, 6, 12, 2, 2, LEATHER)


def _crafter(p: QPainter) -> None:
    # apron over tunic
    _fill(p, 8, 7, 8, 9, CLOTH_BLUE)
    _fill(p, 10, 8, 4, 8, LEATHER)
    # hammer (right)
    _fill(p, 19, 8, 1, 4, WOOD)
    _fill(p, 18, 8, 2, 1, STEEL)
    # tool pouch (left)
    _fill(p, 6, 13, 2, 3, LEATHER)


def _merchant(p: QPainter) -> None:
    # fine coat
    _fill(p, 8, 7, 8, 9, CLOTH_GREEN)
    # trim
    _fill(p, 8, 7, 8, 1, GOLD)
    # coin (right)
    _fill(p, 19, 9, 1, 1, GOLD)
    # satchel (left)
    _fill(p, 5, 10, 3, 3, LEATHER)


def _priest(p: QPainter) -> None:
    # white robe
    _fill(p, 7, 7, 10, 12, CLOTH_WHITE)
    # sash
    _fill(p, 10, 14, 4, 1, GOLD)
    # staff (left)
    _fill(p, 5, 5, 1, 12, WOOD)
    _fill(p, 4, 4, 3, 1, GOLD)


def _ranger(p: QPainter) -> None:
    # green cloak
    _fill(p, 7, 6, 10, 10, CLOTH_GREEN)
    # bow (right)
    _fill(p, 19, 6, 1, 10, WOOD)
    # quiver (back)
    _fill(p, 8, 8, 2, 5, LEATHER)


def _barbarian(p: QPainter) -> None:
    # bare chest with leather harness
    _fill(p, 8, 7, 8, 6, SKIN)
    _fill(p, 10, 9, 4, 1, LEATHER)
    # fur kilt
    _fill(p, 8, 13, 8, 3, LEATHER)
    # axe (right)
    _fill(p, 18, 8, 1, 6, WOOD)
    _fill(p, 17, 8, 3, 2, STEEL)


def _paladin(p: QPainter) -> None:
    # bright armor with gold trim
    _fill(p, 8, 7, 8, 6, STEEL)
    _fill(p, 8, 7, 8, 1, GOLD)
    # hammer (right)
    _fill(p, 19, 7, 1, 6, WOOD)
    _fill(p, 18, 7, 3, 2, STEEL)


def _druid(p: QPainter) -> None:
    # nature robe
    _fill(p, 7, 7, 10, 12, CLOTH_GREEN)
    # staff with leaf
    _fill(p, 5, 5, 1, 12, WOOD)
    _fill(p, 4, 6, 1, 1, CLOTH_GREEN)


def _necromancer(p: QPainter) -> None:
    # dark robe with purple trim
    _fill(p, 7, 7, 10, 12, CLOTH_DARK)
    _fill(p, 7, 7, 10, 1, CLOTH_PURPLE)
    # skull-topped staff
    _fill(p, 5, 5, 1, 12, WOOD)
    _fill(p, 4, 4, 3, 2, CLOTH_WHITE)


def _bard(p: QPainter) -> None:
    # colorful coat
    _fill(p, 8, 7, 8, 9, CLOTH_RED)
    # lute (left)
    _fill(p, 5, 10, 3, 2, WOOD)
    _fill(p, 7, 10, 1, 3, WOOD)


def _monk(p: QPainter) -> None:
    # simple robe
    _fill(p, 7, 7, 10, 12, ROBE_ORANGE)
    # sash
    _fill(p, 10, 14, 4, 1, LEATHER)


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
    elif "thief" in key or "rogue" in key or key in {"assassin"}:
        variant = "thief"
    elif "craft" in key or key in {"crafter", "artisan", "blacksmith"}:
        variant = "crafter"
    elif "merchant" in key or "trader" in key or key in {"vendor"}:
        variant = "merchant"
    elif "priest" in key or "cleric" in key or key in {"acolyte"}:
        variant = "priest"
    elif "ranger" in key or "archer" in key or "hunter" in key:
        variant = "ranger"
    elif "barbarian" in key or "berserker" in key:
        variant = "barbarian"
    elif "paladin" in key or "templar" in key:
        variant = "paladin"
    elif "druid" in key or "warden" in key or "shaman" in key:
        variant = "druid"
    elif "necromancer" in key or "warlock" in key:
        variant = "necromancer"
    elif "bard" in key or "minstrel" in key:
        variant = "bard"
    elif "monk" in key:
        variant = "monk"
    else:
        variant = "fighter"

    img = _make_canvas()
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, False)
    _draw_base(p)
    if variant == "fighter":
        _fighter(p)
    elif variant == "wizard":
        _wizard(p)
    elif variant == "thief":
        _thief(p)
    elif variant == "crafter":
        _crafter(p)
    elif variant == "merchant":
        _merchant(p)
    elif variant == "priest":
        _priest(p)
    elif variant == "ranger":
        _ranger(p)
    elif variant == "barbarian":
        _barbarian(p)
    elif variant == "paladin":
        _paladin(p)
    elif variant == "druid":
        _druid(p)
    elif variant == "necromancer":
        _necromancer(p)
    elif variant == "bard":
        _bard(p)
    elif variant == "monk":
        _monk(p)
    else:
        _fighter(p)
    p.end()
    return _scale_to_pixmap(img, SCALE)


def sample_size() -> QSize:
    return QSize(24 * SCALE, 32 * SCALE)
