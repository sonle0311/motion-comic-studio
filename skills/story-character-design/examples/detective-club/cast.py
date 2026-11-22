# -*- coding: utf-8 -*-
"""Example cast: a detective series. Each character declares only what is its own
(hair, outfit, prop); head, body, hands, eyes, mouth and expressions all call the
shared functions in core.py.

To render it, copy this file over drawkit/cast.py in a project and run
drawkit/export.py.
"""

from core import (INK, SW_IN, SKIN, st, hand, drop, head_center, face_points, body_top)

CHANNEL = {
    "name": "Detective Club",
    "tagline": "Case files · Can you crack it?",
    "background": "#141a2a",
    "accent": "#f6c343",
}

# ================= MR FINCH =================
GREY_HAIR = "#cfd3d8"


def finch_body(P, t):
    out = '<path d="M 0.10,%.3f L 0.10,0" %s/>' % (t + 0.2, st(sw=SW_IN))          # coat front line
    out += '<rect x="-0.7" y="-0.53" width="1.4" height="0.105" %s/>' % st("#7d6543", SW_IN)   # belt
    out += '<rect x="0.025" y="-0.555" width="0.15" height="0.155" rx="0.02" %s/>' % st("#d9b45a", SW_IN)
    for y in (-0.80, -0.67):
        out += '<circle cx="-0.07" cy="%.3f" r="0.028" %s/>' % (y, st("#5d4a30", 0.018))
    return out


def finch_scarf(P):
    t = body_top(P)
    red = "#9c3b2e"
    out = '<rect x="0.13" y="%.3f" width="0.19" height="0.40" rx="0.035" %s/>' % (t + 0.18, st(red))
    for x in (0.19, 0.255):
        out += '<path d="M %.3f,%.3f L %.3f,%.3f" %s/>' % (x, t + 0.50, x, t + 0.57, st(sw=0.02))
    out += '<rect x="-0.36" y="%.3f" width="0.78" height="0.20" rx="0.09" %s/>' % (t + 0.07, st(red))
    return out


def finch_hair(P):
    hx, hy = head_center(P)
    return '<path d="M %.3f,%.3f L %.3f,%.3f Q %.3f,%.3f %.3f,%.3f L %.3f,%.3f Z" %s/>' % (
        hx - 0.6, hy - 0.3, hx - 0.27, hy - 0.3, hx - 0.24, hy + 0.02, hx - 0.31, hy + 0.17,
        hx - 0.6, hy + 0.17, st(GREY_HAIR, SW_IN))


def finch_face_over(P, spec):
    hx, hy = head_center(P)
    f = face_points(P)
    (nx, ny), (fx, fy) = f["near"], f["far"]
    out = ""
    # round glasses
    out += '<path d="M %.3f,%.3f L %.3f,%.3f" %s/>' % (nx - 0.125, ny - 0.02, hx - 0.36, hy + 0.06, st(sw=0.03))
    out += '<path d="M %.3f,%.3f L %.3f,%.3f" %s/>' % (nx + 0.125, ny, fx - 0.10, fy, st(sw=0.03))
    out += '<circle cx="%.3f" cy="%.3f" r="0.125" %s/>' % (nx, ny, st("#ffffff", 0.03, extra='fill-opacity="0.16"'))
    out += '<ellipse cx="%.3f" cy="%.3f" rx="0.10" ry="0.125" %s/>' % (fx, fy, st("#ffffff", 0.03, extra='fill-opacity="0.16"'))
    # the moustache sits above the mouth; its tips lift or droop with the expression
    mx, my = f["mouth"]
    my -= 0.045
    k = spec.get("m_tilt", 0.0)
    out += ('<path d="M %.3f,%.3f C %.3f,%.3f %.3f,%.3f %.3f,%.3f C %.3f,%.3f %.3f,%.3f %.3f,%.3f '
            'C %.3f,%.3f %.3f,%.3f %.3f,%.3f C %.3f,%.3f %.3f,%.3f %.3f,%.3f Z" %s/>') % (
        mx, my - 0.035,
        mx - 0.06, my - 0.075, mx - 0.16, my - 0.03, mx - 0.20, my + 0.05 + k,
        mx - 0.12, my + 0.065, mx - 0.05, my + 0.055, mx, my + 0.015,
        mx + 0.05, my + 0.055, mx + 0.11, my + 0.065, mx + 0.175, my + 0.05 + k,
        mx + 0.14, my - 0.03, mx + 0.06, my - 0.075, mx, my - 0.035,
        st(GREY_HAIR, SW_IN))
    return out


def finch_cap(P):
    hx, hy = head_center(P)
    crown, brim = "#56606b", "#3f4852"
    out = '<path d="M %.3f,%.3f Q %.3f,%.3f %.3f,%.3f Q %.3f,%.3f %.3f,%.3f Q %.3f,%.3f %.3f,%.3f Z" %s/>' % (
        hx + 0.16, hy - 0.27, hx + 0.52, hy - 0.34, hx + 0.77, hy - 0.19,
        hx + 0.81, hy - 0.12, hx + 0.72, hy - 0.125, hx + 0.45, hy - 0.18, hx + 0.18, hy - 0.16, st(brim))
    out += ('<path d="M %.3f,%.3f C %.3f,%.3f %.3f,%.3f %.3f,%.3f C %.3f,%.3f %.3f,%.3f %.3f,%.3f '
            'L %.3f,%.3f Q %.3f,%.3f %.3f,%.3f Z" %s/>') % (
        hx - 0.54, hy - 0.19, hx - 0.58, hy - 0.56, hx - 0.30, hy - 0.75, hx + 0.05, hy - 0.73,
        hx + 0.36, hy - 0.72, hx + 0.54, hy - 0.58, hx + 0.55, hy - 0.28,
        hx + 0.55, hy - 0.21, hx, hy - 0.31, hx - 0.54, hy - 0.19, st(crown))
    out += '<path d="M %.3f,%.3f Q %.3f,%.3f %.3f,%.3f" %s/>' % (
        hx - 0.36, hy - 0.48, hx - 0.18, hy - 0.63, hx + 0.02, hy - 0.64, st(sw=0.028, stroke="#7b8691"))
    return out


def finch_prop(P):
    # leather notebook: the hand lies on top of it (holding it), so draw the notebook first, then the hand
    out = '<g transform="rotate(9 0.72 -0.86)">'
    out += '<rect x="0.56" y="-1.06" width="0.32" height="0.40" rx="0.03" %s/>' % st("#6b4a35")
    out += '<rect x="0.845" y="-1.04" width="0.035" height="0.36" %s/>' % st("#f4eedd", 0.018)
    out += '<path d="M 0.79,-1.06 L 0.79,-0.66" %s/>' % st(sw=0.03, stroke="#d9b45a")
    out += '</g>'
    return out + hand(0.60, -0.67)


FINCH = {
    "name": "Mr Finch", "slug": "finch",
    "role": "Famous detective (self-appointed)", "lineup_expr": "smug",
    "body_h": 1.20, "body_w": 0.50, "top_w": 0.30, "coat": "#b89a6a",
    "brow": "#8d939c", "brow_w": 0.046, "brow_dy": -0.035,
    "eye_rx": 0.05, "eye_ry": 0.078,          # eyes wide open, no drooping lid: confident, easy to read
    "mouth_default": "smile", "mouth_dy": 0.07,   # mouth shows below the moustache: he talks a lot
    "top": -0.74,
    "body_details": finch_body, "neck": finch_scarf, "hair": finch_hair,
    "face_over": finch_face_over, "hat": finch_cap, "prop": finch_prop,
}

# ================= PIP =================
HAIR = "#2a2433"


def pip_body(P, t):
    out = ""
    for col, w in ((INK, 0.105), ("#8a5530", 0.06)):     # cross-body satchel strap
        out += '<path d="M 0.30,%.3f L -0.46,-0.30" %s/>' % (t + 0.05, st(sw=w, stroke=col))
    out += '<path d="M 0.09,%.3f L 0.09,0" %s/>' % (t + 0.2, st(sw=SW_IN))
    for y in (-0.52, -0.33):
        out += '<circle cx="0.17" cy="%.3f" r="0.03" %s/>' % (y, st("#fdf6e3", 0.02))
    return out


def pip_neck(P):
    t = body_top(P)
    hx, _ = head_center(P)
    # leather satchel on the left hip
    out = '<rect x="-0.63" y="-0.44" width="0.32" height="0.27" rx="0.05" %s/>' % st("#9a5f35")
    out += '<path d="M -0.63,-0.335 L -0.31,-0.335" %s/>' % st(sw=SW_IN)
    out += '<circle cx="-0.47" cy="-0.30" r="0.025" %s/>' % st("#d9b45a", 0.018)
    # white collar
    for dx, rot in ((-0.14, -14), (0.18, 14)):
        out += '<ellipse cx="%.3f" cy="%.3f" rx="0.16" ry="0.075" transform="rotate(%d %.3f %.3f)" %s/>' % (
            hx + dx, t + 0.15, rot, hx + dx, t + 0.15, st("#ffffff", SW_IN))
    return out


def pip_back(P):
    hx, hy = head_center(P)
    out = ""
    for dx, rx, ry, rot in ((-0.60, 0.15, 0.24, 20), (0.57, 0.11, 0.20, -20)):
        out += '<ellipse cx="%.3f" cy="%.3f" rx="%.3f" ry="%.3f" transform="rotate(%d %.3f %.3f)" %s/>' % (
            hx + dx, hy + 0.20, rx, ry, rot, hx + dx, hy + 0.20, st(HAIR))
    return out


def pip_hair(P):
    hx, hy = head_center(P)
    pts = [(-0.6, -0.6), (0.6, -0.6), (0.6, 0.02), (0.47, 0.02)]
    d = "M " + " L ".join("%.3f,%.3f" % (hx + x, hy + y) for x, y in pts)
    d += " Q %.3f,%.3f %.3f,%.3f" % (hx + 0.44, hy - 0.10, hx + 0.40, hy - 0.13)
    d += " Q %.3f,%.3f %.3f,%.3f" % (hx + 0.28, hy - 0.17, hx + 0.17, hy - 0.17)
    d += " L %.3f,%.3f L %.3f,%.3f" % (hx + 0.13, hy - 0.10, hx + 0.09, hy - 0.17)
    d += " Q %.3f,%.3f %.3f,%.3f" % (hx - 0.12, hy - 0.18, hx - 0.30, hy - 0.13)
    d += " L %.3f,%.3f Q %.3f,%.3f %.3f,%.3f Z" % (hx - 0.30, hy + 0.14, hx - 0.40, hy + 0.22, hx - 0.6, hy + 0.16)
    out = '<path d="%s" %s/>' % (d, st(HAIR, SW_IN))
    out += '<path d="M %.3f,%.3f Q %.3f,%.3f %.3f,%.3f" %s/>' % (
        hx - 0.24, hy - 0.33, hx - 0.06, hy - 0.40, hx + 0.12, hy - 0.34, st(sw=0.03, stroke="#5f5470"))
    return out


def pip_bobbles(P):
    hx, hy = head_center(P)
    out = ""
    for dx in (-0.51, 0.51):
        out += '<circle cx="%.3f" cy="%.3f" r="0.065" %s/>' % (hx + dx, hy + 0.01, st("#e0483e", SW_IN))
    return out


def pip_blush(P, spec):
    f = face_points(P)
    out = ""
    for (x, y), dx in ((f["near"], -0.10), (f["far"], 0.09)):
        out += '<ellipse cx="%.3f" cy="%.3f" rx="0.06" ry="0.034" fill="#f08f80" opacity="0.5"/>' % (x + dx, y + 0.16)
    return out


def pip_prop(P):
    # magnifying glass: the hand grips the handle, so draw the glass first, then the hand
    out = ""
    for col, w in ((INK, 0.11), ("#8a5530", 0.06)):
        out += '<path d="M 0.585,-0.52 L 0.50,-0.38" %s/>' % st(sw=w, stroke=col)
    out += '<circle cx="0.68" cy="-0.69" r="0.18" %s/>' % st("#bfe3f5", 0.05, extra='fill-opacity="0.5"')
    out += '<path d="M 0.58,-0.74 Q 0.60,-0.81 0.67,-0.80" %s/>' % st(sw=0.026, stroke="#ffffff")
    return out + hand(0.49, -0.37, 0.10)


PIP = {
    "name": "Pip", "slug": "pip",
    "role": "The one who really solves it", "lineup_expr": "wink",
    "body_h": 0.92, "body_w": 0.44, "top_w": 0.27, "coat": "#f2c230",
    "brow": HAIR, "brow_w": 0.03,
    "eye_rx": 0.055, "eye_ry": 0.09, "hl": 0.024,
    "mouth_default": "smile",
    "top": -0.46, "shoe": "#b8402f",
    "body_details": pip_body, "neck": pip_neck, "back": pip_back, "hair": pip_hair,
    "hat": pip_bobbles, "face_under": pip_blush, "prop": pip_prop,
}

# =====================================================================
# SUPPORTING CAST · CASE #001 "The Dry Visitor"
# Fewer details and quieter colours than the two leads. A detail marked CLUE is
# what the viewer uses to solve the case: never drop it, never tidy it away.
# =====================================================================
OIL = "#2b2b2b"
WATER = "#8fd0f0"


def _hair_path(P, pts, color):
    """Hair clipped to the head shape. pts: path commands with coordinates relative to the head centre."""
    hx, hy = head_center(P)
    d = ""
    for cmd, nums in pts:
        d += cmd + " " + " ".join("%.3f,%.3f" % (hx + nums[i], hy + nums[i + 1]) for i in range(0, len(nums), 2)) + " "
    return '<path d="%sZ" %s/>' % (d, st(color, SW_IN))


# ---------- MR BELL: watch shop owner ----------
def bell_body(P, t):
    out = '<rect x="-0.36" y="%.3f" width="0.82" height="1.2" rx="0.05" %s/>' % (t + 0.34, st("#7a5a3c", SW_IN))  # apron
    for x in (-0.24, 0.34):
        out += '<path d="M %.3f,%.3f L %.3f,%.3f" %s/>' % (x, t + 0.34, x * 0.6 + 0.03, t, st(sw=0.05, stroke="#7a5a3c"))
    out += '<rect x="-0.06" y="-0.44" width="0.30" height="0.20" rx="0.03" %s/>' % st("none", SW_IN)
    return out


def bell_hair(P):
    white = "#e4e6e8"
    out = _hair_path(P, [("M", (-0.6, -0.06)), ("Q", (-0.30, -0.10, -0.31, 0.06)), ("Q", (-0.32, 0.20, -0.6, 0.20))], white)
    out += _hair_path(P, [("M", (0.6, -0.04)), ("Q", (0.43, -0.06, 0.44, 0.05)), ("Q", (0.45, 0.16, 0.6, 0.16))], white)
    return out


def bell_loupe(P):
    """Watchmaker's loupe pushed up on the forehead."""
    hx, hy = head_center(P)
    out = '<path d="M %.3f,%.3f Q %.3f,%.3f %.3f,%.3f" %s/>' % (
        hx - 0.47, hy - 0.22, hx, hy - 0.33, hx + 0.47, hy - 0.24, st(sw=0.04, stroke="#5a3d28"))
    out += '<rect x="%.3f" y="%.3f" width="0.22" height="0.24" rx="0.04" %s/>' % (hx + 0.10, hy - 0.62, st("#3f4852"))
    out += '<ellipse cx="%.3f" cy="%.3f" rx="0.04" ry="0.085" %s/>' % (hx + 0.29, hy - 0.50, st("#bfe3f5", 0.02))
    return out


def bell_prop(P):
    out = ""
    for col, w in ((INK, 0.062), ("#b9c0c8", 0.026)):
        out += '<path d="M 0.615,-0.62 L 0.665,-0.98" %s/>' % st(sw=w, stroke=col)      # screwdriver shaft
    for col, w in ((INK, 0.125), ("#c8553d", 0.08)):
        out += '<path d="M 0.585,-0.44 L 0.612,-0.62" %s/>' % st(sw=w, stroke=col)      # handle
    return out + hand(0.59, -0.50)


BELL = {
    "name": "Mr Bell", "slug": "bell", "role": "Watch shop owner", "episode": "001",
    "body_h": 1.05, "body_w": 0.50, "top_w": 0.30, "coat": "#8fa3a0",
    "brow": "#b9bec4", "brow_w": 0.05, "lid": 0.15, "mouth_default": "smile",
    "top": -0.62, "lineup_expr": "sad",
    "body_details": bell_body, "hair": bell_hair, "hat": bell_loupe, "prop": bell_prop,
}


# ---------- TOM: shop assistant ----------
TOM_HAIR = "#30262a"


def tom_body(P, t):
    out = '<path d="M 0.10,%.3f L 0.10,0" %s/>' % (t + 0.2, st(sw=SW_IN))
    out += '<rect x="-0.33" y="-0.70" width="0.20" height="0.17" rx="0.02" %s/>' % st("none", SW_IN)
    for x, y, rx, ry in ((0.27, -0.44, 0.07, 0.045), (-0.08, -0.22, 0.05, 0.035)):     # oil stains on the coat
        out += '<ellipse cx="%.3f" cy="%.3f" rx="%.3f" ry="%.3f" fill="%s" opacity="0.55"/>' % (x, y, rx, ry, OIL)
    return out


def tom_back(P):
    """Spiky hair: it sticks out past the head, so it is drawn behind the head, not inside hair."""
    hx, hy = head_center(P)
    pts = [(-0.30, -0.30), (-0.24, -0.60), (-0.10, -0.44), (-0.02, -0.66), (0.10, -0.45),
           (0.20, -0.63), (0.30, -0.43), (0.40, -0.54), (0.42, -0.30)]
    return '<path d="M %s Z" %s/>' % (" L ".join("%.3f,%.3f" % (hx + x, hy + y) for x, y in pts), st(TOM_HAIR))


def tom_hair(P):
    return _hair_path(P, [("M", (-0.6, -0.6)), ("L", (0.6, -0.6, 0.6, -0.14)), ("Q", (0.22, -0.28, -0.10, -0.21)),
                          ("L", (-0.30, -0.08, -0.30, 0.10, -0.6, 0.10))], TOM_HAIR)


def tom_face(P, spec):
    nx, ny = face_points(P)["near"]
    return '<ellipse cx="%.3f" cy="%.3f" rx="0.06" ry="0.03" transform="rotate(-18 %.3f %.3f)" fill="%s" opacity="0.5"/>' % (
        nx - 0.11, ny + 0.17, nx - 0.11, ny + 0.17, OIL)          # oil smear on the cheek


def tom_prop(P):
    # rag first; hand on top; the CLUE (oil on the hand) drawn last so nothing covers it
    out = ('<path d="M 0.47,-0.60 L 0.69,-0.62 L 0.74,-0.24 L 0.66,-0.32 L 0.60,-0.20 L 0.54,-0.32 '
           'L 0.46,-0.24 Z" %s/>') % st("#e9e2cf")
    out += '<ellipse cx="0.62" cy="-0.36" rx="0.05" ry="0.03" fill="%s" opacity="0.6"/>' % OIL
    out += hand(0.58, -0.60)
    for x, y, rx, ry, rot in ((0.55, -0.635, 0.040, 0.018, -30), (0.615, -0.575, 0.030, 0.014, 20)):
        out += '<ellipse cx="%.3f" cy="%.3f" rx="%.3f" ry="%.3f" transform="rotate(%d %.3f %.3f)" fill="%s"/>' % (
            x, y, rx, ry, rot, x, y, OIL)
    return out


TOM = {
    "name": "Tom", "slug": "tom", "role": "Shop assistant", "episode": "001",
    "body_h": 1.12, "body_w": 0.45, "top_w": 0.28, "coat": "#6f8296",
    "brow": TOM_HAIR, "mouth_default": "flat",
    "top": -0.66, "lineup_expr": "scared",
    "body_details": tom_body, "back": tom_back, "hair": tom_hair, "face_under": tom_face, "prop": tom_prop,
}


# ---------- MRS LANE: regular customer ----------
LANE_HAIR = "#6d5f5a"


def lane_body(P, t):
    out = '<path d="M 0.10,%.3f L 0.10,0" %s/>' % (t + 0.2, st(sw=SW_IN))
    for y in (-0.72, -0.56, -0.40):
        out += '<circle cx="0.10" cy="%.3f" r="0.026" %s/>' % (y, st("#e9e2cf", 0.018))
    # CLUE: the hem is wet and dark
    out += ('<path d="M -0.7,-0.21 q 0.1,-0.06 0.2,0 t 0.2,0 t 0.2,0 t 0.2,0 t 0.2,0 t 0.2,0 t 0.2,0 '
            'L 0.7,0.1 L -0.7,0.1 Z" fill="%s" opacity="0.30"/>') % INK
    return out


def lane_neck(P):
    t = body_top(P)
    hx, _ = head_center(P)
    out = ""
    for i in range(6):                       # pearl necklace
        x = hx - 0.20 + i * 0.09
        y = t + 0.15 + 0.045 * (1 - abs(i - 2.5) / 2.5)
        out += '<circle cx="%.3f" cy="%.3f" r="0.032" %s/>' % (x, y, st("#ffffff", 0.018))
    return out


def lane_back(P):
    """Hair bun: it sticks out past the head, so it is drawn behind the head."""
    hx, hy = head_center(P)
    return '<circle cx="%.3f" cy="%.3f" r="0.19" %s/>' % (hx - 0.08, hy - 0.50, st(LANE_HAIR))


def lane_hair(P):
    return _hair_path(P, [("M", (-0.6, -0.6)), ("L", (0.6, -0.6, 0.6, 0.02)), ("Q", (0.46, -0.20, 0.20, -0.25)),
                          ("L", (0.12, -0.34)), ("Q", (0.0, -0.20, -0.30, -0.10)),
                          ("L", (-0.30, 0.14, -0.6, 0.14))], LANE_HAIR)


def lane_face(P, spec):
    hx, hy = head_center(P)
    return '<circle cx="%.3f" cy="%.3f" r="0.04" %s/>' % (hx - 0.40, hy + 0.24, st("#5fa27a", 0.02))   # jade earring


def lane_prop(P):
    # CLUE: the umbrella is still dripping, a puddle on the floor
    out = '<ellipse cx="0.72" cy="0.02" rx="0.24" ry="0.055" %s/>' % st(WATER, 0.018, extra='fill-opacity="0.85"')
    for col, w in ((INK, 0.075), ("#8a5530", 0.035)):
        out += '<path d="M 0.63,-0.60 L 0.63,-0.80 Q 0.63,-0.89 0.55,-0.89" %s/>' % st(sw=w, stroke=col)
    out += '<path d="M 0.56,-0.62 L 0.70,-0.62 L 0.745,-0.12 L 0.72,-0.02 L 0.675,-0.12 Z" %s/>' % st("#3f6f8f")
    out += '<path d="M 0.63,-0.60 L 0.705,-0.10" %s/>' % st(sw=0.02)
    out += hand(0.63, -0.66)
    out += drop(0.80, -0.30, 0.036) + drop(0.60, -0.19, 0.03) + drop(0.83, -0.10, 0.028)
    return out


LANE = {
    "name": "Mrs Lane", "slug": "lane", "role": "Regular customer", "episode": "001",
    "body_h": 1.00, "body_w": 0.54, "top_w": 0.31, "coat": "#a58aa8",
    "brow": LANE_HAIR, "lid": 0.1, "mouth_default": "smile",
    "top": -0.69, "lineup_expr": "angry", "shoe": "#4a3b4c",
    "body_details": lane_body, "neck": lane_neck, "back": lane_back, "hair": lane_hair,
    "face_over": lane_face, "prop": lane_prop,
}


# ---------- MR NASH: customer collecting a repair ----------
NASH_HAIR = "#3a2e2a"


def nash_body(P, t):
    # CLUE: the coat is smooth and dry. Draw no drops, no dark patches, no creases.
    out = '<path d="M -0.14,%.3f L 0.34,%.3f L 0.10,%.3f Z" %s/>' % (t - 0.02, t - 0.02, t + 0.50, st("#f4f1ea", SW_IN))
    out += '<path d="M 0.10,%.3f L 0.10,0" %s/>' % (t + 0.50, st(sw=SW_IN))
    for y in (-0.50, -0.36):
        out += '<circle cx="0.17" cy="%.3f" r="0.026" %s/>' % (y, st("#5d564a", 0.018))
    out += '<path d="M -0.36,-0.34 L -0.14,-0.34" %s/>' % st(sw=SW_IN)
    return out


def nash_hair(P):
    hx, hy = head_center(P)
    out = _hair_path(P, [("M", (-0.6, -0.6)), ("L", (0.6, -0.6, 0.6, -0.08)), ("Q", (0.46, -0.22, 0.30, -0.25)),
                         ("Q", (0.02, -0.31, -0.14, -0.15)), ("L", (-0.30, -0.10, -0.30, 0.12, -0.6, 0.12))], NASH_HAIR)
    out += '<path d="M %.3f,%.3f Q %.3f,%.3f %.3f,%.3f" %s/>' % (
        hx - 0.18, hy - 0.33, hx + 0.02, hy - 0.41, hx + 0.22, hy - 0.35, st(sw=0.028, stroke="#6a5a52"))
    return out


def nash_prop(P):
    # collection ticket: the hand holds the bottom corner
    out = '<g transform="rotate(10 0.68 -0.76)">'
    out += '<rect x="0.56" y="-0.92" width="0.24" height="0.30" rx="0.015" %s/>' % st("#f4eedd")
    for y in (-0.84, -0.78, -0.72):
        out += '<path d="M 0.60,%.3f L 0.76,%.3f" %s/>' % (y, y, st(sw=0.016))
    out += '</g>'
    return out + hand(0.58, -0.60)


NASH = {
    "name": "Mr Nash", "slug": "nash", "role": "Collecting a repair", "episode": "001",
    "body_h": 1.15, "body_w": 0.47, "top_w": 0.30, "coat": "#8c8577",
    "brow": NASH_HAIR, "brow_w": 0.036, "lid": 0.18, "mouth_default": "flat",
    "top": -0.46, "lineup_expr": "neutral", "shoe": "#6b4226",   # CLUE: dry leather shoes
    "body_details": nash_body, "hair": nash_hair, "prop": nash_prop,
}

EPISODE_001 = [BELL, TOM, LANE, NASH]
CAST = [PIP, FINCH] + EPISODE_001
