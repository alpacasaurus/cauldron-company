"""Package Cauldron Company with PyInstaller (run this on the OS you want to ship)."""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

# Panda3D's wheel bundles the legacy libRocket GUI and NVIDIA Cg shader
# libraries as x86_64-only binaries, which breaks the build on Apple Silicon.
# The game uses neither (Ursina draws its own UI and we ship GLSL shaders).
SKIP_BINARIES = ("rocket", "libcg")
root = Path(SPECPATH)


def wanted(entry):
    return not any(part in Path(entry[0]).name.lower() for part in SKIP_BINARIES)


datas, binaries, hiddenimports = [], [], []
for pkg in ("panda3d", "panda3d_gltf", "panda3d_simplepbr", "ursina", "screeninfo", "witches"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        hiddenimports.append(pkg)

datas.append((str(root / "assets"), "assets"))
binaries = [b for b in binaries if wanted(b)]

hiddenimports += [
    "witches.session",
    "witches.world",
    "witches.actors",
    "witches.forage",
    "witches.brew",
    "witches.catalog",
    "witches.iconart",
    "witches.combat",
    "witches.barks",
    "witches.debuglog",
    "witches.teardown",
    "witches.meshes",
    "witches.glfix",
    "panda3d.core",
    "direct.showbase",
    "direct.task",
]

a = Analysis(
    [str(root / "run.py")],
    pathex=[str(root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "panda3d.rocket"],
    noarchive=False,
)

a.binaries = [b for b in a.binaries if wanted(b)]


def dedupe(*tocs):
    """Drop entries that would write twice to the same destination.

    Homebrew's framework Python is collected both as a real binary and as a
    symlink at `_internal/Python`, and COLLECT fails on the second one.
    """
    seen = set()
    result = []
    for toc in tocs:
        kept = []
        for entry in toc:
            if entry[0] in seen:
                continue
            seen.add(entry[0])
            kept.append(entry)
        result.append(kept)
    return result


a.binaries, a.datas = dedupe(a.binaries, a.datas)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CauldronCompany",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="CauldronCompany",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="CauldronCompany.app",
        icon=None,
        bundle_identifier="games.friendslop.cauldroncompany",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleName": "Cauldron Company",
            "LSApplicationCategoryType": "public.app-category.games",
        },
    )
