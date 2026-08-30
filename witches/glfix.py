"""Portable shaders for Ursina.

macOS only exposes an OpenGL 2.1 compatibility context by default, and its
3.2+/4.1 contexts are *core* profiles where Panda3D's GUI path stops drawing.
Ursina's stock shaders ask for GLSL 130/140, which the 2.1 context rejects, so
we supply GLSL 120 equivalents and leave the default context alone.
"""

from ursina import color
from ursina.shader import Shader
from ursina.vec2 import Vec2

_VERT = """#version 120
uniform mat4 p3d_ModelViewProjectionMatrix;
attribute vec4 p3d_Vertex;
attribute vec2 p3d_MultiTexCoord0;
attribute vec4 p3d_Color;
uniform vec2 texture_scale;
uniform vec2 texture_offset;
varying vec2 uvs;
varying vec4 vertex_color;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    uvs = (p3d_MultiTexCoord0 * texture_scale) + texture_offset;
    vertex_color = p3d_Color;
}
"""

_FRAG = """#version 120
uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
varying vec2 uvs;
varying vec4 vertex_color;

void main() {
    gl_FragColor = texture2D(p3d_Texture0, uvs) * p3d_ColorScale * vertex_color;
}
"""

_TEXT_VERT = """#version 120
uniform mat4 p3d_ModelViewProjectionMatrix;
attribute vec4 p3d_Vertex;
attribute vec2 p3d_MultiTexCoord0;
attribute vec4 p3d_Color;
varying vec2 uvs;
varying vec4 vertex_color;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    uvs = p3d_MultiTexCoord0;
    vertex_color = p3d_Color;
}
"""

# Text is an alpha-only SDF atlas, so keep the glyph colour and modulate alpha.
_TEXT_FRAG = """#version 120
uniform sampler2D p3d_Texture0;
uniform vec4 p3d_ColorScale;
varying vec2 uvs;
varying vec4 vertex_color;

void main() {
    float dist = texture2D(p3d_Texture0, uvs).a;
    float alpha = smoothstep(0.35, 0.65, dist);
    gl_FragColor = vec4(vertex_color.rgb, vertex_color.a * alpha) * p3d_ColorScale;
}
"""

portable_unlit = Shader(
    name="portable_unlit",
    language=Shader.GLSL,
    vertex=_VERT,
    fragment=_FRAG,
    default_input={
        "texture_scale": Vec2(1, 1),
        "texture_offset": Vec2(0.0, 0.0),
    },
)

portable_text = Shader(
    name="portable_text",
    language=Shader.GLSL,
    vertex=_TEXT_VERT,
    fragment=_TEXT_FRAG,
    default_input={
        "outline_color": color.white,
        "outline_offset": Vec2(10, 10),
        "outline_power": 1.0,
    },
)


def patch_ursina_shaders():
    """Point every Ursina entry point at the GLSL 120 shaders."""
    import ursina.prefabs.button as button_mod
    import ursina.shaders.unlit_shader as unlit_mod
    import ursina.shaders.unlit_with_fog_shader as fog_mod
    import ursina.text as text_mod
    from ursina import Entity
    from ursina.prefabs.sky import Sky

    Entity.default_shader = portable_unlit
    text_mod.text_shader = portable_text
    Sky.default_values["shader"] = portable_unlit
    unlit_mod.unlit_shader = portable_unlit
    fog_mod.unlit_with_fog_shader = portable_unlit
    button_mod.unlit_shader = portable_unlit

    # Button binds unlit_shader as a default argument, so the module patch above
    # cannot reach it. Wrap __init__ to inject the portable shader instead.
    Button = button_mod.Button
    if not getattr(Button, "_portable_patched", False):
        original_init = Button.__init__

        def patched_init(self, *args, **kwargs):
            kwargs.setdefault("shader", portable_unlit)
            original_init(self, *args, **kwargs)

        Button.__init__ = patched_init
        Button._portable_patched = True
