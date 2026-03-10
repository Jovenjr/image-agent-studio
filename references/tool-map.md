# Tool Map

## Setup minimo

1. Copia `.env.example` a `.env`.
2. Configura `GEMINI_API_KEY` con tu clave de Google AI Studio.
3. Instala dependencias con `pip install -r requirements.txt`.
4. Conecta el MCP local definido en `.vscode/mcp.json` o ejecuta `python server.py`.

Solo `generate_image` usa la API de Gemini. El resto de tools funciona sin clave.

## Superficie MCP

- `generate_image`
- `preview_image`
- `image_info`
- `normalize_canvas`
- `convert_image`

## Preview visual real

`preview_image` no devuelve JSON descriptivo al agente. Devuelve imagen MCP real para que el cliente la inyecte al contexto visual del modelo.

Contrato:

```json
{
  "image_path": "C:/ruta/absoluta/imagen.png",
  "max_size": 1200
}
```

## Generación con referencias

`generate_image` acepta este contrato:

```json
{
  "prompt": "Describe la imagen a generar",
  "output_path": "C:/ruta/absoluta/output.png",
  "width": 1920,
  "height": 1080,
  "reference_images": [
    "C:/ruta/absoluta/ref1.png",
    "C:/ruta/absoluta/ref2.jpg"
  ],
  "model": "gemini-3.1-flash-image-preview",
  "style": "dramatico, cinematografico",
  "composite_refs_height": 600
}
```

Notas:

- Si pasas varias referencias, el skill crea un composite local automaticamente antes de llamar a Gemini.
- `width` y `height` se reportan como tamano solicitado; el archivo final debe verificarse con `image_info`.

## Verificación posterior

1. Leer dimensiones reales con `image_info`.
2. Si el modelo devolvio otra resolucion, normalizar con `normalize_canvas`.
3. Si ademas hace falta cambiar formato, usar `convert_image`.

## Estrategias de normalización

- `cover`: llena todo el canvas y recorta el sobrante.
- `contain`: mantiene todo visible y agrega padding.
- `stretch`: fuerza el tamaño exacto sin respetar proporción.

## Conversión

`convert_image` usa el motor local para estos casos:

- PNG → JPG
- PNG/JPG → WEBP
- SVG → PNG/PDF
- resize exacto con `width` y `height`

Contrato:

```json
{
  "input_path": "C:/ruta/absoluta/input.svg",
  "output_path": "C:/ruta/absoluta/output.pdf",
  "output_format": "pdf",
  "width": 0,
  "height": 0,
  "quality": 92,
  "dpi": 300
}
```

## Inspeccion

`image_info` devuelve ancho, alto, aspect ratio, formato y peso.

```json
{
  "image_path": "C:/ruta/absoluta/banner.png"
}
```

## Normalización de canvas

`normalize_canvas` ajusta la imagen a un size exacto y devuelve metadata del archivo final.

Contrato:

```json
{
  "input_path": "C:/ruta/absoluta/banner.png",
  "output_path": "C:/ruta/absoluta/banner_1920x1080.png",
  "width": 1920,
  "height": 1080,
  "mode": "cover",
  "bg_color": "#000000"
}
```

## Recorte

`crop` recorta por coordenadas de pixel.

```json
{
  "input_path": "C:/ruta/input.png",
  "output_path": "C:/ruta/cropped.png",
  "left": 100,
  "top": 50,
  "right": 900,
  "bottom": 600
}
```

## Rotación

`rotate` gira la imagen. `expand=true` evita recortar esquinas.

```json
{
  "input_path": "C:/ruta/input.png",
  "output_path": "C:/ruta/rotated.png",
  "angle": 90,
  "expand": true,
  "fill_color": "#000000"
}
```

Usa `apply_filter` con `filter_name: "flip_horizontal"` o `"flip_vertical"` para voltear sin rotar.

## Ajuste de imagen

`adjust_image` controla brillo, contraste, saturacion y nitidez. `1.0` = sin cambio.

```json
{
  "input_path": "C:/ruta/input.png",
  "output_path": "C:/ruta/adjusted.png",
  "brightness": 1.2,
  "contrast": 1.1,
  "saturation": 1.3,
  "sharpness": 1.0
}
```

Rango util: `0.2` (oscuro/plano) – `2.5` (brillante/vivo).

## Filtros

`apply_filter` aplica un filtro predefinido.

Opciones de `filter_name`: `grayscale`, `sepia`, `blur`, `sharpen`, `edge_enhance`, `emboss`, `flip_horizontal`, `flip_vertical`.

```json
{
  "input_path": "C:/ruta/input.png",
  "output_path": "C:/ruta/sepia.png",
  "filter_name": "sepia"
}
```

## Marca de agua

`add_watermark` acepta texto o imagen. Proporciona uno de los dos.

```json
{
  "input_path": "C:/ruta/input.png",
  "output_path": "C:/ruta/watermarked.png",
  "text": "© Mi Marca 2026",
  "watermark_image_path": "",
  "position": "bottom-right",
  "opacity": 180,
  "font_size": 36,
  "color": "#ffffff",
  "padding": 20
}
```

`position` acepta: `top-left`, `top-right`, `bottom-left`, `bottom-right`, `center`.

## Composición de imágenes

`composite_images` pega un overlay sobre una base.

```json
{
  "base_path": "C:/ruta/base.png",
  "overlay_path": "C:/ruta/logo.png",
  "output_path": "C:/ruta/composed.png",
  "x": 50,
  "y": 50,
  "opacity": 200,
  "scale": 0.5
}
```

## Colores dominantes

`get_dominant_colors` devuelve una lista de `{hex, rgb}` con los N colores mas frecuentes.

```json
{
  "image_path": "C:/ruta/input.png",
  "count": 6
}
```

Respuesta ejemplo:
```json
{
  "colors": [
    {"hex": "#1a2b3c", "rgb": [26, 43, 60]},
    {"hex": "#f5e6d0", "rgb": [245, 230, 208]}
  ]
}
```

## Compresión

`compress` reduce el peso del archivo con control de calidad.

```json
{
  "input_path": "C:/ruta/input.png",
  "output_path": "C:/ruta/compressed.jpg",
  "quality": 80,
  "strip_exif": true
}
```

`strip_exif: true` elimina metadatos EXIF (ubicacion, camara, etc.).

## Descripcion por IA

`describe_image` usa Gemini Vision para analizar la imagen. Requiere `GEMINI_API_KEY`.

```json
{
  "image_path": "C:/ruta/input.png",
  "question": "What colors dominate this image?"
}
```

Si `question` esta vacio, describe la imagen de forma general.

## Descarga desde URL

`load_image_from_url` descarga una imagen http/https sin necesidad de API key.

```json
{
  "url": "https://example.com/photo.jpg",
  "output_path": "C:/ruta/output/descargada.jpg"
}
```

No sigue redirects peligrosos de IPs privadas — usa solo URLs publicas.

## GIF animado

`create_gif` crea un GIF animado desde una lista de imagenes.

```json
{
  "frame_paths": [
    "C:/ruta/frame1.png",
    "C:/ruta/frame2.png",
    "C:/ruta/frame3.png"
  ],
  "output_path": "C:/ruta/output/animacion.gif",
  "duration_ms": 200,
  "loop": 0
}
```

`loop: 0` = bucle infinito. `loop: 1` = reproducir una sola vez.

## Núcleo local

Toda la logica compartida del skill vive ahora en `studio_core.py` y el punto de entrada MCP es `server.py`.