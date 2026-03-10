#!/usr/bin/env python3
from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.utilities.types import Image as FastMCPImage

from studio_core import (
    DEFAULT_MODEL,
    add_watermark as core_add_watermark,
    adjust_image as core_adjust_image,
    apply_filter as core_apply_filter,
    build_preview_image,
    composite_images as core_composite_images,
    compress as core_compress,
    convert_image as core_convert_image,
    create_gif as core_create_gif,
    crop as core_crop,
    describe_image as core_describe_image,
    generate_image as core_generate_image,
    get_dominant_colors as core_get_dominant_colors,
    get_image_info,
    load_image_from_url as core_load_image_from_url,
    normalize_canvas as core_normalize_canvas,
    rotate as core_rotate,
)


mcp = FastMCP(
    "Image Agent Studio",
    instructions="""
Servidor MCP local del skill Image Agent Studio.

Superficie enfocada para un flujo completo de imagen:
  — Generacion: generate_image
  — Inspeccion: preview_image, image_info, get_dominant_colors, describe_image
  — Recorte/geometria: crop, rotate, normalize_canvas
  — Ajustes: adjust_image, apply_filter
  — Composicion: add_watermark, composite_images
  — Optimizacion: compress, convert_image
  — Utilidades: load_image_from_url, create_gif

Variable de entorno requerida solo para generate_image y describe_image:
  - GEMINI_API_KEY
""",
)


# ─── Generación ───────────────────────────────────────────────────────────────

@mcp.tool()
def generate_image(
    prompt: str,
    output_path: str,
    width: int = 1080,
    height: int = 1080,
    reference_images: list[str] = [],
    model: str = DEFAULT_MODEL,
    style: str = "",
    composite_refs_height: int = 600,
) -> dict:
    """Genera una imagen con Gemini usando cero, una o varias referencias."""
    return core_generate_image(
        prompt=prompt,
        output_path=output_path,
        width=width,
        height=height,
        reference_images=reference_images,
        model=model,
        style=style,
        composite_refs_height=composite_refs_height,
    )


# ─── Inspección ───────────────────────────────────────────────────────────────

@mcp.tool()
def preview_image(image_path: str, max_size: int = 1200) -> FastMCPImage:
    """Devuelve una imagen PNG reducida para que el agente la pueda inspeccionar visualmente."""
    preview_bytes, _ = build_preview_image(image_path=image_path, max_size=max_size)
    return FastMCPImage(data=preview_bytes, format="png")


@mcp.tool()
def image_info(image_path: str) -> dict:
    """Devuelve resolucion, aspect ratio, formato, modo y peso del archivo."""
    return get_image_info(image_path)


@mcp.tool()
def get_dominant_colors(image_path: str, count: int = 6) -> dict:
    """Extrae los N colores dominantes de la imagen como lista {hex, rgb}."""
    return core_get_dominant_colors(image_path=image_path, count=count)


@mcp.tool()
def describe_image(image_path: str, question: str = "") -> dict:
    """Usa Gemini Vision para describir o analizar la imagen. Requiere GEMINI_API_KEY.
    Si pasas 'question', responde esa pregunta especifica sobre la imagen."""
    return core_describe_image(image_path=image_path, question=question)


# ─── Recorte y geometría ──────────────────────────────────────────────────────

@mcp.tool()
def crop(
    input_path: str,
    output_path: str,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> dict:
    """Recorta la imagen por coordenadas de pixel (left, top, right, bottom)."""
    return core_crop(
        input_path=input_path,
        output_path=output_path,
        left=left,
        top=top,
        right=right,
        bottom=bottom,
    )


@mcp.tool()
def rotate(
    input_path: str,
    output_path: str,
    angle: float,
    expand: bool = True,
    fill_color: str = "#000000",
) -> dict:
    """Rota la imagen. angle en grados (sentido antihorario).
    expand=True ajusta el canvas para no recortar esquinas.
    Para flip: usa apply_filter con filter_name='flip_horizontal' o 'flip_vertical'.
    """
    return core_rotate(
        input_path=input_path,
        output_path=output_path,
        angle=angle,
        expand=expand,
        fill_color=fill_color,
    )


@mcp.tool()
def normalize_canvas(
    input_path: str,
    output_path: str,
    width: int,
    height: int,
    mode: str = "contain",
    bg_color: str = "#000000",
) -> dict:
    """Ajusta una imagen a un canvas exacto usando cover, contain o stretch."""
    return core_normalize_canvas(
        input_path=input_path,
        output_path=output_path,
        width=width,
        height=height,
        mode=mode,
        bg_color=bg_color,
    )


# ─── Ajustes ──────────────────────────────────────────────────────────────────

@mcp.tool()
def adjust_image(
    input_path: str,
    output_path: str,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sharpness: float = 1.0,
) -> dict:
    """Ajusta brillo, contraste, saturacion y nitidez. 1.0 = sin cambio.
    Rango util: 0.2 (oscuro/plano) – 2.5 (brillante/vivo).
    """
    return core_adjust_image(
        input_path=input_path,
        output_path=output_path,
        brightness=brightness,
        contrast=contrast,
        saturation=saturation,
        sharpness=sharpness,
    )


@mcp.tool()
def apply_filter(
    input_path: str,
    output_path: str,
    filter_name: str,
) -> dict:
    """Aplica un filtro predefinido. Opciones:
    grayscale, sepia, blur, sharpen, edge_enhance, emboss,
    flip_horizontal, flip_vertical.
    """
    return core_apply_filter(
        input_path=input_path,
        output_path=output_path,
        filter_name=filter_name,
    )


# ─── Composición ──────────────────────────────────────────────────────────────

@mcp.tool()
def add_watermark(
    input_path: str,
    output_path: str,
    text: str = "",
    watermark_image_path: str = "",
    position: str = "bottom-right",
    opacity: int = 180,
    font_size: int = 36,
    color: str = "#ffffff",
    padding: int = 20,
) -> dict:
    """Añade marca de agua de texto o de imagen.
    position: top-left | top-right | bottom-left | bottom-right | center.
    opacity: 0–255. Proporciona 'text' o 'watermark_image_path'.
    """
    return core_add_watermark(
        input_path=input_path,
        output_path=output_path,
        text=text,
        watermark_image_path=watermark_image_path,
        position=position,
        opacity=opacity,
        font_size=font_size,
        color=color,
        padding=padding,
    )


@mcp.tool()
def composite_images(
    base_path: str,
    overlay_path: str,
    output_path: str,
    x: int = 0,
    y: int = 0,
    opacity: int = 255,
    scale: float = 1.0,
) -> dict:
    """Pega overlay sobre base en la posicion (x, y).
    opacity: 0–255. scale: factor de escala del overlay antes de pegar.
    """
    return core_composite_images(
        base_path=base_path,
        overlay_path=overlay_path,
        output_path=output_path,
        x=x,
        y=y,
        opacity=opacity,
        scale=scale,
    )


# ─── Optimización ─────────────────────────────────────────────────────────────

@mcp.tool()
def compress(
    input_path: str,
    output_path: str,
    quality: int = 80,
    strip_exif: bool = True,
) -> dict:
    """Comprime la imagen con control de calidad (10–95).
    strip_exif=True elimina metadatos EXIF para reducir peso y proteger privacidad.
    """
    return core_compress(
        input_path=input_path,
        output_path=output_path,
        quality=quality,
        strip_exif=strip_exif,
    )


@mcp.tool()
def convert_image(
    input_path: str,
    output_path: str,
    output_format: str = "",
    width: int = 0,
    height: int = 0,
    quality: int = 92,
    dpi: int = 150,
) -> dict:
    """Convierte una imagen entre formatos raster y SVG/PDF cuando aplica."""
    return core_convert_image(
        input_path=input_path,
        output_path=output_path,
        output_format=output_format,
        width=width,
        height=height,
        quality=quality,
        dpi=dpi,
    )


# ─── Utilidades ───────────────────────────────────────────────────────────────

@mcp.tool()
def load_image_from_url(url: str, output_path: str) -> dict:
    """Descarga una imagen desde una URL http/https y la guarda localmente.
    No requiere API key.
    """
    return core_load_image_from_url(url=url, output_path=output_path)


@mcp.tool()
def create_gif(
    frame_paths: list[str],
    output_path: str,
    duration_ms: int = 100,
    loop: int = 0,
) -> dict:
    """Crea un GIF animado desde una lista de imagenes.
    duration_ms: tiempo por frame. loop=0 para bucle infinito.
    """
    return core_create_gif(
        frame_paths=frame_paths,
        output_path=output_path,
        duration_ms=duration_ms,
        loop=loop,
    )


if __name__ == "__main__":
    mcp.run()