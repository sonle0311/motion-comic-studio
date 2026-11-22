---
name: story-character-design
description: Design a cast of 2D characters from a story and draw them with code (Python generating SVG, exported to PNG), with no image-generation model. Use this whenever the user wants to create, add, restyle or fix characters for a channel, series, story, comic or animated video; asks to design characters from a story, draw a character, add a supporting character, or make a character sheet, an expression sheet or a cast line-up; gives a script, case file or story outline and wants the people in it drawn; or says characters look alike, look off-model or do not fit the story. Also use it to keep every later character in the same style as the ones already built.
---

# Story character design

This skill turns a story into a cast of 2D characters drawn with code. Nothing is drawn by hand and no image generator is used. Each character is a short declaration; head, body, hands, eyes, mouth and expressions are shared functions, so one fix changes the whole cast and every later character comes out in the same style.

Idea: write a drawing machine, turn every size into a number, let the user approve by criticising, log every fix.

## When to stop and ask

Character design is the user's aesthetic decision. Run the whole build-and-inspect loop yourself, but show the images to the user for approval before you go on to supporting characters, motion or video. Character names, the relationships between characters and the backstory are also the user's to settle: you may propose them, but do not write them into the dossier as settled.

## Workflow

### 1. Put the drawing machine into the project

If the project has no `drawkit/` folder yet:

```sh
python3 <skill-dir>/scripts/init_project.py <project-dir>
```

The command copies `drawkit/core.py`, `drawkit/export.py`, the template `drawkit/cast.py` and three files: `CHARACTER-DOSSIER.md`, `DRAWING-RULES.md`, `MISTAKES-LOG.md`. Files that already exist are left alone. Each project keeps its own copy of the drawing machine because each series has its own measurements and house rules.

If the project already has `drawkit/`, read the project's `DRAWING-RULES.md` and `MISTAKES-LOG.md` before you draw anything.

### 2. Read the story and write the character dossier

Read the script, outline or channel description, then fill in `CHARACTER-DOSSIER.md`. For each character you need: their role in the story, age and build, three personality words, relationships with the others, a habit or catchphrase, and the object that belongs with them. Propose whatever is missing and mark it "proposed, awaiting approval".

Then turn each story trait into one design decision. The conversion table and an example are in `references/story-to-design.md`; read that file before you declare the first character of a project. The root principle: every detail in the drawing must answer the question "what does this say about this person in the story?". Drop any detail that cannot answer it.

### 3. Settle the style: measure a reference or use the defaults

- **The user has a reference image:** measure it, do not eyeball it. Write a small script that measures the image: head width (this becomes D), total height over D, body height over D, outline thickness over D, the skin and outline colour codes, and the share of the area that is shaded. Write the results into the project's `DRAWING-RULES.md` and change the matching constants in `core.py`. Learn only the proportions, the line work and the way colours are combined; the characters must belong to this project, never copy characters from the reference.
- **No reference:** use the defaults in `DRAWING-RULES.md` and tell the user plainly that these numbers are made up, not measured from a style they like.

### 4. Declare the characters

Add one block per character to `drawkit/cast.py` and put it in `CAST`. The meaning of every key, the hook functions (hair, hat, coat, prop), the landmark table and the layer order are in `references/declaring-characters.md`. A complete example with two leads and an episode's supporting cast: `examples/detective-club/cast.py`.

Default house rules (a project may change them in its own `DRAWING-RULES.md`):

1. Characters face 3/4 to the right; to face left, flip the whole character.
2. No arms are drawn; a floating round hand appears only when it holds something or points.
3. A character is recognised by exactly three things: hair or hat, outfit, one prop.
4. Expressions change through the eyes and eyebrows first; the mouth is small.
5. Every character has the full set of expressions in `EXPRESSIONS`. The set is the project's to change: when a genre needs its own expression, add it there once and the whole cast has it.
6. When drawing a real person, be funny without being demeaning: identify them by a symbol everyone knows, never by exaggerating a physical flaw.

### 5. Export the images and inspect them yourself

```sh
python3 drawkit/export.py
```

The command prints declaration warnings, then exports an expression sheet per character (`expression-sheet-<slug>`), a line-up of the leads (`cast-lineup`), a supporting-cast image for each episode (`episode-<id>-cast`, for characters that have an `episode` key) and a silhouette test (`silhouettes`). Open every PNG with an image-reading tool and check this list before showing the user:

- Both eyes and both eyebrows are there in every expression cell; no hat, hair or glasses covers them.
- The expression cells are clearly different from each other when shrunk to a quarter of their size.
- Hands and props are layered in the right order; nothing is cut off at the edge of the image.
- On a dark background the character does not sink into it (turn on the paper rim, `halo=True`).
- Silhouettes: with the names covered you can still tell who is who. If two silhouettes look alike, change the hat, hair, height or prop of one of them.
- Next to the existing characters: same outline thickness, same kind of shading, same level of detail.

Whenever you fix a mistake, write it into the project's `MISTAKES-LOG.md` (step 7).

### 6. Show the user and take the criticism

Send the line-up and the expression sheets. Say plainly which numbers are made up and what has not been done. When the user criticises:

- Specific criticism, or criticism with a picture: fix exactly that spot, and fix it in the shared function if the fault belongs to the whole cast.
- Vague criticism ("make it nicer", "improve it", "not quite there"): do not add detail. Ask which part, or ask for a tight crop of the detail they mean. Adding detail is the most common misreading, and it pulls the character away from the minimal style.
- Every time a fix changes a number, update that number in `DRAWING-RULES.md`.

### 7. Log the lesson

For each mistake you fix, add one line to the project's `MISTAKES-LOG.md`: the mistake, the cause, the fix, how to re-check it. If the mistake is not specific to this project and characters in other projects would hit it too, add it to the skill's `references/mistakes-log.md` as well, so every later project avoids it. This is the most valuable part of the skill; do not skip it because you are in a hurry.

## Files in the skill

| File | Read it when |
|---|---|
| `references/story-to-design.md` | writing the dossier and turning story traits into visual traits |
| `references/declaring-characters.md` | writing or editing a declaration; you need landmarks or the layer order |
| `references/mistakes-log.md` | before inspecting images; after fixing a mistake that other projects share |
| `assets/DRAWING-RULES.md` | you need the default measurements and the palette |
| `examples/detective-club/cast.py` | you need a full declaration example (an old detective with cap, glasses and moustache; a girl with two hair bunches; four supporting characters for one episode) |
| `scripts/drawkit/` | the master copy of the drawing machine; `init_project.py --update` copies core.py and export.py into the project again |

## Requirements

Python 3 with the standard library only. PNG export needs Google Chrome, Chromium or Microsoft Edge, run headless; set the `CHROME` environment variable to the browser binary if it is not in a standard place. Without a browser the export still writes the SVG files.

## Scope

This skill stops at still images: characters, expressions, the line-up. Motion, backgrounds, camera, effects and sound are not part of it. If the user needs them, build them in the project and suggest adding them to the skill once they work reliably.
