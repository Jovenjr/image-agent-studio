# Image Agent Studio

Local MCP server that exposes a focused image-generation and manipulation surface to any AI agent. It uses **Google Gemini** for generation and **Pillow** for conversion, normalization, and inspection — all from a single portable directory with no external project dependencies.

## Tools

| Tool | Description | Requires API key |
|---|---|---|
| `generate_image` | Generate images with Gemini, optionally compositing multiple reference images | ✅ |
| `preview_image` | Return a downscaled PNG as real MCP visual content for the agent to inspect | ❌ |
| `image_info` | Inspect width, height, aspect ratio, format, mode, and file size | ❌ |
| `normalize_canvas` | Fit an image to an exact canvas using `cover`, `contain`, or `stretch` | ❌ |
| `convert_image` | Convert between PNG, JPG, WEBP, PDF, SVG and optionally resize | ❌ |

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
├── server.py            # MCP entrypoint — exposes the 5 tools
├── studio_core.py       # Core logic (generation, conversion, normalization, preview)
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
| `GEMINI_API_KEY` | For `generate_image` only | Your Google AI Studio API key |

## Recommended workflow

```
generate_image → preview_image → image_info → normalize_canvas → convert_image
```

1. **generate_image** — create the base image with Gemini.
2. **preview_image** — review the result visually inside the agent chat.
3. **image_info** — verify the actual dimensions and format.
4. **normalize_canvas** — resize/crop to an exact target canvas (e.g. 1080×1920).
5. **convert_image** — export to a different format or apply a final resize.

## License

MIT
