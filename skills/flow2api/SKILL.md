---
name: flow2api
description: Generate AI images and videos through a self-hosted Flow2API server (Gemini image models, Veo 3.1, Omni). Use whenever the user asks to generate an AI image or AI video, make character art, keyframes, thumbnails or reference sheets, edit an image (image-to-image), turn an image into video, make a reference-to-video clip or extend a Flow video, or mentions Flow2API, Veo, Gemini image, nano banana or omni-flash. Also use it to check the Flow2API connection or to list which model and option combinations are valid. Every generation is paid, so only generate when the user asked for that output.
---

# Flow2API

Call a Flow2API server to generate images and videos. Flow2API is a self-hosted service with an OpenAI-compatible `POST /v1/chat/completions` endpoint that returns generated media.

The client is one Python script, `scripts/flow2api.py`, next to this file. It needs Python 3.9+ and only the standard library.

## Configuration

| Variable | Value | Notes |
|---|---|---|
| `FLOW2API_BASE_URL` | default `http://localhost:8000` | service root, **without** `/v1`; keep a proxy prefix if there is one |
| `FLOW2API_API_KEY` | generation key | secret |
| `FLOW2API_MAX_PARALLEL_IMAGE` / `_VIDEO` | 9 / 6 | client-side limit on parallel requests |

The script looks up the base URL and the key in this order and takes the first value it finds:

1. The environment variable (`FLOW2API_BASE_URL`, `FLOW2API_API_KEY`).
2. Optional: `CLAUDE_PLUGIN_OPTION_FLOW2API_BASE_URL` and `CLAUDE_PLUGIN_OPTION_FLOW2API_API_KEY`. A plugin that declares these options in its `userConfig` can supply them this way. Nothing breaks if they are absent.
3. The config file `~/.config/flow2api/env` (`KEY=value` lines, mode 600).

**The key is a secret:**
- Never ask for the key in chat. Never print it. Never write it into a project file or a command argument.
- If `check` reports `key: NOT SET`, ask the user to create the config file themselves, in their own terminal. This command reads the key with a hidden prompt:

```bash
mkdir -p ~/.config/flow2api && printf 'Flow2API key: ' && IFS= read -rs K && printf 'FLOW2API_BASE_URL=http://localhost:8000\nFLOW2API_API_KEY=%s\n' "$K" > ~/.config/flow2api/env && chmod 600 ~/.config/flow2api/env && unset K && echo
```

If the server is not on `localhost:8000`, the user changes the URL in that command or edits the file afterwards.

## Commands

`${CLAUDE_SKILL_DIR}` is the folder that holds this SKILL.md. If the variable is not expanded, use the absolute path of this folder.

```bash
S="${CLAUDE_SKILL_DIR}/scripts/flow2api.py"
python3 "$S" check            # GET /v1/models + /aliases; free; run this first
python3 "$S" models           # table of valid models and combinations (local, no network)
python3 "$S" image "prompt" --aspect 9:16 --size 1K --out <dir> --name <name>
python3 "$S" image "keep the character, change the setting..." --ref character.png --out ...   # image-to-image
python3 "$S" video "prompt" --model veo-3.1-fast --mode t2v --aspect 9:16 --duration 8 --out ...
python3 "$S" video "slow camera push" --mode i2v --ref first.png [--ref last.png] --duration 4 --out ...
python3 "$S" video "..." --mode r2v --ref subject.png --ref style.png          # 1–3 reference images
python3 "$S" video "continue" --mode extend --extend <media_id> --out ...      # extend a Flow video
python3 "$S" batch jobs.jsonl --parallel 3   # one job per line: {"kind":"image","prompt":"...","aspect":"9:16","ref":["a.png"],"out":"...","name":"..."}
```

- For a long prompt, use `--prompt-file file.txt`.
- Each result is saved as `<name>.png|.jpg|.mp4` with a `<name>.json` beside it. The JSON file records the model, the config, the prompt and the `media_id`. Keep the `media_id`: you need it to extend a video.
- The image file extension is taken from the file's bytes, not from the URL, so a 1K image may arrive as `.jpg` even when you expected `.png`. Read the real path from the `file` field of the JSON.
- Progress is printed to stderr.

## Models and valid combinations

Use only the combinations in these tables. The script checks before it sends and rejects an invalid combination.

| Image | aspect | size | reference images |
|---|---|---|---|
| `gemini-3.0-pro-image` (best quality) | 16:9, 9:16, 1:1, 4:3, 3:4 | 1K, 2K, 4K | 0 or more |
| `gemini-3.1-flash-image` (default) | same | same | 0 or more |
| `gemini-3.1-flash-lite-image` (fast, cheap) | same | same | 0 or more |

| Video | mode | aspect | seconds | images |
|---|---|---|---|---|
| `veo-3.1-fast` / `veo-3.1-lite` | t2v | 16:9, 9:16 | 4, 6, 8 | 0 |
| | i2v | 16:9, 9:16 | 4, 6 | 1–2 (first frame, last frame) |
| | r2v | 16:9, 9:16 | 8 | 1–3 (subject or style references) |
| | extend | 16:9, 9:16 | 8 | 0, plus `--extend ID` |
| `veo-3.1-quality` | t2v, i2v, extend (no r2v) | same | same | same |
| `omni-1.1-flash` | auto | 16:9, 9:16 | 4, 6, 8, 10 | 0–3 |
| `omni-1.2-flash` | auto | 16:9, 9:16 | 16:9: 3–10; 9:16: 3–15 | 0–3 |

Defaults: image 16:9 at 1K; Veo t2v 8 s, i2v 4 s; Omni auto 8 s.

## Rules

1. **Generations cost money.**
   - Run `image` or `video` only when the user asked for that exact output.
   - For a large batch or for video, state the number of generations first and wait for the user to agree.
   - `check` and `models` are free; run them whenever you need.
2. **Do not resend blindly.**
   - The script retries by itself on HTTP 429, quota errors and reCAPTCHA errors (after 5, 15 and 45 seconds).
   - Report any other error to the user. A dropped connection or a timeout does not mean the upstream job stopped; look in the output folder before you send the job again.
3. **Common errors:**
   - 401: wrong key.
   - 400/422: invalid combination or wrong data type. Keep the user's choices and fix only the part that is wrong.
   - 403: the account is not permitted.
   - 503: the server is out of tokens.
   - 502/504: upstream error.
4. **Servers without a Pro account.**
   - Some servers have no Pro account. On those servers `gemini-3.0-pro-image` and the 2K and 4K sizes fail with a "Pro account required" error. The server's message may be in Chinese: `需要 Pro 账号`.
   - The error arrives at the start, before any image is generated.
   - Fall back to `gemini-3.1-flash-image` at `1K`, and tell the user you did.
5. **Keep a character consistent across images:**
   - Generate one reference image per character (full body, plain background) and have the user approve it.
   - Pass that reference with `--ref` for every later image of the character. In the prompt, say "keep the face, hairstyle and outfit of the character in the reference image".
   - A style reference that contains a character tends to leak that character into scenes where they should not appear. For an empty scene, use an image without people as the style reference.
6. **Variants for simple animation:**
   - To get a second pose, edit the same image: pass it with `--ref` and prompt "keep everything, change only X" (for example, "change only the arm: raised").
   - The two images then match closely enough to alternate as a two-frame animation.
7. **Prompts:**
   - Write prompts in English; results are more stable. If the content is in another language, describe it in words.
   - State the style, the framing, the lighting, and what you do not want (text, logos, watermarks).
   - Do not generate recognisable real people, deceptive content or other people's brands.
8. **Open each result with an image viewer tool and inspect it yourself** (hands, faces, stray text) before you show it to the user.
9. **Watermark.** Generated images may carry a small watermark in the bottom-right corner. Crop it out or patch over it before use.
10. Omni and Veo videos have no resolution option, and the server cannot upscale an existing video.

## AI image to SVG (optional)

Use this when a piece of art needs a big zoom or its shapes need to be separated for animation in code.

- Use VTracer. Installing it needs the user's agreement: `python3 -m venv ~/.venvs/vtracer && ~/.venvs/vtracer/bin/pip install vtracer`.
- Vectorising works well only on images generated in a style such as "flat cel shading, clean bold outlines, limited palette, plain background".
- Soft gradients turn into poster-like bands of colour after vectorising.
- Two useful settings (figures are approximate, for an image of about 768×1376):
  - **Detailed**: `filter_speckle=4, color_precision=6, layer_difference=16`. Close to the original; a few thousand paths; 1 MB or more.
  - **Flat**: `filter_speckle=12, color_precision=5, layer_difference=40`. A few hundred paths; a few hundred KB. Ink lines on faces and folds in clothing are lost. High-contrast images (light background, white clothing) survive better than dark ones.
- Python call: `vtracer.convert_image_to_svg_py(in, out, colormode="color", hierarchical="stacked", mode="spline", ...)`.
- **Do not replace the raster frame with the SVG for full-screen video.** At a few thousand paths, thin ink lines and small patterns merge into blotches, and the frame looks blurry. For a sharper full-screen frame, upscale the raster image 2× with lanczos and then apply an unsharp mask.
- The SVG is a stack of colour shapes. It does **not** come with hands, face or hair as separate parts. To move a character, generate each layer as a separate image, or cut the shapes into regions yourself.

## Testing the script

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/test_flow2api.py"
```

The tests use a local fake server and cost nothing. They cover: config priority, combination checks, parameter types, reference images, SSE frames split across chunks, CRLF, errors inside a stream, a missing `[DONE]`, 401/422 without leaking the key, safe media download, and extending by `media_id`.
