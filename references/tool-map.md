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

## Núcleo local

Toda la logica compartida del skill vive ahora en `studio_core.py` y el punto de entrada MCP es `server.py`.