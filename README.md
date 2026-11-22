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
- Your own Flow2API server and generation key (images are paid generations on your account)
- Optional: Pillow (watermark patch, contact sheets), VTracer (vector pieces)
- A way to record narration: any text-to-speech tool or a human voice. One audio file per line.

## Install

```text
/plugin marketplace add <owner>/motion-comic-studio
/plugin install motion-comic-studio@motion-comic-studio
```

Then install the renderer's one dependency:

```sh
cd <plugin folder>/skills/motion-comic-film/scripts && npm install
```

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
