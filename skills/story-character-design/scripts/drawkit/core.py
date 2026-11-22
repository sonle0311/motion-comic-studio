# -*- coding: utf-8 -*-
"""2D character drawing machine in code (Python generating SVG).

Every coordinate is in units of D (D = the width of the head). The origin (0, 0)
is the point between the two feet on the ground, and the y axis points down
(negative y is up). Characters face 3/4 to the right by default. The measurements
live in DRAWING-RULES.md; change one here and change it there too.
"""

INK = "#1b2233"      # outline: ink blue, never pure black
SW = 0.04            # outer outline width
SW_IN = 0.026        # inner detail line width
SKIN = "#f3d2b0"
MOUTH = "#7a2a2a"
SHADE_OPACITY = 0.14

FACE_SHIFT = 0.10    # face sits right of the head centre (3/4 view)
HEAD_W, HEAD_H, HEAD_R = 1.0, 0.92, 0.42
CHIN_OVERLAP = 0.09  # chin overlaps the body; there is no neck
FOOT_Y = 0.05        # body floats above the ground by the height of the shoe tips

_uid = [0]


def uid(prefix):
    _uid[0] += 1
    return "%s%d" % (prefix, _uid[0])


def st(fill="none", sw=SW, stroke=INK, extra=""):
    return ('fill="%s" stroke="%s" stroke-width="%.3f" stroke-linejoin="round" '
            'stroke-linecap="round" %s' % (fill, stroke, sw, extra))


def body_top(P):
    return -(FOOT_Y + P["body_h"])


def head_center(P):
    return 0.03, body_top(P) + CHIN_OVERLAP - HEAD_H / 2.0


def face_points(P):
    """Landmarks on the face: near eye, far eye, mouth."""
    hx, hy = head_center(P)
    ey = hy + 0.06
    return {
        "near": (hx + FACE_SHIFT - 0.19, ey),
        "far": (hx + FACE_SHIFT + 0.17, ey),
        "mouth": (hx + FACE_SHIFT + 0.04, hy + 0.27),
    }


# ---------- shared parts ----------

def body_path(P):
    t, bh, bw, tw = body_top(P), P["body_h"], P["body_w"], P["top_w"]
    b = -FOOT_Y
    return ("M %.3f,%.3f L %.3f,%.3f C %.3f,%.3f %.3f,%.3f %.3f,%.3f "
            "Q %.3f,%.3f %.3f,%.3f L %.3f,%.3f Q %.3f,%.3f %.3f,%.3f "
            "C %.3f,%.3f %.3f,%.3f %.3f,%.3f Z") % (
        -tw, t, tw, t,
        tw + 0.12, t, bw - 0.04, t + bh * 0.55, bw, b - 0.17,
        bw + 0.02, b, bw - 0.13, b,
        -(bw - 0.13), b, -(bw + 0.02), b, -bw, b - 0.17,
        -(bw - 0.04), t + bh * 0.55, -(tw + 0.12), t, -tw, t)


def head_rect(P, attrs):
    hx, hy = head_center(P)
    return '<rect x="%.3f" y="%.3f" width="%.3f" height="%.3f" rx="%.3f" %s/>' % (
        hx - HEAD_W / 2, hy - HEAD_H / 2, HEAD_W, HEAD_H, HEAD_R, attrs)


def ground_shadow(P):
    return '<ellipse cx="0.02" cy="0.02" rx="%.3f" ry="0.07" fill="%s" opacity="0.18"/>' % (
        P["body_w"] + 0.12, INK)


def shoes(P):
    c = P.get("shoe", "#2d3142")
    out = ""
    for x in (-0.19, 0.23):
        out += '<ellipse cx="%.3f" cy="-0.04" rx="0.17" ry="0.075" %s/>' % (x, st(c))
    return out


def body(P):
    cid = uid("b")
    path = body_path(P)
    t = body_top(P)
    out = '<clipPath id="%s"><path d="%s"/></clipPath>' % (cid, path)
    out += '<path d="%s" %s/>' % (path, st(P["coat"]))
    out += '<g clip-path="url(#%s)">' % cid
    out += P["body_details"](P, t)
    # one-tone shade on the back side (the left)
    out += '<rect x="-0.8" y="%.3f" width="%.3f" height="%.3f" fill="%s" opacity="%.2f"/>' % (
        t, 0.8 - P["body_w"] * 0.52, P["body_h"], INK, SHADE_OPACITY)
    out += '</g>'
    out += '<path d="%s" %s/>' % (path, st())
    return out


def hand(x, y, r=0.105):
    return '<circle cx="%.3f" cy="%.3f" r="%.3f" %s/>' % (x, y, r, st(SKIN))


def drop(x, y, s, fill="#8fd0f0"):
    return ('<path d="M %.3f,%.3f C %.3f,%.3f %.3f,%.3f %.3f,%.3f '
            'C %.3f,%.3f %.3f,%.3f %.3f,%.3f Z" %s/>') % (
        x, y - s, x + s * 0.95, y + s * 0.1, x + s * 0.6, y + s, x, y + s,
        x - s * 0.6, y + s, x - s * 0.95, y + s * 0.1, x, y - s, st(fill, 0.022))


# ---------- face ----------

EXPRESSIONS = {
    "neutral":    {"label": "Neutral", "eyes": "dot"},
    "happy":      {"label": "Happy", "eyes": "arc", "brow_dy": -0.02, "mouth": "open", "m_tilt": -0.03},
    "angry":      {"label": "Angry", "eyes": "dot", "brow_tilt": (0.055, 0.055), "brow_dy": 0.03,
                   "mouth": "frown", "m_tilt": 0.03, "symbol": "vein"},
    "sad":        {"label": "Sad", "eyes": "dot", "lid": 0.3, "brow_tilt": (-0.05, -0.05),
                   "mouth": "frown", "m_tilt": 0.04, "symbol": "tear"},
    "surprised":  {"label": "Surprised", "eyes": "wide", "pupil": 0.032, "brow_dy": -0.06, "mouth": "o"},
    "scared":     {"label": "Scared", "eyes": "wide", "pupil": 0.018, "brow_tilt": (-0.05, -0.05),
                   "brow_dy": -0.04, "mouth": "wavy", "symbol": "fear"},
    # two expressions for a detective story; swap them for what your genre needs
    "suspicious": {"label": "Suspicious", "eyes": "dot", "lid": 0.45, "brow_tilt": (0.035, -0.02),
                   "brow_dys": (0.02, -0.055), "mouth": "flat"},
    "eureka":     {"label": "Eureka!", "eyes": "dot", "hl": 0.026, "open": True, "brow_dy": -0.05, "mouth": "open",
                   "m_tilt": -0.03, "symbol": "rays"},
    # four expressions for a "takes the credit" and "really did the work" pair
    "smug":       {"label": "Smug", "eyes": "closed", "brow_tilt": (0.04, 0.04), "brow_dy": -0.035,
                   "mouth": "grin", "m_tilt": -0.045, "symbol": "sparkle"},
    "oops":       {"label": "Oops", "eyes": "wide", "pupil": 0.02, "brow_tilt": (-0.03, 0.02),
                   "brow_dys": (-0.05, -0.01), "mouth": "grit", "m_tilt": 0.02, "symbol": "sweat"},
    "wink":       {"label": "Wink", "eyes": "dot", "eyes_far": "arc", "open": True,
                   "brow_dys": (-0.03, 0.02), "mouth": "smile", "m_tilt": -0.02},
    "smirk":      {"label": "Smirk", "eyes": "dot", "lid": 0.38, "brow_tilt": (0.0, -0.02),
                   "brow_dys": (0.0, -0.04), "mouth": "smirk", "m_tilt": -0.02},
}
# The order of the cells on the expression sheet. Each project may add, drop or reorder.
EXPRESSION_ORDER = ["neutral", "happy", "angry", "sad", "surprised", "scared", "suspicious", "eureka",
                    "smug", "oops", "wink", "smirk"]


def eye(x, y, spec, P, far=False):
    rx = P.get("eye_rx", 0.05) * (0.88 if far else 1.0)
    ry = P.get("eye_ry", 0.08)
    kind = spec["eyes"]
    if kind == "arc":
        return '<path d="M %.3f,%.3f Q %.3f,%.3f %.3f,%.3f" %s/>' % (
            x - rx * 1.4, y + 0.025, x, y - ry * 1.0, x + rx * 1.4, y + 0.025, st(sw=0.036))
    if kind == "closed":      # closed eye curving down: smug, content
        return '<path d="M %.3f,%.3f Q %.3f,%.3f %.3f,%.3f" %s/>' % (
            x - rx * 1.4, y - 0.015, x, y + ry * 0.85, x + rx * 1.4, y - 0.015, st(sw=0.036))
    if kind == "wide":
        r = ry * 1.05 * (0.92 if far else 1.0)
        return ('<circle cx="%.3f" cy="%.3f" r="%.3f" %s/>'
                '<circle cx="%.3f" cy="%.3f" r="%.3f" fill="%s"/>') % (
            x, y, r, st("#ffffff", SW_IN), x + 0.012, y, spec.get("pupil", 0.03), INK)
    lid = 0.0 if spec.get("open") else max(spec.get("lid", 0.0), P.get("lid", 0.0))
    out = ""
    clip = ""
    if lid > 0:
        cid = uid("e")
        cut = y - ry + 2 * ry * lid
        out += '<clipPath id="%s"><rect x="%.3f" y="%.3f" width="%.3f" height="%.3f"/></clipPath>' % (
            cid, x - rx - 0.02, cut, 2 * rx + 0.04, 2 * ry)
        clip = 'clip-path="url(#%s)"' % cid
    out += '<g %s><ellipse cx="%.3f" cy="%.3f" rx="%.3f" ry="%.3f" fill="%s"/>' % (clip, x, y, rx, ry, INK)
    out += '<circle cx="%.3f" cy="%.3f" r="%.3f" fill="#ffffff"/></g>' % (
        x + rx * 0.35, y - ry * 0.25, spec.get("hl", P.get("hl", 0.018)))
    if lid > 0:
        cut = y - ry + 2 * ry * lid
        out += '<path d="M %.3f,%.3f L %.3f,%.3f" %s/>' % (
            x - rx * 1.35, cut, x + rx * 1.35, cut, st(sw=0.03))
    return out


def brows(P, spec):
    f = face_points(P)
    ry = P.get("eye_ry", 0.08)
    tn, tf = spec.get("brow_tilt", (0.0, 0.0))
    dn, df = spec.get("brow_dys", (spec.get("brow_dy", 0.0),) * 2)
    base = -ry - 0.055 + P.get("brow_dy", 0.0)
    L = 0.085
    w = P.get("brow_w", 0.032)
    (nx, ny), (fx, fy) = f["near"], f["far"]
    out = '<path d="M %.3f,%.3f L %.3f,%.3f" %s/>' % (
        nx - L, ny + base + dn - tn, nx + L, ny + base + dn + tn, st(sw=w, stroke=P["brow"]))
    out += '<path d="M %.3f,%.3f L %.3f,%.3f" %s/>' % (
        fx - L * 0.88, fy + base + df + tf, fx + L * 0.88, fy + base + df - tf, st(sw=w, stroke=P["brow"]))
    return out


def mouth(P, spec):
    kind = spec.get("mouth", P.get("mouth_default"))
    if kind is None:
        return ""
    if P.get("mouth_hidden") and kind not in ("o", "wavy"):
        return ""   # a moustache hides the mouth: it shows only at a climax
    mx, my = face_points(P)["mouth"]
    my += P.get("mouth_dy", 0.0)
    if kind == "smile":
        return '<path d="M %.3f,%.3f Q %.3f,%.3f %.3f,%.3f" %s/>' % (
            mx - 0.06, my, mx, my + 0.065, mx + 0.06, my, st(sw=0.03))
    if kind == "open":
        return '<path d="M %.3f,%.3f Q %.3f,%.3f %.3f,%.3f Z" %s/>' % (
            mx - 0.075, my - 0.01, mx, my + 0.15, mx + 0.075, my - 0.01, st(MOUTH, SW_IN))
    if kind == "o":
        return '<ellipse cx="%.3f" cy="%.3f" rx="0.034" ry="0.044" %s/>' % (mx, my + 0.01, st(MOUTH, SW_IN))
    if kind == "grin":        # toothy grin
        return '<path d="M %.3f,%.3f Q %.3f,%.3f %.3f,%.3f Z" %s/>' % (
            mx - 0.10, my - 0.015, mx, my + 0.17, mx + 0.10, my - 0.015, st("#ffffff", SW_IN))
    if kind == "grit":        # forced smile, gritted teeth
        return ('<rect x="%.3f" y="%.3f" width="0.17" height="0.07" rx="0.022" %s/>'
                '<path d="M %.3f,%.3f L %.3f,%.3f M %.3f,%.3f L %.3f,%.3f" %s/>') % (
            mx - 0.085, my - 0.02, st("#ffffff", SW_IN),
            mx - 0.028, my - 0.02, mx - 0.028, my + 0.05, mx + 0.028, my - 0.02, mx + 0.028, my + 0.05, st(sw=0.018))
    if kind == "smirk":       # one corner of the mouth lifted
        return '<path d="M %.3f,%.3f Q %.3f,%.3f %.3f,%.3f" %s/>' % (
            mx - 0.06, my + 0.02, mx + 0.01, my + 0.055, mx + 0.075, my - 0.03, st(sw=0.03))
    if kind == "flat":
        return '<path d="M %.3f,%.3f L %.3f,%.3f" %s/>' % (mx - 0.055, my + 0.01, mx + 0.055, my + 0.01, st(sw=0.03))
    if kind == "frown":
        return '<path d="M %.3f,%.3f Q %.3f,%.3f %.3f,%.3f" %s/>' % (
            mx - 0.055, my + 0.035, mx, my - 0.03, mx + 0.055, my + 0.035, st(sw=0.03))
    if kind == "wavy":
        return '<path d="M %.3f,%.3f q 0.027,-0.045 0.053,0 t 0.053,0 t 0.053,0" %s/>' % (
            mx - 0.08, my + 0.01, st(sw=0.028))
    return ""


def symbol(P, spec):
    kind = spec.get("symbol")
    if not kind:
        return ""
    hx, hy = head_center(P)
    top = hy + P["top"]
    f = face_points(P)
    if kind == "vein":
        x, y, a = hx - 0.60, top + 0.16, 0.05
        red = "#d8342b"
        out = ""
        for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            out += '<path d="M %.3f,%.3f Q %.3f,%.3f %.3f,%.3f" %s/>' % (
                x + sx * 0.02, y + sy * (a + 0.02), x + sx * 0.02, y + sy * 0.02,
                x + sx * (a + 0.02), y + sy * 0.02, st(sw=0.036, stroke=red))
        return out
    if kind == "tear":
        nx, ny = f["near"]
        return drop(nx - 0.03, ny + 0.17, 0.05)
    if kind == "fear":
        out = ""
        for i, ln in enumerate((0.20, 0.26, 0.17)):
            x = hx + 0.26 + i * 0.11
            out += '<path d="M %.3f,%.3f L %.3f,%.3f" %s/>' % (
                x, top - 0.08 - ln, x, top - 0.08, st(sw=0.032, stroke="#6b4fa0"))
        return out + drop(hx - 0.40, hy + 0.02, 0.055)
    if kind == "rays":
        cx, cy = hx + 0.50, top + 0.06
        out = ""
        for dx, dy in ((0.05, -0.20), (0.17, -0.13), (0.22, 0.0)):
            for col, w in ((INK, 0.075), ("#f6c343", 0.04)):
                out += '<path d="M %.3f,%.3f L %.3f,%.3f" %s/>' % (
                    cx + dx * 0.45, cy + dy * 0.45, cx + dx * 1.25, cy + dy * 1.25, st(sw=w, stroke=col))
        return out
    if kind == "sparkle":
        out = ""
        for x, y, r in ((hx + 0.58, top + 0.08, 0.10), (hx + 0.72, top + 0.24, 0.055)):
            out += ('<path d="M %.3f,%.3f Q %.3f,%.3f %.3f,%.3f Q %.3f,%.3f %.3f,%.3f '
                    'Q %.3f,%.3f %.3f,%.3f Q %.3f,%.3f %.3f,%.3f Z" %s/>') % (
                x, y - r, x, y, x + r, y, x, y, x, y + r, x, y, x - r, y, x, y, x, y - r, st("#f6c343", 0.022))
        return out
    if kind == "sweat":
        return drop(hx - 0.60, hy - 0.14, 0.075)
    return ""


def face(P, spec):
    f = face_points(P)
    out = P.get("face_under", lambda P, s: "")(P, spec)
    out += eye(f["near"][0], f["near"][1], spec, P)
    far_spec = dict(spec, eyes=spec["eyes_far"]) if "eyes_far" in spec else spec
    out += eye(f["far"][0], f["far"][1], far_spec, P, far=True)
    out += mouth(P, spec)
    out += P.get("face_over", lambda P, s: "")(P, spec)
    out += brows(P, spec)
    return out


def head(P, spec):
    cid = uid("h")
    hx, hy = head_center(P)
    out = '<clipPath id="%s">%s</clipPath>' % (cid, head_rect(P, ""))
    out += head_rect(P, st(P.get("skin", SKIN)))
    out += '<g clip-path="url(#%s)">' % cid
    out += P.get("hair", lambda P: "")(P)
    out += '<rect x="%.3f" y="%.3f" width="0.24" height="%.3f" fill="%s" opacity="%.2f"/>' % (
        hx - 0.5, hy - 0.5, HEAD_H + 0.1, INK, SHADE_OPACITY)
    out += '</g>'
    out += head_rect(P, st())            # the head outline runs unbroken, on top of the hair
    out += face(P, spec)
    out += P.get("hat", lambda P: "")(P)
    out += symbol(P, spec)
    return out


HALO = "#efe6d2"     # paper-coloured rim around a character, for dark backgrounds


def character(P, expr="neutral", x=0.0, y=0.0, D=200.0, flip=False, prop=True, halo=False,
              silhouette=False):
    """Return one SVG group. (x, y) is the foot point on the ground, in pixels."""
    spec = EXPRESSIONS[expr]
    parts = [shoes(P), P.get("back", lambda P: "")(P), body(P),
             P.get("neck", lambda P: "")(P), head(P, spec)]
    if prop and P.get("prop"):
        parts.append(P["prop"](P))
    figure = "".join(parts)
    if halo:
        fid = uid("f")
        figure = ('<filter id="%s" x="-40%%" y="-40%%" width="180%%" height="180%%">'
                  '<feMorphology in="SourceAlpha" operator="dilate" radius="0.035" result="d"/>'
                  '<feGaussianBlur in="d" stdDeviation="0.006" result="b"/>'
                  '<feFlood flood-color="%s"/><feComposite in2="b" operator="in" result="o"/>'
                  '<feMerge><feMergeNode in="o"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
                  '<g filter="url(#%s)">%s</g>') % (fid, HALO, fid, figure)
    if silhouette:       # silhouette: tests whether the cast can be told apart by shape alone
        sid = uid("s")
        figure = ('<filter id="%s"><feColorMatrix type="matrix" values="0 0 0 0 0.106  0 0 0 0 0.133  '
                  '0 0 0 0 0.2  0 0 0 1 0"/></filter><g filter="url(#%s)">%s</g>') % (sid, sid, figure)
        return '<g transform="translate(%.2f,%.2f) scale(%s%.2f,%.2f)">%s</g>' % (
            x, y, "-" if flip else "", D, D, figure)
    return '<g transform="translate(%.2f,%.2f) scale(%s%.2f,%.2f)">%s%s</g>' % (
        x, y, "-" if flip else "", D, D, ground_shadow(P), figure)


def total_height(P):
    """Height from the ground to the highest point of the hair or hat, in D."""
    return -(head_center(P)[1] + P["top"])


REQUIRED = ("name", "slug", "body_h", "body_w", "top_w", "coat", "brow", "top", "body_details")


def check(P):
    """Return the warnings for one character declaration. An empty list means it passes."""
    w = [("missing key '%s'" % k) for k in REQUIRED if k not in P]
    if w:
        return w
    h = total_height(P)
    if not 1.5 <= h <= 2.7:
        w.append("height %.2f D is outside the 1.5 to 2.7 D range of the drawing rules" % h)
    if not 0.2 <= P["top_w"] < P["body_w"] <= 0.62:
        w.append("shoulders (top_w) must be narrower than the hem (body_w), and the hem at most 0.62 D")
    if not (P.get("hair") or P.get("hat")):
        w.append("no hair or hat yet: the character will have no shape of its own")
    if not P.get("prop"):
        w.append("no signature prop yet")
    return w
