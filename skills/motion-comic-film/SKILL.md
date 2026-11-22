---
name: motion-comic-film
description: Turn an approved narration script into a finished vertical "motion comic" film - AI-generated key stills moved by code (slow camera, pose swaps, rain, lamp flicker, smoke, mist, dust), subtitles, title and end card, mixed sound, one MP4. Use when the user wants a narrated story video, a motion comic, an animated storytelling reel, a horror or mystery story film, or asks to "make the film", "turn this script into a video", "animate these stills", or to redo a film's pictures while keeping its narration. Works with the flow2api skill for images and the story-character-design skill for the cast.
---

# Motion comic film

One still per story beat, drawn by an image model in one consistent style, then animated in code. The stills carry the drawing; code carries the motion. It reads as a narrated comic that moves, costs about 60 image generations for a ten-minute film, and never shows a broken joint, because every pose is drawn whole.

Everything is built in a project folder. Scripts live in `${CLAUDE_SKILL_DIR}/scripts/` (use the skill folder's absolute path if that variable is not expanded).

## What you need

- A narration script the user has approved, split into lines.
- One voice recording per line (any text-to-speech or a human reader).
- The `flow2api` skill with a working server, for images. Each image is a paid generation.
- Python 3.9+, ffmpeg, Node 18+ and Google Chrome. Once: `cd ${CLAUDE_SKILL_DIR}/scripts && npm install`. Pillow is optional (watermark patch, contact sheets).

## When to stop and ask

The user approves: the script and every later change to its words; the cast reference images; the count of paid generations before each batch; the finished film before anything is published. Do the rest without asking.

## Steps

### 1. Start the project

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/new_project.py <project> "FILM TITLE"
```

It creates `index.html` (the stage), `project.json`, and example `lines.json`, `shots.json`, `prompts.json`.

### 2. Check the script before spending anything

Read it as a hostile viewer and list what does not hold up: wrong numbers and dates, a character who knows what they could not know, people who vanish between scenes, a custom or rule the story leans on that is invented or that sources contradict, a twist that is never stated plainly enough to follow. Read `references/lessons.md` (section "Script") for the checks that have caught real problems. Show the user each proposed change as old line and new line, and wait.

### 3. Lines, voice, timing

- Write `lines.json`: one entry per spoken line, `id` in order, `text`, optional `gap` (pause before it), `brk: 2` for a new section.
- Record `voice/<id>.wav` for every line. Check each take with speech recognition against its text and re-record clear misreads.
- A sound word the narrator would otherwise read aloud ("knock, knock", "crack") is a sound effect, not speech: keep it in the text for the subtitle, set `mute_from` (seconds into that line's recording) and add the effect in `sfx.json`.
- Run `python3 ${CLAUDE_SKILL_DIR}/scripts/timeline.py <project>`. It writes `timing.json`, `cues.json` and `out/voice.wav`. The first line starts at 0.3 s so the film opens with sound.

### 4. Cast reference images

Use the `story-character-design` skill to write the character dossier (who each person is, and which visible details carry story meaning). Then generate one full-body reference per main character with `flow2api`, in the film's style, on a plain background. Use the first approved image as the style reference for the others so the whole cast matches. Save them in `refs/`. Show the line-up and wait for approval.

### 5. Shot list and prompts

Read `references/prompts.md`, then fill `prompts.json`:

- One shot per story beat, about one every 10 to 15 seconds; hold a shot longer only when something inside it changes.
- Each scene description says in words who is present, what they do, the light and the weather, and repeats the story-critical details from the dossier. Pass each present character's reference image in `refs`.
- For a scene with no people, use a people-free image as the style reference and write "NO PEOPLE".

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/make_jobs.py <project>           # prints the number of paid generations
python3 <flow2api>/scripts/flow2api.py batch <project>/out/jobs.jsonl --parallel 4
```

### 6. Review every image, regenerate the bad ones

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/prep_images.py <project> --sheet
```

Open the contact sheets and check each image against its line: right people and only those people, story-critical details present, nothing that contradicts the narration, no stray text. Regenerate single shots with `make_jobs.py <project> --only s07,s19`. A few leftovers that do not contradict the story are cheaper to accept than to chase; list them for the user.

### 7. Variants for movement

For the shots where something should visibly happen (a head shake, a hand tightening, eyes opening, a wound spreading), add an entry under `variants` in `prompts.json`: the same image edited with one change. Generate them with `make_jobs.py <project> --variants`. The stage fades between base and variant, once or in a loop, which reads as the character moving. Aim for a variant on a quarter to a third of the shots.

### 8. Build the timeline

Write `shots.json`: for each shot the image name, the `line` it starts on, the camera move `kb` and effects. Field reference and effect list: `references/stage.md`. Run `prep_images.py` again so every image has its 2x sharpened copy in `img/hi/`.

### 9. Render stills, look, then render the film

```sh
node ${CLAUDE_SKILL_DIR}/scripts/render.mjs <project> --stills 2,30,120,300
node ${CLAUDE_SKILL_DIR}/scripts/render.mjs <project> --workers 2
python3 ${CLAUDE_SKILL_DIR}/scripts/mix.py <project> --amb <rain or room tone> --music <bed>
```

`mix.py` masters to -14 LUFS and writes `film.mp4`.

### 10. Check the film yourself before sending it

- Frames every 10 seconds across the whole film, viewed at a size where faces are readable.
- One frame cropped at full resolution: ink lines must be crisp. A thumbnail hides blur.
- The first 3 seconds have sound and the first words; no silent opening.
- Loudness near -14 LUFS, peak below -1 dBFS.
- Subtitles match the final script.

Report what you checked, what is imperfect, and what nobody has listened to yet.

## What this approach does not do

Characters do not walk or act continuously; movement is the fade between two drawn poses plus camera and atmosphere. For one or two shots that need real motion, generate a short image-to-video clip with `flow2api` from the approved still. Cut-out rigging of AI-drawn body parts was tried and dropped: see `references/lessons.md`.

## Files in this skill

| File | Read when |
|---|---|
| `references/prompts.md` | writing scene and variant prompts |
| `references/stage.md` | writing `shots.json`, `project.json`, `sfx.json` |
| `references/lessons.md` | before checking a script, before reviewing images, when something looks wrong |
| `scripts/` | `new_project.py`, `timeline.py`, `make_jobs.py`, `prep_images.py`, `render.mjs`, `mix.py` |
| `stage/index.html` | the page that draws every frame; copied into each project and safe to edit there |
