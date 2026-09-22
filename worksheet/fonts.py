"""Resolve worksheet fonts and embed bundled or user-supplied TrueType faces."""

import hashlib
from collections.abc import Callable
from pathlib import Path
from typing import cast

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import getRegisteredFontNames
from reportlab.pdfbase.ttfonts import TTFError, TTFont

DEFAULT_FONT = "Andika"
"""Default worksheet face, bundled as the unmodified Andika Regular 7.000 font."""


def resolve_font(font: str = DEFAULT_FONT) -> str:
    """Return a ReportLab font name, registering a TrueType font when necessary.

    Args:
        font: ``Andika``, a standard PDF font name (e.g. ``Helvetica`` or
            ``Times-Roman``), an already registered ReportLab font name, or a
            local ``.ttf`` path. Names are case-sensitive. Relative paths resolve
            against the current working directory; ``~`` expands to the home.

    Returns:
        A registered font name used consistently for measuring and rendering.
        Custom files receive path-derived names, so identical basenames in
        different directories do not overwrite each other in the registry.

    Raises:
        ValueError: If the name is unknown or a font file is missing, unreadable,
            or not a supported TrueType font. No silent fallback is performed.

    Side Effects:
        Lazily reads font files and registers them in ReportLab's process-wide
        registry. TrueType fonts are subset-embedded when a PDF is saved. No
        network access or system-font installation/discovery is performed.
    """
    if (
        font in cast(tuple[str, ...], pdfmetrics.standardFonts)
        or font in getRegisteredFontNames()
    ):
        return font
    if font == DEFAULT_FONT:
        path = Path(__file__).parent / "data" / "fonts" / "Andika-Regular.ttf"
        name = DEFAULT_FONT
    else:
        path = Path(font).expanduser()
        if path.suffix.lower() != ".ttf":
            raise ValueError(
                f"unknown font {font!r}; use Andika, a standard PDF font name, or a .ttf path"
            )
        path = path.resolve()
        name = "worksheet-" + hashlib.sha256(str(path).encode("utf-8")).hexdigest()
    if name not in getRegisteredFontNames():
        try:
            cast(Callable[[TTFont], None], pdfmetrics.registerFont)(
                TTFont(name, str(path))
            )
        except (OSError, TTFError) as error:
            raise ValueError(
                f"cannot load TrueType font {str(path)!r}: {error}"
            ) from error
    return name
