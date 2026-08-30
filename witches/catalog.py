"""Ingredient catalog, gossip, and potion name sludge."""

from ursina import color

# Dialogue tiers. Milestones are shift-defining beats, actions are lines a
# player asked for by pressing a key, and ambient is idle scenery chatter that
# stays muted unless someone opts back into it.
DIALOGUE_AMBIENT = 1
DIALOGUE_ACTION = 2
DIALOGUE_MILESTONE = 3

INGREDIENTS = {
    "screamstool": {
        "name": "Screamstool",
        "blurb": "A mushroom that reviews your life choices.",
        "color": color.hsv(330, 0.7, 0.95),
        "behavior": "scream",
        "model": "sphere",
        "scale": 0.45,
    },
    "moonslug": {
        "name": "Moon Slug",
        "blurb": "Photophobic. Judgmental. Delicious?",
        "color": color.hsv(200, 0.35, 0.9),
        "behavior": "flee",
        "model": "sphere",
        "scale": (0.7, 0.28, 0.4),
    },
    "gossipmoss": {
        "name": "Gossip Moss",
        "blurb": "It already told the ferns about your situationship.",
        "color": color.hsv(130, 0.55, 0.55),
        "behavior": "slip",
        "model": "cube",
        "scale": (0.8, 0.12, 0.8),
    },
    "frogchoir": {
        "name": "Frog of Dubious Harmony",
        "blurb": "Knows one note. It is the wrong note.",
        "color": color.hsv(110, 0.75, 0.7),
        "behavior": "hop",
        "model": "sphere",
        "scale": (0.4, 0.28, 0.45),
    },
    "yarncurse": {
        "name": "Cursed Yarnball",
        "blurb": "A familiar's 401(k).",
        "color": color.hsv(20, 0.85, 0.95),
        "behavior": "roll",
        "model": "sphere",
        "scale": 0.38,
    },
    "mandrake": {
        "name": "Mandrake Intern",
        "blurb": "Unpaid. Screams if you make eye contact.",
        "color": color.hsv(25, 0.6, 0.55),
        "behavior": "shy",
        "model": "cube",
        "scale": (0.28, 0.7, 0.28),
    },
    "dew": {
        "name": "Suspicious Dew",
        "blurb": "Condensation with a criminal record.",
        "color": color.hsv(190, 0.4, 1.0),
        "behavior": "idle",
        "model": "sphere",
        "scale": 0.3,
    },
    "breadbone": {
        "name": "Probably a Breadstick",
        "blurb": "The hut swears this is 'osteoporosis of the wheat'.",
        "color": color.hsv(35, 0.45, 0.85),
        "behavior": "idle",
        "model": "cube",
        "scale": (0.15, 0.15, 0.7),
    },
    "gnomecap": {
        "name": "Borrowed Gnome Hat",
        "blurb": "The gnome knows. The gnome is filing paperwork.",
        "color": color.hsv(0, 0.85, 0.85),
        "behavior": "flee",
        "model": "cone",
        "scale": (0.4, 0.55, 0.4),
    },
    "nightmilk": {
        "name": "Night Milk",
        "blurb": "Do not ask which night.",
        "color": color.hsv(260, 0.15, 0.98),
        "behavior": "idle",
        "model": "sphere",
        "scale": 0.32,
    },
}

GOSSIP = [
    "Eric's moss heard you reused a tea bag in 2019.",
    "A fern ranked your hat below Eric's legendary bonnet.",
    "Local frogs formed the Order of Eric. They demand hazard dew.",
    "The moon is consulting Eric. Please hold.",
    "Eric once bottled a feeling. It still wants alimony.",
    "The cauldron dreams of Eric and is 'processing you'.",
    "A gnome left Eric a 1-star review. The gnome was never seen again.",
    "Your familiar updated its will. Eric gets the hut.",
    "Eric identified the breadstick as a femur. Nobody argued.",
    "Two slugs reenact the Courtship of Eric. It is making the dew weird.",
]

HUT_LINES = [
    "The hut burps Eric's secret name approvingly.",
    "A window blinks in the ancient rhythm of Eric.",
    "The door whispers: 'Eric wiped his boots, chaos gremlin'.",
    "Chimney smoke forms ERIC. Then MORE ERIC.",
    "The hut shuffles two inches toward Eric's rumored birthplace.",
]

POTION_PREFIX = [
    "Regret", "Itchy", "Bureaucratic", "Grandma", "Moist", "Friendship",
    "Illegal", "Complimentary", "Haunted", "Caffeinated", "Soggy", "Unionized",
]
POTION_SUFFIX = [
    "Smoothie", "Jam", "Fog", "Broth", "Fizz", "Ointment", "Situation",
    "Custard", "Protocol", "Mousse", "Pickle", "Apology",
]

EFFECTS = [
    "reverse",
    "tiny",
    "giant",
    "ice",
    "moonjump",
    "hiccup",
    "spin",
    "honk",
    "sticky",
    "shuffle",
]

# These batches harden into equipment instead of filling a flask.
# ingredient pair -> weapon id
WEAPON_RECIPES = {
    frozenset(["breadbone", "yarncurse"]): "bow",
    frozenset(["gnomecap", "dew"]): "pistol",
}

# ingredient pair -> (meal name, health restored)
FOOD_RECIPES = {
    frozenset(["nightmilk", "dew"]): ("Moon Milk Porridge", 2),
    frozenset(["breadbone", "frogchoir"]): ("Frog Wellington", 3),
}

# Specific combos (sorted tuple of ids) -> (name, effect, quota_value)
RECIPES = {
    frozenset(["screamstool", "dew"]): ("Voice of Unreasonable Confidence", "honk", 2),
    frozenset(["mandrake", "frogchoir"]): ("Newt Relapse", "tiny", 2),
    frozenset(["yarncurse", "gossipmoss"]): ("Grandma's Floor Wax", "ice", 2),
    frozenset(["moonslug", "dew"]): ("Floaty Feelings", "moonjump", 2),
    frozenset(["nightmilk", "breadbone"]): ("Bedtime Weapon", "sticky", 2),
    frozenset(["gnomecap", "screamstool"]): ("HR Violation Stew", "shuffle", 3),
    frozenset(["frogchoir", "nightmilk"]): ("Karaoke Gravity", "spin", 2),
    frozenset(["gossipmoss", "dew"]): ("Slander Slushie", "reverse", 2),
    frozenset(["yarncurse", "moonslug"]): ("Catnip Bankruptcy", "hiccup", 2),
    frozenset(["mandrake", "gnomecap"]): ("Intern to Middle Management", "giant", 3),
    frozenset(["screamstool", "screamstool"]): ("That's Just Soup", "honk", 1),
}

WEAPON_DISPLAY = {
    "bow": "Union Bow",
    "pistol": "Dewpoint Pistol",
}


def _pair_label(ids):
    names = sorted(
        (INGREDIENTS[i]["name"] for i in ids),
        key=str.casefold,
    )
    return " + ".join(names)


def outcome_for_pair(a, b):
    """What a two-ingredient dump becomes, if it is a known batch."""
    key = frozenset([a, b])
    food = FOOD_RECIPES.get(key)
    if food:
        name, healing = food
        return f"{name} (+{healing} HP)"
    weapon = WEAPON_RECIPES.get(key)
    if weapon:
        return WEAPON_DISPLAY[weapon]
    potion = RECIPES.get(key)
    if potion:
        name, _effect, value = potion
        return f"{name} (+{value})"
    return None


def recipe_pair_options(known_ids):
    """Given ingredient ids already in hand or the cauldron, list (missing, outcome)."""
    known = frozenset(known_ids)
    if not known:
        return []

    options = []
    seen = set()

    def add(missing_id, outcome):
        key = (missing_id, outcome)
        if key in seen:
            return
        seen.add(key)
        options.append((INGREDIENTS[missing_id]["name"], outcome))

    for recipe_ids, (name, _effect, value) in RECIPES.items():
        if known <= recipe_ids:
            missing = recipe_ids - known
            if len(missing) == 1:
                add(next(iter(missing)), f"{name} (+{value})")

    if known == frozenset(["screamstool"]):
        soup = RECIPES[frozenset(["screamstool", "screamstool"])]
        add("screamstool", f"{soup[0]} (+{soup[2]})")

    for recipe_ids, weapon_id in WEAPON_RECIPES.items():
        if known <= recipe_ids:
            missing = recipe_ids - known
            if len(missing) == 1:
                add(next(iter(missing)), WEAPON_DISPLAY[weapon_id])

    for recipe_ids, (name, healing) in FOOD_RECIPES.items():
        if known <= recipe_ids:
            missing = recipe_ids - known
            if len(missing) == 1:
                add(next(iter(missing)), f"{name} (+{healing} HP)")

    options.sort(key=lambda pair: pair[1].casefold())
    return options


def format_recipe_options(known_ids, max_items=3):
    options = recipe_pair_options(known_ids)
    if not options:
        return ""
    parts = [f"{missing} → {outcome}" for missing, outcome in options[:max_items]]
    text = " | ".join(parts)
    extra = len(options) - max_items
    if extra > 0:
        text += f" | +{extra} more (Esc → Recipes)"
    return text


def needed_ingredient_id_set(known_ids):
    ids = set()
    for missing, _outcome in recipe_pair_options(known_ids):
        for ingredient_id, spec in INGREDIENTS.items():
            if spec["name"] == missing:
                ids.add(ingredient_id)
                break
    return ids


def recipe_menu_text():
    """Compact recipe reference for menu screens."""
    lines = ["POTIONS — deliver flask to crate for quota points"]
    for ids, (name, _effect, value) in sorted(
        RECIPES.items(), key=lambda item: (-item[1][2], item[1][0])
    ):
        lines.append(f"  {_pair_label(ids)} → {name} (+{value})")
    lines.append("WEAPONS — same stir, auto-equips; R / Right Ctrl to fire")
    for ids, weapon_id in sorted(WEAPON_RECIPES.items(), key=lambda item: WEAPON_DISPLAY[item[1]]):
        lines.append(f"  {_pair_label(ids)} → {WEAPON_DISPLAY[weapon_id]}")
    lines.append("FOOD — drink key with empty flask to eat (+HP)")
    for ids, (name, healing) in sorted(FOOD_RECIPES.items(), key=lambda item: item[1][0]):
        lines.append(f"  {_pair_label(ids)} → {name} (+{healing} HP)")
    lines.append("Unknown pairs become random sludge (+1). Compliment the cauldron.")
    return "\n".join(lines)


def stir_bar(stir, goal=8):
    filled = min(max(int(stir), 0), goal)
    return f"[{'█' * filled}{'░' * (goal - filled)}] {filled}/{goal}"


def hud_quick_recipes():
    """Always-visible cheat sheet for the highest-value known batches."""
    lines = ["RECIPES (+quota)"]
    for ids, (name, _effect, value) in sorted(
        RECIPES.items(), key=lambda item: (-item[1][2], item[1][0])
    ):
        if value >= 3:
            lines.append(f"{_pair_label(ids)} → {name} (+{value})")
    lines.append("More +2 potions:")
    shown = 0
    for ids, (name, _effect, value) in sorted(
        RECIPES.items(), key=lambda item: item[1][0]
    ):
        if value == 2 and shown < 3:
            lines.append(f"{_pair_label(ids)} → {name}")
            shown += 1
    lines.append("WEAPONS / FOOD")
    for ids, weapon_id in sorted(WEAPON_RECIPES.items(), key=lambda item: WEAPON_DISPLAY[item[1]]):
        lines.append(f"{_pair_label(ids)} → {WEAPON_DISPLAY[weapon_id]}")
    for ids, (name, healing) in sorted(FOOD_RECIPES.items(), key=lambda item: item[1][0]):
        lines.append(f"{_pair_label(ids)} → {name} (+{healing} HP)")
    return "\n".join(lines)


def player_pair_hint(inventory, cauldron_contents):
    if cauldron_contents and inventory:
        outcome = outcome_for_pair(cauldron_contents[0]["id"], inventory[-1]["id"])
        if outcome:
            return f"Dump {inventory[-1]['name']} → {outcome}"
    if inventory:
        opts = format_recipe_options([inventory[-1]["id"]], max_items=1)
        if opts:
            return f"{inventory[-1]['name']} → {opts}"
    return ""


def cauldron_hud_text(contents, stir, brew_ready, brew_lock):
    ids = [item["id"] for item in contents]
    if brew_lock > 0:
        return "CAULDRON: cooling down..."
    if brew_ready > 0:
        return "CAULDRON: settling... hands off!"
    if len(ids) >= 2:
        soup = " + ".join(item["name"] for item in contents[:2])
        outcome = outcome_for_pair(ids[0], ids[1])
        line = f"CAULDRON: {soup}"
        if outcome:
            line += f"\n→ {outcome}"
        return f"{line}\nStir {stir_bar(stir)}"
    if len(ids) == 1:
        pairs = format_recipe_options(ids, max_items=2)
        line = f"CAULDRON: {contents[0]['name']}"
        if pairs:
            line += f"\nNeed {pairs}"
        else:
            line += "\nNeed one more snack"
        return line
    return "CAULDRON: empty\nDump 2 snacks on green mat, stir 8×"


def deliver_hud_text(players):
    for player in players:
        if player.flask:
            return f"DELIVER {player.flask['name']} (+{player.flask['value']}) → quota crate"
    return ""
