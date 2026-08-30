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
