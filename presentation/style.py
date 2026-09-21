from __future__ import annotations

from dataclasses import dataclass

from pptx.dml.color import RGBColor


@dataclass(frozen=True)
class UniversityStyle:
    # Values reconstructed from the supplied 16:9 PDF design template.
    gold: RGBColor = RGBColor(189, 154, 82)       # #BD9A52
    gold_dark: RGBColor = RGBColor(181, 147, 81)  # #B59351
    magenta: RGBColor = RGBColor(218, 6, 77)      # #DA064D
    black: RGBColor = RGBColor(26, 23, 27)        # #1A171B
    dark_gray: RGBColor = RGBColor(99, 99, 97)
    mid_gray: RGBColor = RGBColor(160, 160, 160)
    light_gray: RGBColor = RGBColor(236, 236, 236)
    white: RGBColor = RGBColor(255, 255, 255)

    # The PDF specifies Helvetica. Arial is metrically safer across macOS,
    # Windows, LibreOffice, and headless renderers while preserving the look.
    heading_font: str = "Arial"
    body_font: str = "Arial"
    fallback_font: str = "Arial"


STYLE = UniversityStyle()
