#!/usr/bin/env python3
from __future__ import annotations

import base64
import io
import mimetypes
import os
import shutil
import tempfile
from pathlib import Path

from PIL import Image

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional when env vars already exist
    load_dotenv = None


SKILL_ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = "gemini-3.1-flash-image-preview"

MODEL_ALIASES = {
    "gemini-3.1-flash-image-preview": "gemini-3.1-flash-image-preview",
    "gemini-flash-image": "gemini-3.1-flash-image-preview",
    "gemini-flash": "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image": "gemini-3-pro-image-preview",
    "gemini-3-pro": "gemini-3-pro-image-preview",
    "imagen-4": "imagen-4.0-generate-001",
    "imagen4": "imagen-4.0-generate-001",
    "imagen-4-ultra": "imagen-4.0-ultra-generate-001",
    "imagen-4-fast": "imagen-4.0-fast-generate-001",
    "imagen-3": "imagen-4.0-generate-001",
    "imagen3": "imagen-4.0-generate-001",
    "imagen-3.0-generate-001": "imagen-4.0-generate-001",
    "gemini-2.0-flash-preview-image-generation": "gemini-3.1-flash-image-preview",
    "gemini-2.0-flash-exp": "gemini-3.1-flash-image-preview",
}

GEMINI_NATIVE_MODELS = {
    "gemini-2.0-flash-preview-image-generation",
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash-exp-image-generation",
    "gemini-2.5-flash-image",
    "gemini-3-pro-image-preview",
    "gemini-3.1-flash-image-preview",
}

RASTER_OUTPUT_FORMATS = {
    "png": "PNG",
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "webp": "WEBP",
    "bmp": "BMP",
    "tiff": "TIFF",
    "pdf": "PDF",
}


def load_local_env() -> None:
    env_path = SKILL_ROOT / ".env"
    if load_dotenv is not None and env_path.exists():
        load_dotenv(env_path, override=False)


def resolve_model(model: str) -> str:
    return MODEL_ALIASES.get(model, model)


def _resize_image(image: Image.Image, width: int, height: int) -> Image.Image:
    original_width, original_height = image.size
    if width and height:
        return image.resize((width, height), Image.LANCZOS)
    if width:
        return image.resize(
            (width, max(1, round(original_height * width / original_width))),
            Image.LANCZOS,
        )
    if height:
        return image.resize(
            (max(1, round(original_width * height / original_height)), height),
            Image.LANCZOS,
        )
    return image


def _save_raster_image(
    image: Image.Image,
    output_path: Path,
    output_format: str,
    quality: int,
    dpi: int,
) -> None:
    fmt = output_format.lower()
    if fmt in {"jpg", "jpeg"}:
        image.convert("RGB").save(output_path, "JPEG", quality=quality)
        return
    if fmt == "webp":
        image.save(output_path, "WEBP", quality=quality)
        return
    if fmt == "bmp":
        image.convert("RGB").save(output_path, "BMP")
        return
    if fmt == "tiff":
        image.save(output_path, "TIFF")
        return
    if fmt == "pdf":
        image.convert("RGB").save(output_path, "PDF", resolution=dpi)
        return
    image.save(output_path, "PNG")


def _parse_hex_color(value: str) -> tuple[int, int, int, int]:
    color = value.strip().lstrip("#")
    if len(color) == 6:
        return (int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16), 255)
    if len(color) == 8:
        return (
            int(color[0:2], 16),
            int(color[2:4], 16),
            int(color[4:6], 16),
            int(color[6:8], 16),
        )
    raise ValueError("Usa color en formato #RRGGBB o #RRGGBBAA")


def _resize_cover(image: Image.Image, width: int, height: int) -> Image.Image:
    scale = max(width / image.width, height / image.height)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.LANCZOS,
    )
    left = max((resized.width - width) // 2, 0)
    top = max((resized.height - height) // 2, 0)
    return resized.crop((left, top, left + width, top + height))


def _resize_contain(
    image: Image.Image,
    width: int,
    height: int,
    bg_color: tuple[int, int, int, int],
) -> Image.Image:
    scale = min(width / image.width, height / image.height)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.LANCZOS,
    )
    canvas = Image.new("RGBA", (width, height), bg_color)
    left = (width - resized.width) // 2
    top = (height - resized.height) // 2
    canvas.paste(resized, (left, top), resized)
    return canvas


def _save_canvas_image(image: Image.Image, output_path: Path) -> None:
    if output_path.suffix.lower() in {".jpg", ".jpeg", ".bmp"}:
        image.convert("RGB").save(output_path)
        return
    image.save(output_path)


def _composite_reference_images(
    image_paths: list[str],
    output_path: Path,
    target_height: int,
    gap: int = 24,
    gap_fill: tuple[int, int, int] = (255, 255, 255),
) -> Path:
    scaled_images: list[Image.Image] = []
    try:
        for image_path in image_paths:
            with Image.open(image_path) as source_image:
                rgb_image = source_image.convert("RGB")
            scale = target_height / rgb_image.height
            resized = rgb_image.resize(
                (max(1, round(rgb_image.width * scale)), target_height),
                Image.LANCZOS,
            )
            scaled_images.append(resized)

        total_width = sum(image.width for image in scaled_images) + gap * (len(scaled_images) - 1)
        canvas = Image.new("RGB", (total_width, target_height), gap_fill)
        offset_x = 0
        for image in scaled_images:
            canvas.paste(image, (offset_x, 0))
            offset_x += image.width + gap

        output_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output_path, "JPEG", quality=92)
        return output_path.resolve()
    finally:
        for image in scaled_images:
            image.close()


def _extract_native_image_bytes(response: object) -> bytes:
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            inline_data = getattr(part, "inline_data", None)
            if inline_data is None:
                continue
            data = getattr(inline_data, "data", None)
            if data is None:
                continue
            return base64.b64decode(data) if isinstance(data, str) else data
    raise RuntimeError("Gemini no devolvio una imagen. Intenta un prompt diferente.")


def _generate_with_gemini(
    prompt: str,
    output_path: Path,
    model: str,
    reference_image: str | None = None,
) -> Path:
    load_local_env()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY no esta configurada. Copia .env.example a .env y completa tu clave."
        )

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "Falta la dependencia google-genai. Ejecuta: pip install -r requirements.txt"
        ) from exc

    resolved_model = resolve_model(model)
    client = genai.Client(api_key=api_key)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if resolved_model in GEMINI_NATIVE_MODELS:
        if reference_image and Path(reference_image).exists():
            ref_path = Path(reference_image)
            contents: object = [
                types.Part.from_text(text=prompt),
                types.Part.from_bytes(
                    data=ref_path.read_bytes(),
                    mime_type=mimetypes.guess_type(str(ref_path))[0] or "image/jpeg",
                ),
            ]
        else:
            contents = prompt

        response = client.models.generate_content(
            model=resolved_model,
            contents=contents,
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
        )
        output_path.write_bytes(_extract_native_image_bytes(response))
        return output_path.resolve()

    response = client.models.generate_images(
        model=resolved_model,
        prompt=prompt,
        config=types.GenerateImagesConfig(number_of_images=1),
    )
    generated_images = getattr(response, "generated_images", None) or []
    if not generated_images:
        raise RuntimeError("El modelo no genero ninguna imagen. Intenta un prompt diferente.")

    image_object = getattr(generated_images[0], "image", None)
    image_bytes = getattr(image_object, "image_bytes", None)
    if not image_bytes:
        raise RuntimeError("La respuesta del modelo no incluyo bytes de imagen.")

    output_path.write_bytes(image_bytes)
    return output_path.resolve()


def generate_image(
    prompt: str,
    output_path: str,
    width: int = 1080,
    height: int = 1080,
    reference_images: list[str] | None = None,
    model: str = DEFAULT_MODEL,
    style: str = "",
    composite_refs_height: int = 600,
) -> dict:
    output = Path(output_path).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    refs = [str(Path(path).expanduser().resolve()) for path in (reference_images or [])]
    existing_refs = [path for path in refs if Path(path).exists()]
    if refs and not existing_refs:
        raise FileNotFoundError(f"Ninguna referencia encontrada: {refs}")

    reference_image: str | None = None
    composite_path: str | None = None
    if len(existing_refs) == 1:
        reference_image = existing_refs[0]
    elif len(existing_refs) > 1:
        composite_output = output.parent / f"{output.stem}__refs.jpg"
        composite_path = str(
            _composite_reference_images(existing_refs, composite_output, composite_refs_height)
        )
        reference_image = composite_path

    full_prompt = f"{prompt}, {style}".strip(", ") if style else prompt
    result_path = _generate_with_gemini(full_prompt, output, model, reference_image=reference_image)

    return {
        "output": str(result_path),
        "model": resolve_model(model),
        "requested_size": {"width": width, "height": height},
        "references_used": existing_refs,
        "composite_created": composite_path,
        "size_kb": round(Path(result_path).stat().st_size / 1024, 1),
    }


def convert_image(
    input_path: str,
    output_path: str,
    output_format: str = "",
    width: int = 0,
    height: int = 0,
    quality: int = 92,
    dpi: int = 150,
) -> dict:
    source = Path(input_path).expanduser().resolve()
    target = Path(output_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    if not source.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {source}")

    source_format = source.suffix.lower().lstrip(".")
    target_format = (output_format or target.suffix.lstrip(".")).lower()
    if target_format == "jpeg":
        target_format = "jpg"
    if not target_format:
        raise ValueError(
            "Debes indicar output_format o usar una extension valida en output_path."
        )

    if source_format == "svg":
        if target_format == "svg":
            shutil.copy2(source, target)
        elif target_format == "pdf":
            try:
                from reportlab.graphics import renderPDF
                from svglib.svglib import svg2rlg
            except ImportError as exc:
                raise RuntimeError(
                    "Faltan svglib/reportlab para convertir SVG. Ejecuta: pip install -r requirements.txt"
                ) from exc

            drawing = svg2rlg(str(source))
            if not drawing:
                raise RuntimeError("No se pudo parsear el SVG de entrada.")
            if width or height:
                scale_x = (width / drawing.width) if width else 1.0
                scale_y = (height / drawing.height) if height else scale_x
                drawing.width = width or drawing.width * scale_y
                drawing.height = height or drawing.height * scale_x
                drawing.transform = (scale_x, 0, 0, scale_y, 0, 0)
            renderPDF.drawToFile(drawing, str(target))
        elif target_format in RASTER_OUTPUT_FORMATS:
            try:
                from reportlab.graphics import renderPM
                from svglib.svglib import svg2rlg
            except ImportError as exc:
                raise RuntimeError(
                    "Faltan svglib/reportlab para convertir SVG. Ejecuta: pip install -r requirements.txt"
                ) from exc

            drawing = svg2rlg(str(source))
            if not drawing:
                raise RuntimeError("No se pudo parsear el SVG de entrada.")
            if width or height:
                scale_x = (width / drawing.width) if width else 1.0
                scale_y = (height / drawing.height) if height else scale_x
                drawing.width = width or drawing.width * scale_y
                drawing.height = height or drawing.height * scale_x
                drawing.transform = (scale_x, 0, 0, scale_y, 0, 0)

            temp_path: str | None = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                    temp_path = temp_file.name
                renderPM.drawToFile(drawing, temp_path, fmt="PNG", dpi=dpi)
                with Image.open(temp_path) as raster_image:
                    _save_raster_image(raster_image, target, target_format, quality, dpi)
            finally:
                if temp_path:
                    Path(temp_path).unlink(missing_ok=True)
        else:
            raise ValueError(f"Formato de salida no soportado desde SVG: {target_format}")
    else:
        with Image.open(source) as source_image:
            converted = _resize_image(source_image, width, height)
            _save_raster_image(converted, target, target_format, quality, dpi)

    final_width: int | None = None
    final_height: int | None = None
    try:
        with Image.open(target) as final_image:
            final_width, final_height = final_image.size
    except Exception:
        final_width, final_height = None, None

    return {
        "input": str(source),
        "output": str(target),
        "format": target_format,
        "width": final_width,
        "height": final_height,
        "size_kb": round(target.stat().st_size / 1024, 1),
    }


def build_preview_image(image_path: str, max_size: int = 1200) -> tuple[bytes, dict]:
    source = Path(image_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"No existe la imagen de entrada: {source}")

    with Image.open(source) as source_image:
        original_width, original_height = source_image.size
        preview = source_image.convert("RGBA")

    preview_width, preview_height = preview.size
    resized = False
    if max(preview_width, preview_height) > max_size:
        ratio = max_size / max(preview_width, preview_height)
        preview_width = max(1, int(preview_width * ratio))
        preview_height = max(1, int(preview_height * ratio))
        preview = preview.resize((preview_width, preview_height), Image.LANCZOS)
        resized = True

    buffer = io.BytesIO()
    preview.save(buffer, format="PNG")
    preview_bytes = buffer.getvalue()

    return preview_bytes, {
        "input": str(source),
        "format": "png",
        "mime_type": "image/png",
        "original_width": original_width,
        "original_height": original_height,
        "width": preview_width,
        "height": preview_height,
        "resized": resized,
        "size_kb": round(len(preview_bytes) / 1024, 1),
    }


def normalize_canvas(
    input_path: str,
    output_path: str,
    width: int,
    height: int,
    mode: str = "contain",
    bg_color: str = "#000000",
) -> dict:
    if mode not in {"cover", "contain", "stretch"}:
        raise ValueError("mode debe ser 'cover', 'contain' o 'stretch'.")

    source = Path(input_path).expanduser().resolve()
    target = Path(output_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    if not source.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {source}")

    with Image.open(source) as source_image:
        image = source_image.convert("RGBA")

    background = _parse_hex_color(bg_color)
    if mode == "cover":
        normalized = _resize_cover(image, width, height)
    elif mode == "stretch":
        normalized = image.resize((width, height), Image.LANCZOS)
    else:
        normalized = _resize_contain(image, width, height, background)

    _save_canvas_image(normalized, target)

    return {
        "input": str(source),
        "output": str(target),
        "format": target.suffix.lower().lstrip("."),
        "width": width,
        "height": height,
        "mode": mode,
        "size_kb": round(target.stat().st_size / 1024, 1),
    }


def get_image_info(image_path: str) -> dict:
    source = Path(image_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"No existe la imagen de entrada: {source}")

    with Image.open(source) as image:
        return {
            "path": str(source),
            "width": image.width,
            "height": image.height,
            "aspect_ratio": round(image.width / image.height, 4) if image.height else None,
            "format": image.format,
            "mode": image.mode,
            "size_kb": round(source.stat().st_size / 1024, 1),
        }


# ─── Nuevas tools ─────────────────────────────────────────────────────────────

def crop(
    input_path: str,
    output_path: str,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> dict:
    """Recorta la imagen por coordenadas de pixel (left, top, right, bottom)."""
    source = Path(input_path).expanduser().resolve()
    target = Path(output_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as img:
        w, h = img.size
        box = (
            max(0, left),
            max(0, top),
            min(w, right),
            min(h, bottom),
        )
        cropped = img.crop(box)
        cropped.save(target)

    return {
        "input": str(source),
        "output": str(target),
        "box": {"left": box[0], "top": box[1], "right": box[2], "bottom": box[3]},
        "width": cropped.width,
        "height": cropped.height,
        "size_kb": round(target.stat().st_size / 1024, 1),
    }


def rotate(
    input_path: str,
    output_path: str,
    angle: float,
    expand: bool = True,
    fill_color: str = "#000000",
) -> dict:
    """Rota la imagen el número de grados indicado (sentido antihorario).
    Con expand=True el canvas se agranda para no recortar. flip horizontal = 180,
    flip vertical = usa apply_filter con filter_name='flip_vertical'.
    """
    source = Path(input_path).expanduser().resolve()
    target = Path(output_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)

    fill = _parse_hex_color(fill_color)[:3]
    with Image.open(source) as img:
        mode = img.mode
        if mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
            mode = "RGBA"
        fc = fill if mode == "RGB" else (*fill, 0)
        rotated = img.rotate(-angle, expand=expand, fillcolor=fc)
        rotated.save(target)

    return {
        "input": str(source),
        "output": str(target),
        "angle": angle,
        "expand": expand,
        "width": rotated.width,
        "height": rotated.height,
        "size_kb": round(target.stat().st_size / 1024, 1),
    }


def adjust_image(
    input_path: str,
    output_path: str,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sharpness: float = 1.0,
) -> dict:
    """Ajusta brillo, contraste, saturacion y nitidez. 1.0 = sin cambio,
    <1.0 = reducir, >1.0 = aumentar. Rango util: 0.0 – 3.0."""
    from PIL import ImageEnhance

    source = Path(input_path).expanduser().resolve()
    target = Path(output_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as img:
        result = img.copy()

    for factor, enhancer_cls in [
        (brightness, ImageEnhance.Brightness),
        (contrast, ImageEnhance.Contrast),
        (saturation, ImageEnhance.Color),
        (sharpness, ImageEnhance.Sharpness),
    ]:
        if factor != 1.0:
            result = enhancer_cls(result).enhance(factor)

    result.save(target)
    return {
        "input": str(source),
        "output": str(target),
        "brightness": brightness,
        "contrast": contrast,
        "saturation": saturation,
        "sharpness": sharpness,
        "size_kb": round(target.stat().st_size / 1024, 1),
    }


def _apply_sepia(img: Image.Image) -> Image.Image:
    rgb = img.convert("RGB")
    pixels = list(rgb.getdata())
    sepia = [
        (
            min(255, int(r * 0.393 + g * 0.769 + b * 0.189)),
            min(255, int(r * 0.349 + g * 0.686 + b * 0.168)),
            min(255, int(r * 0.272 + g * 0.534 + b * 0.131)),
        )
        for r, g, b in pixels
    ]
    out = Image.new("RGB", rgb.size)
    out.putdata(sepia)
    return out


def apply_filter(
    input_path: str,
    output_path: str,
    filter_name: str,
) -> dict:
    """Aplica un filtro predefinido a la imagen.
    Opciones: grayscale, sepia, blur, sharpen, edge_enhance, emboss,
              flip_horizontal, flip_vertical.
    """
    from PIL import ImageFilter

    FILTERS: dict = {
        "grayscale": lambda img: img.convert("L").convert("RGB"),
        "sepia": _apply_sepia,
        "blur": lambda img: img.filter(ImageFilter.GaussianBlur(radius=3)),
        "sharpen": lambda img: img.filter(ImageFilter.SHARPEN),
        "edge_enhance": lambda img: img.filter(ImageFilter.EDGE_ENHANCE),
        "emboss": lambda img: img.filter(ImageFilter.EMBOSS),
        "flip_horizontal": lambda img: img.transpose(Image.FLIP_LEFT_RIGHT),
        "flip_vertical": lambda img: img.transpose(Image.FLIP_TOP_BOTTOM),
    }

    if filter_name not in FILTERS:
        raise ValueError(
            f"Filtro '{filter_name}' no reconocido. Opciones: {sorted(FILTERS)}"
        )

    source = Path(input_path).expanduser().resolve()
    target = Path(output_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as img:
        result = FILTERS[filter_name](img)

    result.save(target)
    return {
        "input": str(source),
        "output": str(target),
        "filter": filter_name,
        "size_kb": round(target.stat().st_size / 1024, 1),
    }


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
    """Añade una marca de agua de texto o de imagen sobre la foto.
    position: top-left | top-right | bottom-left | bottom-right | center.
    opacity: 0 (invisible) – 255 (opaco).
    """
    from PIL import ImageDraw

    if not text and not watermark_image_path:
        raise ValueError("Proporciona 'text' o 'watermark_image_path'.")

    source = Path(input_path).expanduser().resolve()
    target = Path(output_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as img:
        base = img.convert("RGBA")

    iw, ih = base.size

    def _resolve_pos(ow: int, oh: int) -> tuple[int, int]:
        positions = {
            "top-left": (padding, padding),
            "top-right": (iw - ow - padding, padding),
            "bottom-left": (padding, ih - oh - padding),
            "bottom-right": (iw - ow - padding, ih - oh - padding),
            "center": ((iw - ow) // 2, (ih - oh) // 2),
        }
        return positions.get(position, positions["bottom-right"])

    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))

    if text:
        draw = ImageDraw.Draw(layer)
        try:
            from PIL import ImageFont

            font = ImageFont.truetype("arial.ttf", size=font_size)
        except (OSError, IOError):
            try:
                from PIL import ImageFont

                font = ImageFont.load_default(size=font_size)
            except TypeError:
                from PIL import ImageFont

                font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        r, g, b = _parse_hex_color(color)[:3]
        pos = _resolve_pos(tw, th)
        draw.text(pos, text, font=font, fill=(r, g, b, opacity))

    elif watermark_image_path:
        wm_source = Path(watermark_image_path).expanduser().resolve()
        if not wm_source.exists():
            raise FileNotFoundError(f"No existe la marca de agua: {wm_source}")
        with Image.open(wm_source) as wm:
            wm_rgba = wm.convert("RGBA")
        if opacity != 255:
            r_ch, g_ch, b_ch, a_ch = wm_rgba.split()
            a_ch = a_ch.point(lambda v: int(v * opacity / 255))
            wm_rgba = Image.merge("RGBA", (r_ch, g_ch, b_ch, a_ch))
        pos = _resolve_pos(wm_rgba.width, wm_rgba.height)
        layer.paste(wm_rgba, pos, wm_rgba)

    result = Image.alpha_composite(base, layer)
    if target.suffix.lower() in {".jpg", ".jpeg"}:
        result = result.convert("RGB")
    result.save(target)

    return {
        "input": str(source),
        "output": str(target),
        "text": text or None,
        "watermark_image": watermark_image_path or None,
        "position": position,
        "opacity": opacity,
        "size_kb": round(target.stat().st_size / 1024, 1),
    }


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
    base_src = Path(base_path).expanduser().resolve()
    overlay_src = Path(overlay_path).expanduser().resolve()
    target = Path(output_path).expanduser().resolve()

    for p, label in [(base_src, "base"), (overlay_src, "overlay")]:
        if not p.exists():
            raise FileNotFoundError(f"No existe el archivo {label}: {p}")
    target.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(base_src) as b, Image.open(overlay_src) as o:
        base = b.convert("RGBA")
        overlay = o.convert("RGBA")

    if scale != 1.0:
        nw = max(1, round(overlay.width * scale))
        nh = max(1, round(overlay.height * scale))
        overlay = overlay.resize((nw, nh), Image.LANCZOS)

    if opacity != 255:
        r_ch, g_ch, b_ch, a_ch = overlay.split()
        a_ch = a_ch.point(lambda v: int(v * opacity / 255))
        overlay = Image.merge("RGBA", (r_ch, g_ch, b_ch, a_ch))

    base.paste(overlay, (x, y), overlay)
    if target.suffix.lower() in {".jpg", ".jpeg"}:
        base = base.convert("RGB")
    base.save(target)

    return {
        "base": str(base_src),
        "overlay": str(overlay_src),
        "output": str(target),
        "position": {"x": x, "y": y},
        "opacity": opacity,
        "scale": scale,
        "width": base.width,
        "height": base.height,
        "size_kb": round(target.stat().st_size / 1024, 1),
    }


def get_dominant_colors(image_path: str, count: int = 6) -> dict:
    """Extrae la paleta de colores dominantes de la imagen.
    Devuelve lista de {hex, rgb} ordenada por frecuencia."""
    source = Path(image_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"No existe la imagen de entrada: {source}")

    count = max(1, min(count, 32))
    with Image.open(source) as img:
        small = img.convert("RGB").resize((150, 150), Image.LANCZOS)

    quantized = small.quantize(colors=count, method=Image.Quantize.MEDIANCUT)
    palette_flat = quantized.getpalette() or []
    colors = []
    for i in range(count):
        if i * 3 + 2 >= len(palette_flat):
            break
        r, g, b = palette_flat[i * 3], palette_flat[i * 3 + 1], palette_flat[i * 3 + 2]
        colors.append({"hex": f"#{r:02x}{g:02x}{b:02x}", "rgb": [r, g, b]})

    return {"image": str(source), "count": len(colors), "colors": colors}


def compress(
    input_path: str,
    output_path: str,
    quality: int = 80,
    strip_exif: bool = True,
) -> dict:
    """Comprime la imagen con control de calidad (10–95).
    strip_exif=True elimina metadatos EXIF para reducir peso y privacidad.
    Formato de salida determinado por la extension de output_path.
    """
    source = Path(input_path).expanduser().resolve()
    target = Path(output_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)

    quality = max(10, min(quality, 95))
    fmt = target.suffix.lower().lstrip(".")
    if fmt == "jpeg":
        fmt = "jpg"

    original_kb = round(source.stat().st_size / 1024, 1)

    with Image.open(source) as img:
        save_img = img.copy() if strip_exif else img
        _save_raster_image(save_img, target, fmt or "jpg", quality, 72)

    final_kb = round(target.stat().st_size / 1024, 1)
    return {
        "input": str(source),
        "output": str(target),
        "quality": quality,
        "strip_exif": strip_exif,
        "original_size_kb": original_kb,
        "output_size_kb": final_kb,
        "reduction_pct": round((1 - final_kb / original_kb) * 100, 1) if original_kb else 0,
    }


def describe_image(image_path: str, question: str = "") -> dict:
    """Usa Gemini Vision para describir la imagen o responder una pregunta sobre ella.
    Requiere GEMINI_API_KEY."""
    load_local_env()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY no esta configurada. Copia .env.example a .env y completa tu clave."
        )

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "Falta google-genai. Ejecuta: pip install -r requirements.txt"
        ) from exc

    source = Path(image_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"No existe la imagen de entrada: {source}")

    prompt_text = question.strip() if question.strip() else "Describe esta imagen en detalle."
    mime = mimetypes.guess_type(str(source))[0] or "image/jpeg"
    image_bytes = source.read_bytes()

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Part.from_text(text=prompt_text),
            types.Part.from_bytes(data=image_bytes, mime_type=mime),
        ],
    )

    return {
        "image": str(source),
        "question": prompt_text,
        "description": response.text,
    }


def load_image_from_url(url: str, output_path: str) -> dict:
    """Descarga una imagen desde una URL y la guarda localmente.
    Soporta http y https. No requiere API key."""
    import urllib.request
    import urllib.error

    target = Path(output_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    if not url.startswith(("http://", "https://")):
        raise ValueError("Solo se admiten URLs http:// o https://")

    headers = {"User-Agent": "ImageAgentStudio/1.0"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Error al descargar la imagen: {exc}") from exc

    target.write_bytes(data)

    with Image.open(target) as img:
        w, h = img.size
        fmt = img.format or ""

    return {
        "url": url,
        "output": str(target),
        "format": fmt,
        "width": w,
        "height": h,
        "size_kb": round(target.stat().st_size / 1024, 1),
    }


def create_gif(
    frame_paths: list[str],
    output_path: str,
    duration_ms: int = 100,
    loop: int = 0,
) -> dict:
    """Crea un GIF animado a partir de una lista de imagenes.
    duration_ms: tiempo por frame en milisegundos.
    loop: 0 = bucle infinito, N = repetir N veces.
    """
    if not frame_paths:
        raise ValueError("Debes proporcionar al menos un frame.")

    target = Path(output_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    frames: list[Image.Image] = []
    for path in frame_paths:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"No existe el frame: {p}")
        frames.append(Image.open(p).convert("RGBA"))

    if not frames:
        raise ValueError("No se cargaron frames validos.")

    frames[0].save(
        target,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=loop,
        disposal=2,
    )
    for f in frames:
        f.close()

    return {
        "output": str(target),
        "frames": len(frames),
        "duration_ms": duration_ms,
        "loop": loop,
        "size_kb": round(target.stat().st_size / 1024, 1),
    }