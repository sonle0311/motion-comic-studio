# Mistakes already made and how they were fixed (shared by every project)

Read this before you inspect images. Add a line whenever you fix a mistake that another project could also hit. A mistake that belongs to one project only goes into that project's `MISTAKES-LOG.md`.

## Character design

| Mistake | Cause | Fix | Re-check with |
|---|---|---|---|
| A hat or fringe covers the eyebrows | the lower edge of the hat is below the eyebrow line (hy − 0.11 or higher up) | raise the hat, or lower the eyebrows with `brow_dy`; with glasses, the eyebrows sit between the rim of the glasses and the brim of the hat | count two eyebrows in every expression cell |
| Ear, glasses arm and sideburn pile up into a tangle | three small details within 0.15 D | remove one detail (usually the ear) | look at it at D = 130 px |
| The character sinks into a dark background | the ink-blue outline is nearly the background colour | turn on `halo=True` | the line-up on a dark background |
| The eyes look blank and white | the highlight `hl` is larger than 0.026 | reduce `hl` | the expression sheet |
| The prop covers the hand | the object is drawn after the hand | draw a held object first, the hand after it | check every character that has a prop |
| A calm character cannot show strong emotion | the character's drooping lid is applied to every expression | give expressions that need open eyes `"open": True` | the "eureka" and "surprised" cells |
| Two characters are hard to tell apart | they differ only in colour and face | change the height, the head shape or the prop | the silhouette image |
| A soft prop (rag, scarf, bag) drawn as a round lump with dots looks like a face | a blob plus two or three round dots reads as eyes and a nose | draw soft things hanging down with a jagged edge; stains are long smears, not round dots | the cast image shrunk down |
| The hair patch at the temple turns into a rectangle like an ear flap | straight edges, patch too big | round it with curves, no taller than 0.26 D | the cast image |
| A scared or horrified expression looks like laughing | the `open` mouth is an open-mouthed laugh | scared expressions use `o` or `wavy`; separate them from "surprised" with reversed slanted eyebrows and a symbol | the expression sheet, with the eyes covered so you see only the mouth |
| A detail that sticks out of the head (a tuft, a bow) does not show | it is drawn in `hair`, which is clipped to the head shape | draw anything that sticks out in `hat` or `back` | the silhouette image |
| The hand covers a prop that is a clue in the story | the hand sits exactly where the object is | move the hand to the strap or handle, draw the hand first and the clue part after it | check the clue detail on its own in every cell |

## Working with the reviewer

| Mistake | Cause | Fix |
|---|---|---|
| Told to "improve it", then stuffing in more detail (for example a fist with every knuckle), which breaks the style | reading "improve" as "add" | ask which part, ask for a tight crop; the default is to simplify, not to add |
| Inventing names, relationships and backstory and writing them down as settled | deciding on the user's behalf | write "proposed, awaiting approval" until the user chooses |
| The user changes a character's role or personality but the drawing keeps the traits of the old role (a quiet man becomes a chatterbox yet still has a moustache over his mouth and drooping lids) | only the name and the lines were changed | every time the story changes a role, go through each "from story to design" row in the dossier; when a trait has lost its reason, tell the user and propose a change |

## Rigging cut-out puppets (AI images or code drawings)

| Mistake | Cause | Fix |
|---|---|---|
| Gaps at the joints, or pieces overlapping untidily | joint points placed by eye | measure automatically: take the main axis of the piece's pixel region and pull the two end points in by half the thickness; define angle 0 as the limb hanging straight down |
| Feet slide on the ground | the step phase is not tied to the distance travelled | phase = distance / (2 × stride); the planted foot stays still; solve the leg with two-bone IK |
| The knee bends backwards | wrong sign for the bend direction in the IK | facing right, the knee points to +x; check with one frame of a straight leg |
| The character never stops fidgeting | several small motions stacked while standing still | standing still is gentle breathing only; a tremble or a jolt only for a reason, and it fades out |
| Wrong layer order: the back arm lies over the body | drawing order does not follow depth | back arm, back leg → front leg → body → head → front arm → held prop |

## Watch for these when you build moving scenes later

These two come from a reference video and have not yet appeared in a project:

- A character jumps back to its old position at a beat change. Each segment is correct on its own, so you have to watch them in sequence.
- An impact effect is drawn over the hand. The right order: body → effect → hand → text.

## Technical

| Mistake | Cause | Fix |
|---|---|---|
| PNG export fails | the machine has no rsvg, cairosvg or ImageMagick | capture the SVG with headless Chrome (`export.py` already does this); with no Chrome, set the `CHROME` variable or deliver SVG only |
| Two shapes share one `clipPath`, so the clipping is wrong | duplicate ids in the same SVG file | always get ids from `uid()` |
