# Writing prompts

## Scene prompts

`prompts.json` has a shared `style` prefix and one `scene` per shot. The prefix fixes what must not vary:

- the drawing style, described in words as well as by reference image (outline, shading, palette);
- "keep the exact face, hair and clothes of each referenced character";
- the framing rule: main subject in the upper two thirds, lower fifth calm and dark, because subtitles sit there;
- what must not appear: text, letters, logos, watermarks.

Each scene then says, in this order: place and time, weather and light, who is there (name the reference: "the old man from the reference (grey goatee, brown shirt, checked scarf)"), what each person is doing, and the one detail the narration depends on. Write prompts in English; describe non-English text content in words and ask for it to be illegible, because image models draw fake lettering.

Things that reliably go wrong, and the wording that prevents them:

| Problem | Wording |
|---|---|
| A referenced character appears in a scene they are not in | use a people-free image as the style reference; write "NO PEOPLE in the foreground" |
| A covered face is drawn as a cartoon ghost | "smooth cloth with NO holes, NO drawn eyes and NO mouth; it only dips slightly where the eyes are" |
| Gore | "not gory, no blood" or "a thin line and a few drops only"; show the tool, the reaction and the result, not the wound |
| Readable fake text on documents and signs | "all printed text is blurred and illegible" |
| A prop changes colour or material between shots | repeat the prop's description in every scene that shows it |

## Variant prompts

A variant is an edit of an existing shot, with that shot as its only reference:

> Edit the reference image. Keep EXACTLY the same composition, camera, characters, clothes, drawing style, background and lighting. Change ONLY this: the old man has turned his head to the other side, eyes closed, mid head-shake.

Change one thing per variant: a head turn, a mouth, an arm, a state (wound spreads, body swells, eyes open). The model keeps the rest close enough that a fade between the two reads as movement. Do not ask for a new camera angle; that is a new shot.

Good candidates: someone speaking a quoted line (mouth and eyes), a refusal or argument (loop between two poses), knocking or pounding (fast loop), a slow change the narration describes (one long fade), the film's key reveal (fast fade timed to the word).

## References

- One approved full-body image per main character, plain background.
- Pass at most the characters who are in the scene, plus nothing else. Extra references leak into the picture.
- A character seen only as an object (a portrait on an altar, a photo on an ID card) gets its own reference of that object.
