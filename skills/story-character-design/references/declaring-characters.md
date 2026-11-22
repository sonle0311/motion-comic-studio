# Declaring characters

A character is a `dict` in `drawkit/cast.py`, listed in `CAST`. The drawing machine in `core.py` takes care of everything shared.

## Coordinate system

- The unit is **D** = the width of the head. Every number, line thickness included, is in D.
- The origin (0, 0) is between the two feet on the ground. **Negative y is up.**
- Characters face 3/4 to the right: the front is positive x, the back is negative x.

## Landmarks

Let `t = body_top(P)` = −(0.05 + `body_h`) and `(hx, hy) = head_center(P)`.

| Landmark | Coordinates |
|---|---|
| Head centre | hx = 0.03; hy = t + 0.09 − 0.46 |
| Head | from hx − 0.5 to hx + 0.5; from hy − 0.46 (crown) to hy + 0.46 (chin) |
| Near eye, far eye | (hx − 0.09, hy + 0.06) and (hx + 0.27, hy + 0.06); get them from `face_points(P)` |
| Mouth | (hx + 0.14, hy + 0.27) |
| Top edge of the body | y = t; the chin overlaps down to t + 0.09 |
| Hem | y = −0.05 |
| Hand holding something in front | x from 0.49 to 0.62; y from −0.37 (child) to −0.67 (adult) |

## Required keys

| Key | Meaning |
|---|---|
| `name`, `slug` | display name; file name in plain lowercase ASCII, unique in the cast |
| `body_h` | body height |
| `body_w`, `top_w` | half the hem width, half the shoulder width (`top_w` < `body_w` ≤ 0.62) |
| `coat` | coat colour |
| `brow` | eyebrow colour |
| `top` | highest point relative to the head centre; −0.46 is a bare crown, more negative with a hat. Expression symbols (red vein, purple lines, yellow rays) follow this number |
| `body_details` | function `(P, t)` that draws the details on the coat |

## Optional keys

| Key | Default | Meaning |
|---|---|---|
| `role` | none | the line under the name in the cast line-up |
| `episode` | none | the episode id of a supporting character, for example `"001"`. A character with `episode` is left out of the line-up and goes into that episode's `episode-<id>-cast` image |
| `lineup_expr` | `neutral` | the expression used in the line-up |
| `skin`, `shoe` | shared colours | skin colour, shoe colour |
| `eye_rx`, `eye_ry` | 0.05; 0.08 | half width and half height of the eye |
| `hl` | 0.018 | radius of the highlight in the eye; above 0.026 the eye looks blank and white |
| `lid` | 0 | drooping eyelid, from 0 to 0.5 |
| `brow_w`, `brow_dy` | 0.032; 0 | eyebrow thickness; shift the eyebrows up (negative) or down |
| `mouth_default` | no mouth | `smile`, `flat`, `frown`, `open`, `o`, `wavy`, `grin`, `grit`, `smirk` |
| `mouth_hidden` | False | True: the mouth shows only for `o` and `wavy` (a moustache or scarf hides it) |
| `mouth_dy` | 0 | shift the mouth down when there is a moustache |

## Hook functions and layer order

Drawing goes from bottom to top in exactly this order:

1. ground shadow, shoes
2. `back(P)`: things behind both body and head (hair bunches, a cape, a backpack)
3. body; inside the body comes `body_details(P, t)`, **clipped to the body shape**, then the shade, then the body outline
4. `neck(P)`: collar, scarf, a bag on the hip; not clipped
5. head; inside the head comes `hair(P)`, **clipped to the head shape**, then the shade, then the head outline in one unbroken line
6. `face_under(P, spec)`: blush, freckles
7. eyes, mouth
8. `face_over(P, spec)`: glasses, moustache, beard. `spec.get("m_tilt", 0)` tells you whether the moustache should lift (negative) or droop (positive)
9. eyebrows
10. `hat(P)`: hat, bow, anything that sits on top of the hair
11. expression symbol
12. `prop(P)`: the prop and the hand

Inside `prop` you decide the order of hand and object yourself: a held object (notebook, the handle of a magnifying glass, a grip) is drawn first and then `hand(x, y)`, so the hand is on top; an object that is swung or pointed outward (a stick, a torch) is drawn after the hand.

## Helpers in core.py

- `st(fill, sw, stroke, extra)`: the standard stroke attribute string. Outer outlines use `SW` (0.04), inner details use `SW_IN` (0.026).
- `hand(x, y, r=0.105)`: a round hand.
- `drop(x, y, s)`: a water drop.
- `head_center(P)`, `body_top(P)`, `face_points(P)`: get landmarks from these, do not recompute them.
- `character(P, expr, x, y, D, flip, prop, halo, silhouette)`: one SVG group placed at pixel (x, y).
- `check(P)`: the list of warnings for one declaration.

## Adding or changing expressions

The expression set belongs to the project. The shipped set is `neutral`, `happy`, `angry`, `sad`, `surprised`, `scared`, `suspicious`, `eureka`, `smug`, `oops`, `wink`, `smirk`.

To add one, add an entry to `EXPRESSIONS` and its name to `EXPRESSION_ORDER` in `core.py`; to drop one from the sheets, take it out of `EXPRESSION_ORDER`. The fields: `label` (the text under the cell), `eyes` (`dot`, `arc`, `closed`, `wide`), `eyes_far` (a different eye style for the far eye, used for a wink), `lid`, `open` (ignore the character's own drooping lid), `pupil`, `hl`, `brow_tilt` (near, far; positive tips the inner end down), `brow_dy` or `brow_dys`, `mouth`, `m_tilt`, `symbol` (`vein`, `tear`, `fear`, `rays`, `sparkle`, `sweat`). For a new symbol, add a branch to the `symbol` function.

## Drawing tips

- A shape that sits inside the head or the body can simply overflow the edge; the excess is clipped away.
- A detail smaller than 0.05 D disappears when the character is shrunk. Three small details close together turn into a tangle: remove one.
- The outline colour is the ink blue `INK`; a light detail on dark hair uses a tone slightly lighter than the hair, not white.
- Resize a character with `D` when you call `character`; do not multiply coordinates.
