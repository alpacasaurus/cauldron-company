#!/usr/bin/env python3
"""Report every shader Ursina compiles and flag ones the Mac GL context rejects."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from panda3d.core import loadPrcFileData

loadPrcFileData("", "window-type offscreen")

from ursina import Ursina, application  # noqa: E402
from ursina.shader import Shader  # noqa: E402

from witches.glfix import patch_ursina_shaders  # noqa: E402

seen = {}
original_compile = Shader.compile


def traced_compile(self, *args, **kwargs):
    versions = []
    for part in (getattr(self, "vertex", None), getattr(self, "fragment", None)):
        if not part:
            continue
        for line in part.splitlines():
            if line.strip().startswith("#version"):
                versions.append(line.strip().split()[1])
                break
    seen[getattr(self, "name", "?")] = versions
    return original_compile(self, *args, **kwargs)


Shader.compile = traced_compile


def main():
    patch_ursina_shaders()
    Ursina(window_type="offscreen", development_mode=False, editor_ui_enabled=False)

    from witches.session import boot

    director = boot()
    director.start(2)
    for _ in range(30):
        application.base.taskMgr.step()

    print("\nshaders compiled:")
    stale = []
    for name, versions in sorted(seen.items()):
        legacy = [v for v in versions if v not in ("120",)]
        flag = "  <-- not GLSL 120" if legacy else ""
        print(f"  {name:26} versions={versions}{flag}")
        if legacy:
            stale.append(name)
    print()
    print(f"non-120 shaders: {stale}" if stale else "every compiled shader is GLSL 120")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
