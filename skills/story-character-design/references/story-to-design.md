# From story to design

A viewer meets a character for a few seconds on a phone screen. The design has to do the introduction: one look should tell who is old and who is young, who leads whom, who can be trusted. So start from the story, not from the drawing.

## Step A: take six things about each character from the story

1. **Role:** guide, learner, troublemaker, victim, suspect, narrator.
2. **Age and build.**
3. **Three personality words**, one of which is a weakness.
4. **Relationship** with each other main character (mentor and pupil, neighbours, rivals).
5. **A habit or catchphrase.**
6. **Their object:** the thing this person always carries or works with.

Where the story is silent, propose something and mark it "proposed, awaiting approval".

## Step B: turn story traits into visual traits

| Trait in the story | Design decision | Key in the declaration |
|---|---|---|
| Age, build | body height; a child has a short body and the same head, so the head looks big | `body_h` 0.85–0.95 (child), 1.05–1.25 (adult) |
| Figure: thin, stocky, imposing | shoulder and hem width | `top_w`, `body_w` |
| Quiet, reserved | cover the mouth (moustache, scarf, high collar); the mouth shows only at a climax | `mouth_hidden: True` |
| Talkative, blunt | always has a mouth | `mouth_default: "smile"` |
| Calm, seasoned, tired | drooping lids, small eyes | `lid` 0.2–0.35, small `eye_ry` |
| Naive, curious | big eyes, big highlight, blush | `eye_rx`, `eye_ry`, `hl`, `face_under` |
| Job, habit | one single prop | `prop` |
| Status, circumstances | the material and neatness of the outfit | `body_details`, `neck` |
| Lead | a bright coat colour that stands well apart from the background | `coat` |
| Supporting role, suspect | quieter colour than the leads, so the eye goes to the leads first | `coat` |
| Villain, someone suspicious | do not draw them ugly; use drooping lids, slanted eyebrows, cool colours | `lid`, `brow_tilt` in the default expression |

Every detail must answer "what does this say about this person in the story?". If two details say the same thing, keep one.

## Step C: make the cast different from each other

Characters who stand next to each other must differ in at least three of these five points:

1. **Height** (a difference only shows from 0.3 D upward).
2. **Head shape:** hat, hairstyle, anything that sticks out of the head (hair bunches, a hat brim).
3. **Coat colour:** one dominant colour per main character, no two in the same tone.
4. **Prop.**
5. **Face:** glasses, moustache, blush, big or small eyes.

Check with `silhouettes.png`: if two silhouettes look alike, change point 1, 2 or 4, because colour and face do not show in a silhouette.

The relationship between two characters should be visible as contrast. Mentor and pupil: tall and short, muted and bright, mouth covered and mouth showing. Rivals: same height, opposing colours.

## Step D: supporting characters per episode

A character who appears in only one episode (a suspect, a witness) uses the same drawing machine but fewer details than a lead: hair, one coat colour, one prop. If the prop or the outfit is a clue in that episode (a dry coat, wet shoes, oil on the hands), say so in the dossier so that nobody "tidies up" the clue.

## Example: a detective and his apprentice

| | The detective | The apprentice |
|---|---|---|
| Role | guide | learner, asks the questions the audience would ask |
| Age | about 60 | about 12 |
| Personality | quiet, meticulous, stubborn | quick, curious, hasty |
| From story to design | quiet → moustache covers the mouth; seasoned → lids drooping 28%; takes notes → notebook | talkative → always has a mouth; curious → big eyes and a magnifying glass; a child → body 0.92 D |
| Contrast | 2.36 D tall, muted brown coat, flat cap | 1.80 D tall, bright yellow coat, two hair bunches |

When the story changes, the table changes with it. In `examples/detective-club/cast.py` the same detective was later rewritten as a talkative man who takes the credit, so his mouth now shows below the moustache and his lids no longer droop.
