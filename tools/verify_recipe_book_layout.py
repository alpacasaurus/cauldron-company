#!/usr/bin/env python3
"""Verify recipe book icon rows fit inside the overlay card."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from witches.hudicons import RecipeBookOverlay, recipe_book_sections


def main():
    layout = RecipeBookOverlay.layout_metrics()
    potions, weapons, food = recipe_book_sections()
    split = (len(potions) + 1) // 2
    errors = []

    left, right, bottom, top = layout["bounds"]
    pad = layout["pad"]
    half = layout["row_half"]

    def check_col(label, center_x, rows, start_y):
        if center_x - half < left:
            errors.append(f"{label} overflows left")
        if center_x + half > right:
            errors.append(f"{label} overflows right")
        end_y = start_y - (max(len(rows), 1) - 1) * layout["row_step"]
        if end_y - half < bottom + pad:
            errors.append(f"{label} overflows bottom")

    check_col("potion-left", layout["potion_cols"][0], potions[:split], layout["content_top"])
    check_col("potion-right", layout["potion_cols"][1], potions[split:], layout["content_top"])
    check_col("gear", layout["gear_col"], weapons + food, layout["gear_top"])

    if errors:
        print("FAIL")
        for err in errors:
            print(" ", err)
        print("layout", layout)
        return 1

    print("ok", layout["card_w"], layout["card_h"], "rows", len(potions), len(weapons), len(food))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
