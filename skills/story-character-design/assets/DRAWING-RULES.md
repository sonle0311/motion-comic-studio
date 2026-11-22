# Character drawing rules

Every measurement is in **D = the width of the head**. The origin is the point between the two feet on the ground. The numbers here match `drawkit/core.py`; change one place and change the other too.

These numbers are **made up** (version 0), not measured from any reference image. When you have a reference image in a style you like, measure it and update the tables below.

## Shared measurements

| Item | Value |
|---|---|
| Head | 1 D wide, 0.92 D tall, a rounded square with corner radius 0.42 D |
| Chin overlap on the body | 0.09 D (there is no neck) |
| Body | a flared coat shape: shoulders 0.54–0.60 D wide, hem 0.88–1.0 D wide |
| Legs | no legs are drawn; two oval shoe tips, 0.34 × 0.15 D, peek out below the hem |
| Outer outline | 0.04 D, ink blue `#1b2233` (never pure black) |
| Inner detail lines | 0.026 D |
| Shade | one tone, 14% ink over the back side (the left), with a straight edge |
| Ground shadow | an oval at 18% opacity |
| Face | shifted 0.10 D right of the head centre (3/4 view) |
| Eyes | 0.36 D apart; the far eye is 88% as wide as the near eye |
| Hand | a circle of radius 0.105 D, floating, drawn only when it holds something or points |
| Paper rim | 0.035 D in `#efe6d2`, turned on only when the character stands on a dark background |

## House rules

1. Characters face 3/4 to the right by default. To face left, flip the whole character (`flip=True`).
2. No arms are drawn.
3. Each character is recognised by three things: hairstyle or hat, outfit, one prop.
4. Expressions change through the eyes and eyebrows first; the mouth is small.
5. Every character has the full set of expressions in `EXPRESSIONS`: neutral, happy, angry, sad, surprised, scared, suspicious, eureka, smug, oops, wink, smirk. Add or remove expressions to suit the genre.
6. Symbols that go with expressions: angry = a red vein; sad = a tear; scared = three purple lines and a drop of sweat; eureka = three yellow rays; smug = two sparkles; oops = one big drop of sweat behind the head.
7. The layer order of hand and prop is declared per prop: for a held object (a notebook, the handle of a magnifying glass) the hand is on top; for an object swung or pointed outward (a stick, a torch) the object is on top.
8. Drawing real people: funny but not demeaning, never exaggerating a physical flaw.

## Palette

| Role | Code |
|---|---|
| Outline ink | `#1b2233` |
| Skin | `#f3d2b0` |
| File paper | `#efe6d2` |
| Night background | `#141a2a` |
| Desk-lamp yellow | `#f6c343` |
| Stamp red | `#d8342b` |

## Characters

One column per character: height, body height, the three identifiers, prop, eyes, mouth.

| | Character 1 | Character 2 |
|---|---|---|
| Height | | |
| Body height | | |
| Identifiers | | |
| Prop | | |
| Eyes | | |
| Mouth | | |
