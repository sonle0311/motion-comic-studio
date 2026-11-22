# Stage files

All files sit in the project folder next to `index.html`.

## project.json

| Key | Default | Meaning |
|---|---|---|
| `title` | | title card text, also on the end card |
| `size` | `[1080, 1920]` | frame size |
| `titleAt` | none | `[start, end]` seconds for the title card, usually the pause after the hook lines |
| `endCard` | `[]` | lines under the title at the end, e.g. channel name and a fiction notice |
| `font`, `titleFont` | system sans, Georgia | CSS font families; put `@font-face` rules in `fonts.css` to bundle fonts |
| `titleColor`, `subColor` | red, off-white | |
| `boil` | 0.9 | frame jitter strength; 0 turns it off |
| `crossfade` | 0.45 | seconds of fade between shots |
| `lead` | 0.35 | seconds a shot starts before its line |
| `start`, `tail` | 0.3, 7 | used by `timeline.py`: first line start, seconds after the last line |

## shots.json

A list in film order. Each shot starts `lead` seconds before the line it names and lasts until the next shot.

| Key | Meaning |
|---|---|
| `img` | image name without extension (`img/hi/<name>.jpg` must exist) |
| `line` | line id the shot starts on |
| `dt` | shift the start, seconds |
| `kb` | camera `[x0, y0, zoom0, x1, y1, zoom1]`: centre as a fraction of the image, zoom 1 fills the frame. Keep zoom at or below about 1.7 unless the still is larger than 1K |
| `alt` | pose swap, see below |
| `cut` | 1 = hard cut in, no crossfade |
| `shakeAt` | line id: shake the frame for 0.6 s when that line starts |
| `rain`, `mist`, `dust`, `flick` | effect strength, 1 is normal |
| `smoke` | `[[x, y], ...]` points on the image (fractions) where thin smoke rises |
| `sepia` | 1 = flashback tint |
| `dark` | brightness 0 to 1, for reusing a day image as night |
| `boil` | per-shot multiplier of the jitter |

`alt`:

| Form | Effect |
|---|---|
| `{"img": "s02b", "mode": "loop", "period": 2.6}` | fades to the variant and back every `period` seconds: talking, arguing, pounding |
| `{"img": "s29b", "at": "049", "dt": 0, "fade": 2.5}` | fades to the variant when line `049` starts: a change the narration names |
| `{"img": "s18b", "frac": 0.45, "fade": 0.6}` | fades once, partway through the shot |

Reuse: the same image can appear in several shots with different `kb` (a wide view, then a slow push on a detail). A shot whose base is the variant and whose `alt` is the original gives the reverse movement.

## sfx.json

`[{"file": "sfx/knock.wav", "at": "015", "dt": 2.3, "db": -6}]`: `at` is a line id or seconds.

## Rendering

- `render.mjs <project> --stills 1,2,3` writes `out/stills/t_<t>.jpg`.
- `--workers N` splits the film across N browsers. Two is safe; more is faster on a strong machine.
- `--from` and `--to` render part of the film for a quick look.
- The page is deterministic: the same `t` always gives the same frame.
