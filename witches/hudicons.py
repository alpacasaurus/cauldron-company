"""Compact pixel-art HUD icons for ingredients, outcomes, and gear."""

from ursina import Entity, Text, color

from witches.catalog import (
    FOOD_RECIPES,
    INGREDIENTS,
    RECIPES,
    WEAPON_DISPLAY,
    WEAPON_RECIPES,
    format_recipe_options,
    stir_bar,
)
from witches.glfix import portable_unlit
from witches.iconart import ensure_hud_icons, icon_texture
from witches.teardown import destroy_tree
from witches.uistyle import (
    X_CAULDRON,
    X_PLAYER_L,
    X_PLAYER_R,
    X_RECIPE,
    Y_CAULDRON_ICONS,
    Y_CAULDRON_META,
    Y_PLAYER_CARRIED,
    Y_PLAYER_ICONS,
    Y_PLAYER_NAME,
    Y_PLAYER_POCKETS,
    Z_HUD_ICON,
    Z_OVERLAY_BACK,
    Z_OVERLAY_ICON,
    Z_OVERLAY_PANEL,
    Z_OVERLAY_TEXT,
    hud_panel,
    s,
    tinted_panel,
)


def ingredient_name(ingredient_id):
    return INGREDIENTS[ingredient_id]["name"]


def item_chip(item):
    return item["id"]


def arrow_chip():
    return "arrow"


def outcome_chip(outcome_kind, value=0):
    overlay = None
    if outcome_kind == "potion" and value:
        overlay = str(value)
    elif outcome_kind == "food" and value:
        overlay = str(value)
    return outcome_kind, overlay


def outcome_label(outcome_kind, value=0):
    if outcome_kind == "potion":
        return f"potion {value}" if value else "potion"
    if outcome_kind == "food":
        return f"food +{value}" if value else "food"
    if outcome_kind == "bow":
        return "Union Bow"
    if outcome_kind == "pistol":
        return "Dewpoint Pistol"
    return outcome_kind


def classify_outcome(a, b):
    key = frozenset([a, b])
    if key in WEAPON_RECIPES:
        return WEAPON_RECIPES[key], 0
    if key in FOOD_RECIPES:
        return "food", FOOD_RECIPES[key][1]
    if key in RECIPES:
        return "potion", RECIPES[key][2]
    return None, 0


def hud_recipe_icon_rows(max_rows=5):
    rows = []
    for ids, (_name, _effect, value) in sorted(
        RECIPES.items(), key=lambda item: (-item[1][2], item[1][0])
    ):
        if value >= 3:
            rows.append({"ids": sorted(ids), "kind": "potion", "value": value})
    for ids, weapon_id in sorted(WEAPON_RECIPES.items()):
        rows.append({"ids": sorted(ids), "kind": weapon_id, "value": 0})
    for ids, (_name, healing) in sorted(FOOD_RECIPES.items(), key=lambda item: item[1][0]):
        rows.append({"ids": sorted(ids), "kind": "food", "value": healing})
    for ids, (_name, _effect, value) in sorted(RECIPES.items(), key=lambda item: item[1][0]):
        if value == 2 and len(rows) < max_rows:
            rows.append({"ids": sorted(ids), "kind": "potion", "value": value})
    return rows[:max_rows]


def _chip_spec(chip):
    if isinstance(chip, tuple):
        icon_id, overlay = chip
        return icon_id, overlay
    return chip, None


RECIPE_SLOTS = 4
POCKET_SLOTS = 3
CARRIED_SLOTS = 4


def recipe_row_slots(row):
    ids = list(row["ids"][:2])
    while len(ids) < 2:
        ids.append(None)
    return [ids[0], ids[1], "arrow", outcome_chip(row["kind"], row["value"])]


def missing_ingredient_id(known_ids):
    opts = format_recipe_options(known_ids, max_items=1)
    if not opts:
        return None
    missing_name = opts.split("->", 1)[0].strip()
    for ingredient_id, spec in INGREDIENTS.items():
        if spec["name"] == missing_name:
            return ingredient_id
    return None


def row_width(badge_cls):
    return (RECIPE_SLOTS - 1) * badge_cls.spacing()


def show_slot_row(strip, slots, center_x, y, z=Z_HUD_ICON):
    badge_cls = strip.badges[0].__class__ if strip.badges else IconBadge
    spacing = badge_cls.spacing()
    x0 = center_x - row_width(badge_cls) * 0.5
    for i, badge in enumerate(strip.badges):
        if i >= RECIPE_SLOTS:
            badge.hide()
            continue
        slot = slots[i] if i < len(slots) else None
        x = x0 + i * spacing
        if slot:
            icon_id, overlay = _chip_spec(slot)
            badge.place(x, y, icon_id, overlay, z=z)
        else:
            badge.place_empty(x, y, z=z)


def show_fixed_row(strip, slots, x0, y, count, z=Z_HUD_ICON):
    spacing = strip.badges[0].__class__.spacing()
    for i in range(count):
        slot = slots[i] if i < len(slots) else None
        x = x0 + i * spacing
        if slot:
            icon_id, overlay = _chip_spec(slot)
            strip.badges[i].place(x, y, icon_id, overlay, z=z)
        else:
            strip.badges[i].place_empty(x, y, z=z)
    for i in range(count, len(strip.badges)):
        strip.badges[i].hide()


def pocket_slot_chips(inventory):
    chips = [item_chip(item) for item in inventory[:POCKET_SLOTS]]
    while len(chips) < POCKET_SLOTS:
        chips.append(None)
    return chips


def carried_slot_chips(player):
    chips = []
    if player.flask:
        chips.append(outcome_chip("potion", player.flask["value"]))
    if player.meal:
        chips.append(outcome_chip("food", player.meal["healing"]))
    if player.weapon:
        chips.append(outcome_chip(player.weapon, 0))
    if player.effects:
        chips.append(("warning", str(len(player.effects))))
    return chips


class IconBadge:
    ICON_SCALE = s(0.042)
    BACKDROP_PAD = 1.12
    ICON_GAP = s(0.018)
    ARROW_WIDTH_MUL = 0.9
    ARROW_ASPECT = 2.5
    ARROW_UV_FLIP = 1
    ARROW_GOLD = color.hsv(48, 0.85, 1)
    ARROW_GOLD_HI = color.hsv(48, 0.55, 1)

    @classmethod
    def spacing(cls):
        return cls.ICON_SCALE * cls.BACKDROP_PAD + cls.ICON_GAP

    def __init__(self, parent):
        ensure_hud_icons()
        self.root = Entity(parent=parent, enabled=False)
        backdrop_scale = self.ICON_SCALE * self.BACKDROP_PAD
        self.backdrop = Entity(
            parent=self.root,
            model="quad",
            scale=(backdrop_scale, backdrop_scale),
            color=color.rgba(0, 0, 0, 0.62),
            z=0.001,
        )
        self.gem = Entity(
            parent=self.root,
            model="quad",
            scale=(self.ICON_SCALE, self.ICON_SCALE),
            color=color.white,
            shader=portable_unlit,
            double_sided=True,
        )
        self.shaft = Entity(
            parent=self.root,
            model="quad",
            enabled=False,
            shader=portable_unlit,
            double_sided=True,
        )
        self.head = Entity(
            parent=self.root,
            model="quad",
            enabled=False,
            shader=portable_unlit,
            double_sided=True,
        )
        self.label = Text(
            parent=self.root,
            origin=(0.5, -0.5),
            scale=s(0.38),
            color=color.rgba32(255, 255, 255, 255),
            enabled=False,
        )

    def place(self, x, y, icon_id, overlay=None, z=Z_HUD_ICON):
        self.root.enabled = True
        self.root.position = (x, y, z)
        self.root.rotation_z = 0
        self.gem.enabled = True
        if icon_id == "arrow":
            self._place_arrow(z)
            return
        self.backdrop.enabled = True
        backdrop_scale = self.ICON_SCALE * self.BACKDROP_PAD
        self.backdrop.scale = (backdrop_scale, backdrop_scale)
        self.backdrop.color = color.rgba(0, 0, 0, 0.62)
        self.shaft.enabled = False
        self.head.enabled = False
        self.head.rotation_z = 0
        self.gem.texture = icon_texture(icon_id)
        self.gem.texture_scale = (1, 1)
        self.gem.color = color.white
        self.gem.scale = (self.ICON_SCALE, self.ICON_SCALE)
        if overlay:
            self.label.text = overlay
            self.label.enabled = True
            self.label.origin = (0.5, -0.5)
            self.label.scale = s(0.38)
            self.label.color = color.rgba32(255, 255, 255, 255)
            self.label.position = (
                self.ICON_SCALE * 0.38,
                -self.ICON_SCALE * 0.38,
                -0.001,
            )
        else:
            self.label.text = ""
            self.label.enabled = False

    def _place_arrow(self, z):
        arrow_w = self.ICON_SCALE * self.ARROW_WIDTH_MUL
        arrow_h = arrow_w / self.ARROW_ASPECT
        self.backdrop.enabled = True
        self.backdrop.scale = (arrow_w * 1.08, arrow_h * 2.2)
        self.backdrop.color = color.rgba(0, 0, 0, 0.38)
        self.label.enabled = False
        self.gem.enabled = True
        self.gem.texture = icon_texture("arrow")
        self.gem.color = color.white
        self.gem.texture_scale = (self.ARROW_UV_FLIP, 1)
        self.gem.scale = (arrow_w, arrow_h)
        self.gem.position = (0, 0, -0.001)
        self.root.rotation_z = 0

    def place_empty(self, x, y, z=Z_HUD_ICON):
        self.root.enabled = True
        self.root.position = (x, y, z)
        self.root.rotation_z = 0
        backdrop_scale = self.ICON_SCALE * self.BACKDROP_PAD
        self.backdrop.enabled = True
        self.backdrop.scale = (backdrop_scale, backdrop_scale)
        self.backdrop.color = color.rgba(255, 255, 255, 0.08)
        self.gem.enabled = False
        self.shaft.enabled = False
        self.head.enabled = False
        self.head.rotation_z = 0
        self.label.enabled = False

    def hide(self):
        self.root.enabled = False
        self.backdrop.enabled = True
        self.gem.enabled = True
        self.gem.texture_scale = (1, 1)


class IconStrip:
    def __init__(self, parent, badge_count=6):
        self.badges = [IconBadge(parent) for _ in range(badge_count)]

    def show(self, chips, x0, y, spacing=None):
        spacing = spacing or IconBadge.spacing()
        for i, badge in enumerate(self.badges):
            if i < len(chips):
                icon_id, overlay = _chip_spec(chips[i])
                badge.place(x0 + i * spacing, y, icon_id, overlay)
            else:
                badge.hide()

    def show_centered(self, chips, center_x, y, spacing=None):
        spacing = spacing or IconBadge.spacing()
        if not chips:
            self.hide_all()
            return
        x0 = center_x - (len(chips) - 1) * spacing * 0.5
        self.show(chips, x0, y, spacing)

    def hide_all(self):
        for badge in self.badges:
            badge.hide()

    def destroy(self):
        for badge in self.badges:
            destroy_tree(badge.root)


def recipe_book_sections():
    potions = []
    for ids, (_name, _effect, value) in sorted(
        RECIPES.items(), key=lambda item: (-item[1][2], item[1][0])
    ):
        potions.append({"ids": sorted(ids), "kind": "potion", "value": value})
    weapons = []
    for ids, weapon_id in sorted(WEAPON_RECIPES.items(), key=lambda item: WEAPON_DISPLAY[item[1]]):
        weapons.append({"ids": sorted(ids), "kind": weapon_id, "value": 0})
    food = []
    for ids, (_name, healing) in sorted(FOOD_RECIPES.items(), key=lambda item: item[1][0]):
        food.append({"ids": sorted(ids), "kind": "food", "value": healing})
    return potions, weapons, food


def _row_chips(row):
    return recipe_row_slots(row)


class BookIconBadge(IconBadge):
    ICON_SCALE = s(0.031)
    ICON_GAP = s(0.010)
    BACKDROP_PAD = 1.06
    ARROW_WIDTH_MUL = 0.86
    ARROW_ASPECT = 2.7
    ARROW_UV_FLIP = 1


class BookIconStrip(IconStrip):
    def __init__(self, parent, badge_count=RECIPE_SLOTS):
        self.badges = [BookIconBadge(parent) for _ in range(badge_count)]


def _book_row_half_width():
    badge = BookIconBadge
    backdrop = badge.ICON_SCALE * badge.BACKDROP_PAD
    return row_width(badge) * 0.5 + backdrop * 0.5


class RecipeBookOverlay:
    """Full-screen icon recipe reference opened with Tab."""

    CARD_X = 0.0
    CARD_Y = 0.03
    CARD_W = 0.78
    CARD_H = 0.74
    PAD = 0.028
    ROW_STEP = 0.044
    SECTION_GAP = 0.048
    TITLE_TOP = 0.048
    HEADER_RULE_GAP = 0.034
    ROW_START = 0.142
    SECTION_LABEL_LIFT = 0.056
    SECTION_RULE_DROP = 0.022
    FOOD_LABEL_LIFT = 0.026
    FOOD_ROW_DROP = 0.034

    @classmethod
    def layout_metrics(cls):
        row_half = _book_row_half_width()
        inner_left = cls.CARD_X - cls.CARD_W * 0.5 + cls.PAD
        inner_right = cls.CARD_X + cls.CARD_W * 0.5 - cls.PAD
        inner_w = inner_right - inner_left
        col_w = inner_w / 3.0
        potion_cols = (
            inner_left + col_w * 0.5,
            inner_left + col_w * 1.5,
        )
        gear_col = inner_left + col_w * 2.5
        card_top = cls.CARD_Y + cls.CARD_H * 0.5
        card_bottom = cls.CARD_Y - cls.CARD_H * 0.5
        content_top = card_top - cls.ROW_START
        section_label_y = content_top + cls.SECTION_LABEL_LIFT
        section_bottom = card_bottom + 0.042
        section_top = section_label_y + 0.018
        section_mid_y = (section_top + section_bottom) * 0.5
        section_h = section_top - section_bottom
        return {
            "card_w": cls.CARD_W,
            "card_h": cls.CARD_H,
            "pad": cls.PAD,
            "row_step": cls.ROW_STEP,
            "row_half": row_half,
            "col_w": col_w,
            "inner_left": inner_left,
            "inner_right": inner_right,
            "potion_cols": potion_cols,
            "gear_col": gear_col,
            "content_top": content_top,
            "section_label_y": section_label_y,
            "gear_top": content_top,
            "title_y": card_top - cls.TITLE_TOP,
            "header_rule_y": card_top - cls.TITLE_TOP - cls.HEADER_RULE_GAP,
            "footer_y": card_bottom + 0.032,
            "footer_rule_y": card_bottom + 0.054,
            "section_bottom": section_bottom,
            "section_top": section_top,
            "section_mid_y": section_mid_y,
            "section_h": section_h,
            "potion_block_x": sum(potion_cols) / 2,
            "potion_block_w": col_w * 2 - 0.016,
            "gear_block_w": col_w - 0.016,
            "col_divider_x": inner_left + col_w * 2,
            "potion_divider_x": sum(potion_cols) / 2,
            "bounds": (inner_left, inner_right, card_bottom, card_top),
        }

    def __init__(self, parent):
        self.parent = parent
        self.strips = []
        self.entities = []
        layout = self.layout_metrics()
        potions, weapons, food = recipe_book_sections()
        split = (len(potions) + 1) // 2

        self._add(
            hud_panel(
                parent,
                self.CARD_X,
                self.CARD_Y,
                self.CARD_W,
                self.CARD_H,
                alpha=0.93,
                z=Z_OVERLAY_BACK,
            )
        )
        self._add_rule(
            self.CARD_X,
            layout["header_rule_y"],
            self.CARD_W - self.PAD * 2,
            alpha=0.22,
        )
        self._add_text(
            "RECIPE BOOK",
            self.CARD_X,
            layout["title_y"],
            s(0.98),
            color.hsv(280, 0.35, 0.98),
            origin=(0.5, 0.5),
        )

        self._add_section_panel(
            layout["potion_block_x"],
            layout["section_mid_y"],
            layout["potion_block_w"],
            layout["section_h"],
            (72, 36, 108),
            0.2,
        )
        self._add_section_panel(
            layout["gear_col"],
            layout["section_mid_y"],
            layout["gear_block_w"],
            layout["section_h"],
            (88, 64, 28),
            0.16,
        )
        self._add_vrule(
            layout["col_divider_x"],
            layout["section_mid_y"],
            layout["section_h"] - 0.012,
            alpha=0.28,
        )
        self._add_vrule(
            layout["potion_divider_x"],
            layout["section_mid_y"],
            layout["section_h"] - 0.024,
            alpha=0.14,
            thickness=0.0015,
        )

        potion_mid = layout["potion_block_x"]
        self._add_section_label(
            "POTIONS",
            potion_mid,
            layout["section_label_y"],
            s(0.64),
            280,
            0.22,
            width=0.22,
        )
        for col, chunk in zip(layout["potion_cols"], (potions[:split], potions[split:])):
            y = layout["content_top"]
            for row_idx, row in enumerate(chunk):
                self._add_row(parent, row, col, y, row_idx)
                y -= self.ROW_STEP

        self._add_section_label(
            "GEAR",
            layout["gear_col"],
            layout["section_label_y"],
            s(0.64),
            40,
            0.35,
            width=0.14,
        )
        y = layout["gear_top"]
        for row_idx, row in enumerate(weapons):
            self._add_row(parent, row, layout["gear_col"], y, row_idx)
            y -= self.ROW_STEP
        y -= self.SECTION_GAP
        self._add_section_label(
            "FOOD",
            layout["gear_col"],
            y + self.FOOD_LABEL_LIFT,
            s(0.64),
            120,
            0.35,
            width=0.14,
        )
        y -= self.FOOD_ROW_DROP
        food_start = len(weapons)
        for row_idx, row in enumerate(food):
            self._add_row(parent, row, layout["gear_col"], y, food_start + row_idx)
            y -= self.ROW_STEP

        self._add_rule(
            self.CARD_X,
            layout["footer_rule_y"],
            self.CARD_W - self.PAD * 2,
            alpha=0.16,
        )
        self._add_text(
            "Deliver flasks to crate for quota  ·  Tab close  ·  Esc pause",
            self.CARD_X,
            layout["footer_y"],
            s(0.52),
            color.hsv(0, 0, 0.76),
            origin=(0.5, 0),
        )

    def _add_rule(self, x, y, width, thickness=0.0025, rgb=(255, 255, 255), alpha=0.18):
        self._add(
            tinted_panel(
                self.parent,
                x,
                y,
                width,
                thickness,
                rgb,
                alpha,
                z=Z_OVERLAY_PANEL,
            )
        )

    def _add_vrule(self, x, y, height, thickness=0.002, rgb=(255, 255, 255), alpha=0.18):
        self._add(
            tinted_panel(
                self.parent,
                x,
                y,
                thickness,
                height,
                rgb,
                alpha,
                z=Z_OVERLAY_PANEL,
            )
        )

    def _add_section_panel(self, x, y, width, height, rgb, alpha):
        self._add(
            tinted_panel(
                self.parent,
                x,
                y,
                width,
                height,
                rgb,
                alpha,
                z=Z_OVERLAY_PANEL,
            )
        )

    def _add_section_label(self, text, x, y, scale, hue, sat, width):
        self._add_text(
            text,
            x,
            y,
            scale,
            color.hsv(hue, sat, 0.92),
            origin=(0.5, 0.5),
        )
        accent = color.hsv(hue, sat * 0.85, 0.95)
        self._add(
            Entity(
                parent=self.parent,
                model="quad",
                position=(x, y - self.SECTION_RULE_DROP, Z_OVERLAY_PANEL),
                scale=(width, 0.003),
                color=color.rgba(accent.r, accent.g, accent.b, 0.55),
                shader=portable_unlit,
            )
        )

    def _add_row_band(self, center_x, y, row_index):
        band_w = row_width(BookIconBadge) + 0.016
        band_h = self.ROW_STEP * 0.84
        tint = (255, 255, 255) if row_index % 2 == 0 else (0, 0, 0)
        alpha = 0.055 if row_index % 2 == 0 else 0.12
        self._add(
            tinted_panel(
                self.parent,
                center_x,
                y,
                band_w,
                band_h,
                tint,
                alpha,
                z=Z_OVERLAY_PANEL,
            )
        )

    def _add_text(self, text, x, y, scale, tint, origin=(0, 0)):
        self._add(
            Text(
                parent=self.parent,
                text=text,
                x=x,
                y=y,
                z=Z_OVERLAY_TEXT,
                origin=origin,
                scale=scale,
                color=tint,
            )
        )

    def _add(self, entity):
        self.entities.append(entity)
        return entity

    def _add_row(self, parent, row, center_x, y, row_index=0):
        self._add_row_band(center_x, y, row_index)
        strip = BookIconStrip(parent)
        show_slot_row(strip, recipe_row_slots(row), center_x, y, z=Z_OVERLAY_ICON)
        self.strips.append(strip)

    def destroy(self):
        for strip in self.strips:
            strip.destroy()
        for entity in self.entities:
            destroy_tree(entity)
        self.strips.clear()
        self.entities.clear()


class RecipeSidebar:
    ROWS = 5

    def __init__(self, parent):
        sidebar_w = row_width(IconBadge) + 0.08
        self.panel = hud_panel(parent, X_RECIPE, 0.18, sidebar_w, 0.34)
        self.header = Text(
            parent=parent,
            text="RECIPES",
            x=X_RECIPE,
            y=0.34,
            origin=(0.5, 0.5),
            scale=s(0.92),
            color=color.hsv(200, 0.25, 0.95),
        )
        self.footer = Text(
            parent=parent,
            text="Tab = full list",
            x=X_RECIPE,
            y=0.03,
            origin=(0.5, 0.5),
            scale=s(0.58),
            color=color.hsv(200, 0.15, 0.72),
        )
        self.rows = [IconStrip(parent, badge_count=RECIPE_SLOTS) for _ in range(self.ROWS)]

    def refresh(self, rows):
        y = 0.27
        for i, strip in enumerate(self.rows):
            if i >= len(rows):
                strip.hide_all()
                continue
            show_slot_row(strip, recipe_row_slots(rows[i]), X_RECIPE, y)
            y -= 0.054

    def set_enabled(self, enabled):
        self.panel.enabled = enabled
        self.header.enabled = enabled
        self.footer.enabled = enabled
        if enabled:
            pass
        else:
            for strip in self.rows:
                strip.hide_all()

    def destroy(self):
        destroy_tree(self.panel)
        destroy_tree(self.header)
        destroy_tree(self.footer)
        for strip in self.rows:
            strip.destroy()


class PlayerStatusBar:
    def __init__(self, parent, side="left"):
        self.side = side
        self.x = X_PLAYER_L if side == "left" else X_PLAYER_R
        panel_x = self.x + (0.08 if side == "left" else -0.08)
        self.panel = hud_panel(parent, panel_x, Y_PLAYER_POCKETS - 0.018, 0.20, 0.10, alpha=0.42)
        origin = (-0.5, -0.5) if side == "left" else (0.5, -0.5)
        label_origin = (-0.5, 0.5) if side == "left" else (0.5, 0.5)
        label_x = self.x if side == "left" else self.x
        self.name = Text(
            parent=parent,
            text="",
            x=label_x,
            y=Y_PLAYER_NAME,
            origin=label_origin,
            scale=s(0.78),
        )
        self.pocket_label = Text(
            parent=parent,
            text="POCKETS",
            x=label_x,
            y=Y_PLAYER_POCKETS + 0.034,
            origin=label_origin,
            scale=s(0.46),
            color=color.hsv(200, 0.15, 0.78),
        )
        self.carried_label = Text(
            parent=parent,
            text="CARRYING",
            x=label_x,
            y=Y_PLAYER_CARRIED + 0.034,
            origin=label_origin,
            scale=s(0.46),
            color=color.hsv(45, 0.25, 0.82),
        )
        self.pocket_strip = IconStrip(parent, badge_count=POCKET_SLOTS)
        self.carried_strip = IconStrip(parent, badge_count=CARRIED_SLOTS)

    def refresh(self, player, _cauldron_contents):
        spacing = IconBadge.spacing()
        if self.side == "left":
            pocket_x = self.x
            carried_x = self.x + spacing * 0.55
        else:
            pocket_x = self.x - spacing * (POCKET_SLOTS - 1)
            carried_x = self.x - spacing * (POCKET_SLOTS - 1) * 0.5
        self.name.text = f"{player.display_name}  {player.health}/{player.max_health} HP"
        show_fixed_row(
            self.pocket_strip,
            pocket_slot_chips(player.inventory),
            pocket_x,
            Y_PLAYER_POCKETS,
            POCKET_SLOTS,
        )
        carried = carried_slot_chips(player)
        if carried:
            self.carried_label.enabled = True
            self.carried_strip.show_centered(carried, carried_x, Y_PLAYER_CARRIED)
        else:
            self.carried_label.enabled = False
            self.carried_strip.hide_all()
        self.panel.enabled = True

    def destroy(self):
        destroy_tree(self.panel)
        destroy_tree(self.name)
        destroy_tree(self.pocket_label)
        destroy_tree(self.carried_label)
        self.pocket_strip.destroy()
        self.carried_strip.destroy()


class CauldronStatusBar:
    def __init__(self, parent):
        cauldron_w = row_width(IconBadge) + 0.08
        self.panel = hud_panel(parent, X_CAULDRON + 0.04, 0.28, cauldron_w, 0.16)
        self.header = Text(
            parent=parent,
            text="CAULDRON",
            x=X_CAULDRON,
            y=0.36,
            origin=(-0.5, 0.5),
            scale=s(0.82),
            color=color.hsv(110, 0.35, 0.95),
        )
        self.strip = IconStrip(parent, badge_count=RECIPE_SLOTS)
        self.meta = Text(
            parent=parent,
            text="",
            x=X_CAULDRON,
            y=Y_CAULDRON_META,
            origin=(-0.5, 0.5),
            scale=s(0.68),
            color=color.hsv(110, 0.2, 0.9),
        )

    def _show_slots(self, slots, meta):
        center_x = X_CAULDRON + row_width(IconBadge) * 0.5
        show_slot_row(self.strip, slots, center_x, Y_CAULDRON_ICONS)
        self.meta.text = meta

    def refresh(self, contents, stir, brew_ready, brew_lock):
        ids = [item["id"] for item in contents]

        if brew_lock > 0:
            self._show_slots(
                [None, None, "arrow", outcome_chip("potion", 0)],
                f"cooling {brew_lock:.1f}s",
            )
            return
        if brew_ready > 0:
            slots = self._content_slots(ids)
            self._show_slots(slots, f"settling {brew_ready:.1f}s")
            return

        if len(ids) >= 2:
            kind, value = classify_outcome(ids[0], ids[1])
            if not kind:
                kind, value = "potion", 1
            slots = recipe_row_slots({"ids": ids[:2], "kind": kind, "value": value})
            self._show_slots(slots, stir_bar(stir))
        elif len(ids) == 1:
            partner = missing_ingredient_id(ids)
            slots = [ids[0], None, "arrow", partner]
            self._show_slots(slots, "need partner")
        else:
            self._show_slots([None, None, "arrow", None], "dump 2 · stir 8x")

    def _content_slots(self, ids):
        if len(ids) >= 2:
            kind, value = classify_outcome(ids[0], ids[1])
            if not kind:
                kind, value = "potion", 1
            return recipe_row_slots({"ids": ids[:2], "kind": kind, "value": value})
        if len(ids) == 1:
            partner = missing_ingredient_id(ids)
            return [ids[0], None, "arrow", partner]
        return [None, None, "arrow", outcome_chip("potion", 0)]

    def destroy(self):
        destroy_tree(self.panel)
        destroy_tree(self.header)
        destroy_tree(self.meta)
        self.strip.destroy()


def deliver_icon_text(players):
    for player in players:
        if player.flask:
            return f"Deliver +{player.flask['value']} to crate"
    return ""
