# Lessons

Each line is a mistake that was made, found by a viewer or a review, and fixed. Add to it.

## Script

| Check | Why |
|---|---|
| Add up every number: years, ages, counts | "twenty years in the ground" beside a death eleven years earlier is the first thing a viewer catches |
| For every drastic act, ask why the easier option was not taken, and answer it in one spoken line | viewers ask "why not just burn it?"; a reason that lives only in the writer's head is a hole |
| State the twist once in plain words at the moment of discovery, and once in the aftermath | a reveal built only from clues (a name on a card, a face that does not match) was not understood |
| Who is present in each scene, and where did the others go | four men open a coffin, two remain an hour later, with no line saying the others left |
| Would the authorities, the family or the neighbours really do nothing | a body found in the wrong grave needs more than "they took a note" |
| Every rule the story sets up must pay off | a taboo repeated three times and then broken with no consequence reads as forgotten |
| Customs and beliefs the plot leans on must be real and sourced | an invented custom reads as fake to people who know the real ones; search, and drop what sources contradict |
| Two films in a row must not share a frame | "a note with four rules" twice, or the same kind of ghost twice, reads as repetition |

## Images

| Problem | Fix |
|---|---|
| A character leaks into a scene because their image was the style reference | style-reference a people-free image for empty scenes; say "NO PEOPLE" |
| The same prop differs between shots | describe it in every prompt that shows it |
| Watermark in the bottom-right corner | `prep_images.py` patches it; check corners after upscaling |
| Fake lettering on walls and papers | ask for illegible text; crop or frame it out with `kb` |
| Two drawings of the same moment do not match (eyes closed in one render, open in a separately generated one) | make the second by editing the first, not by a new generation |

## Motion

| Tried | Result |
|---|---|
| Replacing the frame with a VTracer SVG to jitter each path | at a few thousand paths, thin ink lines and small patterns merge into blotches; the film looked blurred at full size though thumbnails looked fine. Keep the raster, upscale 2x with lanczos and unsharp, jitter the whole frame |
| Cutting an AI-drawn parts sheet into limbs and rigging them | parts are drawn in perspective, so joints never line up at every angle; took five rounds to look acceptable and still read as a puppet. Use it for props and swappable heads or hands only |
| Many small sine movements while a character stands | reads as twitching. At rest: breathing only |
| Reviewing a render on a contact sheet | hid the blur. Always crop one frame at full resolution |
| Four render workers each loading large per-shot data | browser crashed at start. Two workers, or lighter assets |

## Sound

| Problem | Fix |
|---|---|
| Narrator reads sound words aloud | mute that part of the take, play a real effect, keep the word in the subtitle |
| Film opens with seconds of near silence | first words inside the first half second, ambience from frame one; viewers leave in the first three seconds |
| Constant rain and music feel noisy against the voice | ambience about 26 dB and music about 24 dB under the voice; high-pass the voice at 85 Hz and cut a little at 220 Hz |

## Review

- Send the user a small preview file when the master is large; say which file is the master.
- Say what was not checked. "Nobody has listened to the whole film" is information the user needs.
