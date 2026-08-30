#!/usr/bin/env python3
"""Generate HUD pixel-art icons for ingredients and outcomes."""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "witches" / "assets" / "textures" / "hud"
DRAW_SIZE = 32
EXPORT_SIZE = 128
T = (0, 0, 0, 0)


def save(name, img):
    OUT.mkdir(parents=True, exist_ok=True)
    if img.size != (EXPORT_SIZE, EXPORT_SIZE):
        img = img.resize((EXPORT_SIZE, EXPORT_SIZE), Image.NEAREST)
    img.save(OUT / f"{name}.png")
    print(f"wrote {name}.png ({EXPORT_SIZE}x{EXPORT_SIZE})")


def canvas():
    return Image.new("RGBA", (DRAW_SIZE, DRAW_SIZE), T)


def screamstool():
    img = canvas()
    d = ImageDraw.Draw(img)
    d.ellipse([8, 6, 24, 20], fill=(255, 120, 180, 255))
    d.rectangle([14, 18, 18, 26], fill=(240, 220, 200, 255))
    for x, y in ((11, 10), (17, 8), (21, 12), (14, 14)):
        d.ellipse([x, y, x + 2, y + 2], fill=(255, 255, 255, 255))
    return img


def moonslug():
    img = canvas()
    d = ImageDraw.Draw(img)
    d.ellipse([5, 12, 27, 22], fill=(120, 180, 230, 255))
    d.ellipse([6, 13, 26, 21], fill=(150, 205, 245, 255))
    d.ellipse([8, 15, 12, 19], fill=(40, 60, 90, 255))
    d.ellipse([20, 15, 24, 19], fill=(40, 60, 90, 255))
    d.line([24, 17, 30, 16], fill=(120, 180, 230, 255), width=2)
    return img


def gossipmoss():
    img = canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([4, 18, 28, 26], fill=(70, 130, 70, 255))
    d.rectangle([6, 16, 26, 20], fill=(90, 155, 85, 255))
    for x, y in ((8, 18), (14, 20), (20, 17), (24, 21)):
        d.point((x, y), fill=(45, 95, 45, 255))
        d.point((x + 1, y), fill=(45, 95, 45, 255))
    return img


def frogchoir():
    img = canvas()
    d = ImageDraw.Draw(img)
    d.ellipse([8, 14, 24, 26], fill=(70, 170, 70, 255))
    d.ellipse([10, 8, 16, 14], fill=(80, 185, 80, 255))
    d.ellipse([16, 8, 22, 14], fill=(80, 185, 80, 255))
    d.ellipse([12, 10, 14, 12], fill=(20, 30, 20, 255))
    d.ellipse([18, 10, 20, 12], fill=(20, 30, 20, 255))
    d.line([16, 14, 16, 16], fill=(60, 140, 60, 255), width=2)
    return img


def yarncurse():
    img = canvas()
    d = ImageDraw.Draw(img)
    d.ellipse([8, 8, 24, 24], fill=(255, 150, 60, 255))
    d.arc([9, 9, 23, 23], 30, 300, fill=(220, 100, 30, 255), width=2)
    d.arc([11, 11, 21, 21], 120, 390, fill=(255, 200, 120, 255), width=2)
    d.line([16, 8, 16, 6], fill=(255, 180, 80, 255), width=2)
    return img


def mandrake():
    img = canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([14, 10, 18, 26], fill=(150, 95, 55, 255))
    d.polygon([(16, 4), (10, 12), (22, 12)], fill=(80, 140, 60, 255))
    d.line([12, 14, 8, 18], fill=(150, 95, 55, 255), width=2)
    d.line([20, 14, 24, 18], fill=(150, 95, 55, 255), width=2)
    d.ellipse([13, 8, 19, 12], fill=(180, 120, 70, 255))
    d.point((15, 10), fill=(30, 20, 10, 255))
    d.point((18, 10), fill=(30, 20, 10, 255))
    return img


def dew():
    img = canvas()
    d = ImageDraw.Draw(img)
    d.polygon([(16, 4), (24, 18), (16, 28), (8, 18)], fill=(120, 220, 255, 255))
    d.polygon([(16, 6), (22, 17), (16, 25), (10, 17)], fill=(180, 240, 255, 255))
    d.ellipse([13, 10, 16, 13], fill=(255, 255, 255, 180))
    return img


def breadbone():
    img = canvas()
    d = ImageDraw.Draw(img)
    d.polygon([(8, 22), (12, 8), (16, 8), (20, 22)], fill=(220, 180, 110, 255))
    d.line([10, 12, 18, 12], fill=(190, 150, 85, 255), width=1)
    d.line([11, 16, 17, 16], fill=(190, 150, 85, 255), width=1)
    d.ellipse([12, 6, 16, 10], fill=(240, 210, 150, 255))
    return img


def gnomecap():
    img = canvas()
    d = ImageDraw.Draw(img)
    d.polygon([(16, 4), (6, 22), (26, 22)], fill=(220, 40, 40, 255))
    d.rectangle([6, 22, 26, 26], fill=(245, 245, 245, 255))
    d.line([16, 4, 16, 22], fill=(180, 30, 30, 255), width=1)
    return img


def nightmilk():
    img = canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([11, 10, 21, 26], fill=(235, 230, 255, 255))
    d.rectangle([10, 8, 22, 12], fill=(210, 200, 240, 255))
    d.rectangle([14, 12, 18, 16], fill=(200, 190, 255, 255))
    d.ellipse([13, 18, 19, 24], fill=(245, 242, 255, 255))
    return img


def potion():
    img = canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([13, 8, 19, 10], fill=(120, 70, 150, 255))
    d.polygon([(12, 10), (20, 10), (22, 14), (10, 14)], fill=(160, 90, 200, 255))
    d.rectangle([11, 14, 21, 26], fill=(140, 70, 190, 255))
    d.rectangle([12, 16, 20, 22], fill=(190, 120, 240, 255))
    d.ellipse([13, 22, 19, 26], fill=(100, 50, 150, 255))
    return img


def bow():
    img = canvas()
    d = ImageDraw.Draw(img)
    d.arc([6, 4, 26, 28], 70, 290, fill=(140, 90, 45, 255), width=3)
    d.line([16, 6, 16, 26], fill=(200, 170, 120, 255), width=1)
    d.line([16, 16, 24, 12], fill=(220, 200, 160, 255), width=2)
    return img


def pistol():
    img = canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([6, 14, 18, 18], fill=(80, 160, 210, 255))
    d.rectangle([18, 12, 26, 18], fill=(60, 130, 180, 255))
    d.rectangle([8, 18, 14, 24], fill=(50, 50, 70, 255))
    d.rectangle([20, 18, 24, 22], fill=(40, 40, 55, 255))
    d.point((24, 14), fill=(255, 220, 80, 255))
    return img


def food():
    img = canvas()
    d = ImageDraw.Draw(img)
    d.ellipse([6, 18, 26, 28], fill=(90, 150, 80, 255))
    d.ellipse([8, 19, 24, 27], fill=(120, 180, 100, 255))
    d.ellipse([12, 10, 20, 18], fill=(220, 180, 110, 255))
    d.line([14, 8, 14, 10], fill=(180, 180, 180, 255), width=1)
    d.line([18, 7, 18, 10], fill=(180, 180, 180, 255), width=1)
    return img


def arrow():
    img = canvas()
    d = ImageDraw.Draw(img)
    gold = (255, 208, 88, 255)
    gold_hi = (255, 236, 168, 255)
    gold_sh = (210, 155, 45, 255)
    d.rectangle([7, 15, 15, 17], fill=gold_sh)
    d.rectangle([7, 15, 15, 16], fill=gold)
    d.point([(7, 15), (8, 15), (9, 15)], fill=gold_hi)
    d.polygon([(14, 10), (24, 16), (14, 22)], fill=gold_sh)
    d.polygon([(15, 11), (23, 16), (15, 21)], fill=gold)
    d.line([(15, 11), (22, 16)], fill=gold_hi, width=1)
    return img


def warning():
    img = canvas()
    d = ImageDraw.Draw(img)
    d.polygon([(16, 4), (28, 26), (4, 26)], fill=(230, 60, 60, 255))
    d.polygon([(16, 8), (24, 24), (8, 24)], fill=(255, 90, 70, 255))
    d.rectangle([15, 12, 17, 18], fill=(255, 255, 240, 255))
    d.rectangle([15, 20, 17, 22], fill=(255, 255, 240, 255))
    return img


def crate():
    img = canvas()
    d = ImageDraw.Draw(img)
    d.rectangle([6, 10, 26, 26], fill=(150, 100, 55, 255))
    d.rectangle([6, 10, 26, 14], fill=(180, 125, 70, 255))
    d.line([6, 18, 26, 18], fill=(110, 70, 35, 255), width=2)
    d.line([16, 10, 16, 26], fill=(110, 70, 35, 255), width=2)
    d.rectangle([8, 12, 12, 16], fill=(255, 220, 80, 255))
    return img


def main():
    icons = {
        "screamstool": screamstool,
        "moonslug": moonslug,
        "gossipmoss": gossipmoss,
        "frogchoir": frogchoir,
        "yarncurse": yarncurse,
        "mandrake": mandrake,
        "dew": dew,
        "breadbone": breadbone,
        "gnomecap": gnomecap,
        "nightmilk": nightmilk,
        "potion": potion,
        "bow": bow,
        "pistol": pistol,
        "food": food,
        "arrow": arrow,
        "warning": warning,
        "crate": crate,
    }
    for name, fn in icons.items():
        save(name, fn())
    print(f"Generated {len(icons)} icons in {OUT}")


if __name__ == "__main__":
    main()
