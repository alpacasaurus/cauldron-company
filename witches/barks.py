"""Local NPC trash talk. Nobody in this clearing went to charm school.

These are spoken verbatim in the NPC's own voice, so they skip the Eric omen
preamble that wraps narrated dialogue. Keep the voice short, loud, and rude.
"""

import random

# A goblin notices a witch and opens with a character assassination.
ENEMY_SPOTTED = [
    "Hey! Cone-head! That hat makes you look like a taxable dunce!",
    "Christ, it's the soup hag. Still broke, still ugly.",
    "I've audited corpses with better posture than you, sweetheart.",
    "Nice broom. Shove it up your ass and spin, why don't you.",
    "You smell like wet dog and eleven months of unpaid rent.",
    "Piss off, witch. Nobody is buying your little bucket of sludge.",
    "Your mother kissed a frog and out came whatever this is.",
    "HEY! I'm auditing here, you knock-kneed bitch!",
    "Look at this dipshit, boiling weeds at midnight. Get a hobby. Get a life.",
    "Is that cauldron your girlfriend? Figures. Nothing warm-blooded would have you.",
    "Nine hells, put a bag over that face before you curdle my milk.",
    "You call that a robe? My gran was buried in something less depressing.",
]

ENEMY_ATTACK = [
    "Eat shit and expense it!",
    "Hold still, I'm garnishing your goddamn wages!",
    "This is a verbal warning, you stupid hag!",
    "Say hello to my little audit!",
    "I'm gonna wear your hat as a novelty condom!",
    "Bite me? No. I bite YOU, asshole!",
    "Payroll says you're overdue for a beating!",
]

ENEMY_HURT = [
    "AGH! My spleen! That's coming out of your pay, bitch!",
    "You hit like an intern with a hand cramp!",
    "OW! OW! I have a family, you psychotic bag of sticks!",
    "Right, that's IT. I'm filing a grievance AND kicking your ass.",
    "Do you know how much dental costs in this economy?!",
]

ENEMY_DEATH = [
    "Tell my ex-wife... she was right about everything... the witch...",
    "I regret... every single spreadsheet...",
    "Worth it... I still hate your hat...",
    "Died doing what I loved. Harassing strangers. Bluh.",
    "Ah, hell with it. Piss on your quota.",
    "Nobody... liked me anyway... and honestly? Fair...",
]

FAMILIAR_THEFT = [
    "Mine now, bitch. Go cry into your little hat.",
    "You left it in an open pocket, dumbass. That's basically consent.",
    "I'm taking this, and your dignity, which was cheap and on sale.",
    "Snitches get scratched. Bye.",
    "Hard to steal from someone competent. Wouldn't know. Never met one.",
]

FAMILIAR_SCRITCH = [
    "Lower. LOWER. God, you're useless with those thumbs.",
    "Fine. We're square. Touch my stomach and I open your wrist.",
    "Mmh. Tell anyone I liked that and I piss in both your boots.",
    "Yeah, that's the spot, you enormous pink idiot. Don't stop.",
]

HUT_BARKS = [
    "Wipe your feet, you filthy little goblin.",
    "Knock again and I chew your hand off at the elbow.",
    "Oh good. The disappointment is home.",
    "I've eaten better witches than you. Literally. They screamed nicer.",
    "Don't touch my knob with those hands. I know where they've been.",
    "You live here rent free and STILL show up empty-handed?",
]

CAULDRON_REFUSAL = [
    "That's not a recipe, that's a war crime with a garnish.",
    "Put something in me, coward. I'm not a decoration.",
    "One ingredient. ONE. Are you brewing or just showing off your wrist?",
    "I've had richer broth made out of pond and regret.",
]

CAULDRON_COMPLIMENT = [
    "Ugh, stop. I look like a pot. ...say it again though.",
    "Flattery works on me. I'm a pot. I have no standards and no spine.",
    "Finally, some respect in this godforsaken lawn.",
    "Keep talking, gorgeous, and I might not spit in the batch.",
]

_last_line = {}


def pick(bank):
    """A random line from a bank, never the one that bank just used."""
    key = id(bank)
    options = [line for line in bank if line != _last_line.get(key)] or list(bank)
    choice = random.choice(options)
    _last_line[key] = choice
    return choice
