# Image Agent Studio

Local MCP server that exposes a focused image-generation and manipulation surface to any AI agent. It uses **Google Gemini** for generation and **Pillow** for conversion, normalization, and inspection — all from a single portable directory with no external project dependencies.

## Tools

### Generation

| Tool | Description | Requires API key |
|---|---|---|
| `generate_image` | Generate images with Gemini, optionally compositing multiple reference images | ✅ |

### Inspection

| Tool | Description | Requires API key |
|---|---|---|
| `preview_image` | Return a downscaled PNG as real MCP visual content for the agent to inspect | ❌ |
| `image_info` | Inspect width, height, aspect ratio, format, mode, and file size | ❌ |
| `get_dominant_colors` | Extract the N dominant colors from an image as `{hex, rgb}` list | ❌ |
| `describe_image` | Use Gemini Vision to describe or answer a question about an image | ✅ |

### Crop & Geometry

| Tool | Description | Requires API key |
|---|---|---|
| `crop` | Crop by pixel coordinates `(left, top, right, bottom)` | ❌ |
| `rotate` | Rotate by any angle (anti-clockwise), optionally expanding the canvas | ❌ |
| `normalize_canvas` | Fit an image to an exact canvas using `cover`, `contain`, or `stretch` | ❌ |

### Adjustments

| Tool | Description | Requires API key |
|---|---|---|
| `adjust_image` | Tune brightness, contrast, saturation, and sharpness (1.0 = no change) | ❌ |
| `apply_filter` | Apply a preset filter: `grayscale`, `sepia`, `blur`, `sharpen`, `edge_enhance`, `emboss`, `flip_horizontal`, `flip_vertical` | ❌ |

### Composition

| Tool | Description | Requires API key |
|---|---|---|
| `add_watermark` | Add a text or image watermark with position, opacity, and font controls | ❌ |
| `composite_images` | Paste an overlay image onto a base at `(x, y)` with opacity and scale | ❌ |

### Optimization

| Tool | Description | Requires API key |
|---|---|---|
| `compress` | Lossy-compress an image with quality control and optional EXIF strip | ❌ |
| `convert_image` | Convert between PNG, JPG, WEBP, PDF, SVG and optionally resize | ❌ |

### Utilities

| Tool | Description | Requires API key |
|---|---|---|
| `load_image_from_url` | Download an image from an http/https URL and save it locally | ❌ |
| `create_gif` | Create an animated GIF from a list of image paths | ❌ |

## Requirements

- Python 3.11 or newer
- A [Google AI Studio API key](https://aistudio.google.com/apikey) (only for `generate_image`)
- VS Code with the GitHub Copilot extension (to use via MCP)

## Setup

```bash
# 1. Clone / navigate to the directory
cd image-agent-studio

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate it
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure your API key
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY
```

## Connecting as an MCP server in VS Code

The `.vscode/mcp.json` file is already included. VS Code will detect the server automatically when you open the folder.

> **Windows**: the config uses `.venv/Scripts/python.exe`.  
> **Linux / macOS**: change the `command` in `.vscode/mcp.json` to `.venv/bin/python`.

To start the server manually (for debugging):

```bash
python server.py
```

## Project structure

```
image-agent-studio/
├── server.py            # MCP entrypoint — exposes the 17 tools
├── studio_core.py       # Core logic (all tool implementations)
├── requirements.txt     # Python dependencies
├── .env.example         # API key template — copy to .env and fill in
├── .vscode/
│   └── mcp.json         # VS Code MCP connection config (portable)
├── references/
│   └── tool-map.md      # Tool contracts and usage examples
├── output/              # Generated images land here (gitignored)
└── SKILL.md             # Agent skill descriptor
```

## Security

- **Never commit `.env`** — it is listed in `.gitignore`.
- `output/` is also gitignored; generated images stay local only.
- Only `generate_image` reads `GEMINI_API_KEY`. The other four tools require no credentials.
- If you accidentally expose your key, rotate it immediately at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | For `generate_image` and `describe_image` | Your Google AI Studio API key |

## Recommended workflow

```
generate_image / load_image_from_url
  → preview_image
  → image_info / get_dominant_colors / describe_image
  → crop / rotate / normalize_canvas
  → adjust_image / apply_filter
  → add_watermark / composite_images
  → compress / convert_image
  → create_gif   (if animation is needed)
```

1. **generate_image** — create the base image with Gemini (or **load_image_from_url** to start from an existing one).
2. **preview_image** — review the result visually inside the agent chat.
3. **image_info / get_dominant_colors / describe_image** — inspect dimensions, palette, or AI description.
4. **crop / rotate / normalize_canvas** — geometry adjustments.
5. **adjust_image / apply_filter** — tone and style corrections.
6. **add_watermark / composite_images** — branding and layering.
7. **compress / convert_image** — optimize and export.
8. **create_gif** — animate a sequence of frames if needed.

## License

MIT
