# motion-comic-studio

A Claude Code plugin for making narrated motion-comic films: a story becomes a cast, the cast becomes consistent AI stills, and code moves, subtitles, mixes and renders them into one vertical MP4.

## Skills

| Skill | What it does |
|---|---|
| `motion-comic-film` | The whole pipeline, from an approved narration script to `film.mp4`: script check, timing, shot list, image batches, pose variants, stage, render, mix. |
| `story-character-design` | Turns a story into a character dossier and a code-drawn cast sheet, so every visible detail has a reason. |
| `flow2api` | Generates images and videos through your own Flow2API server (Gemini image models, Veo, Omni), with validation, batching and safe key handling. |

## Requirements

- Claude Code
- Python 3.9+, ffmpeg, Node 18+, Google Chrome
- Your own Flow2API server and generation key: see [Set up the Flow2API server](#set-up-the-flow2api-server) (images are paid generations on your account)
- Optional: Pillow (watermark patch, contact sheets), VTracer (vector pieces)
- A way to record narration: any text-to-speech tool or a human voice. One audio file per line.

## Install

```text
/plugin marketplace add sonle0311/motion-comic-studio
/plugin install motion-comic-studio@motion-comic-studio
```

Then install the renderer's one dependency:

```sh
cd <plugin folder>/skills/motion-comic-film/scripts && npm install
```

## Set up the Flow2API server

The `flow2api` skill is only a client. Image and video generation happens on a Flow2API server that you run yourself, signed in with your own Google Flow account. The server is a separate project:

- Server used with this plugin: https://github.com/sonle0311/flow2api (a fork with extra fixes)
- Original project: https://github.com/TheSmallHanCat/flow2api (MIT, by TheSmallHanCat)

Quick start with Docker:

```sh
git clone https://github.com/sonle0311/flow2api.git
cd flow2api
docker compose up -d
```

Or without Docker:

```sh
git clone https://github.com/sonle0311/flow2api.git
cd flow2api
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python main.py
```

The server listens on port 8000. Open its admin page, add your Flow account, choose a captcha method and create a generation key; the server's own README covers each step. Then give this plugin the service root (for a local server, `http://localhost:8000`) and that key as described below.

## Configure Flow2API

Either run `/plugin configure motion-comic-studio@motion-comic-studio` and fill in the service root and key, or write the config file from your own terminal (the key is read with a hidden prompt and never shown):

```sh
mkdir -p ~/.config/flow2api && printf 'Flow2API key: ' && IFS= read -rs K && printf 'FLOW2API_BASE_URL=http://localhost:8000\nFLOW2API_API_KEY=%s\n' "$K" > ~/.config/flow2api/env && chmod 600 ~/.config/flow2api/env && unset K && echo
```

Ask Claude to "check the Flow2API connection"; it runs a free, read-only check.

## Use

Give Claude a script and say what you want:

> Make a motion-comic film from this script. Vertical, about ten minutes. Here is the narration audio folder.

Claude checks the script, proposes the cast, tells you how many paid generations each batch needs and waits for your yes, then builds the film and reports what it checked.

## What to expect

- About 60 image generations for a ten-minute film: one reference per main character, 40 to 45 scene stills, 15 or so pose variants.
- Characters do not walk; movement is camera, atmosphere and fades between two drawn poses.
- At 1K source images, very tight zooms look soft. Larger sizes need a server account that allows them.

## License

MIT
