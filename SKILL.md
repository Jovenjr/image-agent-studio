---
name: image-agent-studio
description: Use when an agent needs a local MCP-backed image workflow from this directory only: generate with Gemini, preview images visually, inspect dimensions, normalize exact canvases, and convert formats without importing external project directories.
---

# Image Agent Studio

Skill autocontenido que se distribuye con su propio servidor MCP local.

La idea ya no es exponer scripts sueltos, sino conectar este MCP al agente y trabajar sobre una superficie pequena y estable de tools.

## Estado actual

- El servidor local vive en `server.py`.
- La logica compartida vive en `studio_core.py`.
- La configuracion MCP del workspace apunta a este skill en `.vscode/mcp.json`.
- El skill ya no depende de wrappers CLI para su flujo principal.

## Tools expuestas por el MCP

- `generate_image`
- `preview_image`
- `image_info`
- `normalize_canvas`
- `convert_image`

## Variable de entorno y API key

- Variable requerida para generacion: `GEMINI_API_KEY`
- Tipo de clave: clave de Google AI Studio / Gemini API
- Archivo esperado: `.env` en la raiz de este directorio
- Plantilla incluida: `.env.example`

Solo `generate_image` necesita esa variable. `preview_image`, `image_info`, `normalize_canvas` y `convert_image` no requieren ninguna clave.

## Dependencias

Instala las dependencias desde este directorio:

```powershell
pip install -r requirements.txt
```

## Uso rapido

1. Copia `.env.example` a `.env`.
2. Pon tu `GEMINI_API_KEY` en `.env`.
3. Instala dependencias con `pip install -r requirements.txt`.
4. Conecta el MCP definido en `.vscode/mcp.json` o ejecuta `python server.py`.
5. Invoca las tools desde el agente conectado.

Ejemplo de arranque manual del servidor:

```powershell
python server.py
```

## Cuándo usarlo

- Cuando el usuario pide generar una imagen con Gemini usando una o varias referencias.
- Cuando el output debe quedar en una resolución exacta como 1920x1080 o 1080x1920.
- Cuando hace falta convertir entre PNG, JPG, WEBP o PDF.
- Cuando el agente necesita ver una imagen como contenido visual real via `preview_image`.
- Cuando hace falta un MCP local, estable y reutilizable sin depender del resto del repo.

## Flujo recomendado

1. `generate_image` para crear la imagen base.
2. `preview_image` para que el agente vea el resultado.
3. `image_info` para validar el tamaño real del archivo.
4. `normalize_canvas` si el entregable requiere canvas exacto.
5. `convert_image` si hace falta exportar a otro formato o redimensionar.

## Reglas operativas

- Mantener los outputs de generación en `.png` o `.jpg`.
- No asumir que el modelo respetó exactamente el layout o la resolución: verificar siempre.
- `generate_image` es la unica tool que requiere `GEMINI_API_KEY`.
- `preview_image` devuelve bytes PNG al cliente MCP como contenido visual.
- Las rutas de salida se crean automaticamente si el directorio no existe.

## Referencia rápida

Si necesitas ejemplos de payload, setup y estrategia operativa del MCP, lee `references/tool-map.md`.