"""Portable GLSL 120 bloom for Panda3D's macOS compatibility context."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from importlib import import_module
from math import isfinite
from typing import Any, cast

GLSL_VERSION = 120

VERTEX_SHADER = """
#version 120
uniform mat4 p3d_ModelViewProjectionMatrix;
attribute vec4 p3d_Vertex;
attribute vec2 p3d_MultiTexCoord0;
varying vec2 tex_coord;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    tex_coord = p3d_MultiTexCoord0;
}
"""

THRESHOLD_FRAGMENT_SHADER = """
#version 120
uniform sampler2D source_tex;
uniform float threshold;
varying vec2 tex_coord;

void main() {
    vec3 source_color = texture2D(source_tex, tex_coord).rgb;
    float brightness = dot(source_color, vec3(0.2126, 0.7152, 0.0722));
    float contribution = smoothstep(threshold, min(1.0, threshold + 0.22), brightness);
    gl_FragColor = vec4(source_color * contribution, 1.0);
}
"""

BLUR_FRAGMENT_SHADER = """
#version 120
uniform sampler2D source_tex;
uniform vec2 texel_size;
uniform vec2 direction;
varying vec2 tex_coord;

void main() {
    vec2 offset = texel_size * direction;
    vec4 result = texture2D(source_tex, tex_coord) * 0.227027;
    result += texture2D(source_tex, tex_coord + offset * 1.384615) * 0.316216;
    result += texture2D(source_tex, tex_coord - offset * 1.384615) * 0.316216;
    result += texture2D(source_tex, tex_coord + offset * 3.230769) * 0.070270;
    result += texture2D(source_tex, tex_coord - offset * 3.230769) * 0.070270;
    gl_FragColor = vec4(result.rgb, 1.0);
}
"""

COMPOSITE_FRAGMENT_SHADER = """
#version 120
uniform sampler2D scene_tex;
uniform sampler2D bloom_tex;
uniform float intensity;
uniform vec2 scene_texel_size;
uniform float fxaa_enabled;
varying vec2 tex_coord;

vec3 fxaa_scene(vec2 uv) {
    vec3 center = texture2D(scene_tex, uv).rgb;
    if (fxaa_enabled < 0.5) {
        return center;
    }

    vec3 northwest = texture2D(scene_tex, uv + vec2(-1.0, -1.0) * scene_texel_size).rgb;
    vec3 northeast = texture2D(scene_tex, uv + vec2(1.0, -1.0) * scene_texel_size).rgb;
    vec3 southwest = texture2D(scene_tex, uv + vec2(-1.0, 1.0) * scene_texel_size).rgb;
    vec3 southeast = texture2D(scene_tex, uv + vec2(1.0, 1.0) * scene_texel_size).rgb;

    vec3 luma_weights = vec3(0.299, 0.587, 0.114);
    float luma_center = dot(center, luma_weights);
    float luma_northwest = dot(northwest, luma_weights);
    float luma_northeast = dot(northeast, luma_weights);
    float luma_southwest = dot(southwest, luma_weights);
    float luma_southeast = dot(southeast, luma_weights);
    float luma_minimum = min(
        luma_center,
        min(min(luma_northwest, luma_northeast), min(luma_southwest, luma_southeast))
    );
    float luma_maximum = max(
        luma_center,
        max(max(luma_northwest, luma_northeast), max(luma_southwest, luma_southeast))
    );

    vec2 direction;
    direction.x = -((luma_northwest + luma_northeast) - (luma_southwest + luma_southeast));
    direction.y = (luma_northwest + luma_southwest) - (luma_northeast + luma_southeast);
    float direction_reduce = max(
        (luma_northwest + luma_northeast + luma_southwest + luma_southeast) * 0.03125,
        0.0078125
    );
    float reciprocal_minimum = 1.0 / (min(abs(direction.x), abs(direction.y)) + direction_reduce);
    direction = clamp(direction * reciprocal_minimum, vec2(-8.0), vec2(8.0)) * scene_texel_size;

    vec3 result_a = 0.5 * (
        texture2D(scene_tex, uv + direction * (1.0 / 3.0 - 0.5)).rgb
        + texture2D(scene_tex, uv + direction * (2.0 / 3.0 - 0.5)).rgb
    );
    vec3 result_b = result_a * 0.5 + 0.25 * (
        texture2D(scene_tex, uv + direction * -0.5).rgb
        + texture2D(scene_tex, uv + direction * 0.5).rgb
    );
    float luma_result_b = dot(result_b, luma_weights);
    if (luma_result_b < luma_minimum || luma_result_b > luma_maximum) {
        return result_a;
    }
    return result_b;
}

void main() {
    vec3 scene_color = fxaa_scene(tex_coord);
    vec3 bloom_color = texture2D(bloom_tex, tex_coord).rgb;
    gl_FragColor = vec4(scene_color + bloom_color * intensity, 1.0);
}
"""

SUPPORTED_MULTISAMPLE_COUNTS = (0, 2, 4, 8)


def validate_multisamples(samples: int) -> None:
    """Validate a portable framebuffer multisample count."""
    if isinstance(samples, bool) or samples not in SUPPORTED_MULTISAMPLE_COUNTS:
        choices = ", ".join(str(choice) for choice in SUPPORTED_MULTISAMPLE_COUNTS)
        raise ValueError(f"antialias_samples must be one of: {choices}")


@dataclass(frozen=True, slots=True)
class NativeBloomConfig:
    threshold: float = 0.56
    intensity: float = 1.35
    antialias_samples: int = 4
    enable_fxaa: bool = True

    def __post_init__(self) -> None:
        if not isfinite(self.threshold) or not 0.0 <= self.threshold <= 1.0:
            raise ValueError("bloom threshold must be finite and between zero and one")
        if not isfinite(self.intensity) or self.intensity < 0.0:
            raise ValueError("bloom intensity must be finite and non-negative")
        validate_multisamples(self.antialias_samples)


def prefers_native_bloom(platform_name: str) -> bool:
    """Return whether a platform should avoid Panda3D's Cg CommonFilters bloom."""
    return platform_name == "darwin"


class NativeBloomPipeline:
    """Four-pass GPU bloom using FilterManager and compatibility GLSL."""

    def __init__(
        self, manager: Any, textures: tuple[Any, ...], quads: tuple[Any, ...]
    ) -> None:
        self._manager = manager
        self._textures = textures
        self._quads = quads
        self.enabled = True

    @staticmethod
    def _texture(panda: Any, name: str) -> Any:
        texture = panda.Texture(name)
        texture.setWrapU(panda.Texture.WMClamp)
        texture.setWrapV(panda.Texture.WMClamp)
        texture.setMinfilter(panda.SamplerState.FT_linear)
        texture.setMagfilter(panda.SamplerState.FT_linear)
        return texture

    @classmethod
    def create(
        cls, base: Any, config: NativeBloomConfig | None = None
    ) -> NativeBloomPipeline:
        """Redirect the main display region through threshold, blur, and composite passes."""
        resolved = NativeBloomConfig() if config is None else config
        panda = cast(Any, import_module("panda3d.core"))
        filter_module = cast(Any, import_module("direct.filter.FilterManager"))
        manager: Any | None = None
        try:
            created_manager = filter_module.FilterManager(base.win, base.cam)
            manager = created_manager
            scene_texture = cls._texture(panda, "spacepaint-bloom-scene")
            bright_texture = cls._texture(panda, "spacepaint-bloom-bright")
            blur_x_texture = cls._texture(panda, "spacepaint-bloom-x")
            blur_y_texture = cls._texture(panda, "spacepaint-bloom-y")

            scene_buffer_properties = panda.FrameBufferProperties()
            scene_buffer_properties.setRgbColor(True)
            scene_buffer_properties.setMultisamples(resolved.antialias_samples)
            composite_quad = created_manager.renderSceneInto(
                colortex=scene_texture,
                fbprops=scene_buffer_properties,
            )
            bright_quad = created_manager.renderQuadInto(
                "spacepaint-bloom-threshold",
                colortex=bright_texture,
                div=2,
                align=2,
            )
            blur_x_quad = created_manager.renderQuadInto(
                "spacepaint-bloom-horizontal",
                colortex=blur_x_texture,
                div=4,
                align=4,
            )
            blur_y_quad = created_manager.renderQuadInto(
                "spacepaint-bloom-vertical",
                colortex=blur_y_texture,
                div=4,
                align=4,
            )
            quads = (composite_quad, bright_quad, blur_x_quad, blur_y_quad)
            if any(quad is None for quad in quads):
                raise RuntimeError(
                    "Panda3D could not allocate one or more bloom buffers"
                )

            threshold_shader = panda.Shader.make(
                panda.Shader.SL_GLSL,
                VERTEX_SHADER,
                THRESHOLD_FRAGMENT_SHADER,
            )
            blur_shader = panda.Shader.make(
                panda.Shader.SL_GLSL,
                VERTEX_SHADER,
                BLUR_FRAGMENT_SHADER,
            )
            composite_shader = panda.Shader.make(
                panda.Shader.SL_GLSL,
                VERTEX_SHADER,
                COMPOSITE_FRAGMENT_SHADER,
            )

            bright_quad.setShader(threshold_shader)
            bright_quad.setShaderInput("source_tex", scene_texture)
            bright_quad.setShaderInput("threshold", resolved.threshold)

            window_width = max(1, int(base.win.getXSize()))
            window_height = max(1, int(base.win.getYSize()))
            blur_x_quad.setShader(blur_shader)
            blur_x_quad.setShaderInput("source_tex", bright_texture)
            blur_x_quad.setShaderInput(
                "texel_size",
                panda.Vec2(2.0 / window_width, 2.0 / window_height),
            )
            blur_x_quad.setShaderInput("direction", panda.Vec2(1.0, 0.0))

            blur_y_quad.setShader(blur_shader)
            blur_y_quad.setShaderInput("source_tex", blur_x_texture)
            blur_y_quad.setShaderInput(
                "texel_size",
                panda.Vec2(4.0 / window_width, 4.0 / window_height),
            )
            blur_y_quad.setShaderInput("direction", panda.Vec2(0.0, 1.0))

            composite_quad.setShader(composite_shader)
            composite_quad.setShaderInput("scene_tex", scene_texture)
            composite_quad.setShaderInput("bloom_tex", blur_y_texture)
            composite_quad.setShaderInput("intensity", resolved.intensity)
            composite_quad.setShaderInput(
                "scene_texel_size",
                panda.Vec2(1.0 / window_width, 1.0 / window_height),
            )
            composite_quad.setShaderInput(
                "fxaa_enabled", 1.0 if resolved.enable_fxaa else 0.0
            )

            return cls(
                created_manager,
                (scene_texture, bright_texture, blur_x_texture, blur_y_texture),
                quads,
            )
        except Exception:
            if manager is not None:
                with suppress(Exception):
                    manager.cleanup()
            raise

    def cleanup(self) -> None:
        if not self.enabled:
            return
        self.enabled = False
        self._manager.cleanup()
