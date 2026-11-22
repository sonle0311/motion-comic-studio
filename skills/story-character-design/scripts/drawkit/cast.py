# -*- coding: utf-8 -*-
"""The cast of this project. This file is a TEMPLATE: edit CHANNEL, then replace the
sample character with the characters of your story. Each character declares only
what is its own (hair or hat, outfit, prop); head, body, hands, eyes, mouth and
expressions call the shared functions in core.py.

Coordinates are in D (head width), origin between the feet, negative y is up.
Landmark table and the meaning of every key: see references/declaring-characters.md
in the skill.
"""

from core import (INK, SW_IN, SKIN, st, hand, head_center, face_points, body_top)

CHANNEL = {
    "name": "Channel or story title",
    "tagline": "A one-line introduction",
    "background": "#141a2a",   # background of the cast line-up
    "accent": "#f6c343",       # accent colour (title, lamp glow)
}

# ================= SAMPLE CHARACTER =================
SAMPLE_HAIR = "#3a2e2a"


def sample_body(P, t):
    """Details on the coat. Everything drawn here is clipped to the body shape."""
    out = '<path d="M 0.10,%.3f L 0.10,0" %s/>' % (t + 0.2, st(sw=SW_IN))              # button line
    out += '<rect x="-0.33" y="-0.62" width="0.2" height="0.17" rx="0.02" %s/>' % st("none", SW_IN)  # chest pocket
    return out


def sample_neck(P):
    """Drawn after the body and before the head: collar, scarf, a bag on the hip."""
    t = body_top(P)
    hx, _ = head_center(P)
    out = ""
    for dx, rot in ((-0.14, -14), (0.18, 14)):
        out += '<ellipse cx="%.3f" cy="%.3f" rx="0.15" ry="0.07" transform="rotate(%d %.3f %.3f)" %s/>' % (
            hx + dx, t + 0.15, rot, hx + dx, t + 0.15, st("#ffffff", SW_IN))
    return out


def sample_hair(P):
    """Hair: clipped to the head shape; the head outline is drawn over it last."""
    hx, hy = head_center(P)
    d = "M %.3f,%.3f L %.3f,%.3f L %.3f,%.3f" % (hx - 0.6, hy - 0.6, hx + 0.6, hy - 0.6, hx + 0.6, hy - 0.10)
    d += " Q %.3f,%.3f %.3f,%.3f Q %.3f,%.3f %.3f,%.3f" % (
        hx + 0.30, hy - 0.27, hx, hy - 0.20, hx - 0.22, hy - 0.16, hx - 0.30, hy - 0.02)
    d += " L %.3f,%.3f L %.3f,%.3f Z" % (hx - 0.30, hy + 0.12, hx - 0.6, hy + 0.12)
    return '<path d="%s" %s/>' % (d, st(SAMPLE_HAIR, SW_IN))


def sample_prop(P):
    """Signature prop. For a held object draw the object first, then the hand (hand on top)."""
    out = '<g transform="rotate(8 0.70 -0.78)">'
    out += '<rect x="0.55" y="-0.96" width="0.30" height="0.36" rx="0.03" %s/>' % st("#3f6f8f")
    out += '<rect x="0.815" y="-0.94" width="0.03" height="0.32" %s/>' % st("#f4eedd", 0.018)
    out += '</g>'
    return out + hand(0.58, -0.60)


SAMPLE = {
    "name": "Sample", "slug": "sample", "role": "Role in the story",
    "body_h": 1.10,      # body height: child 0.85–0.95; adult 1.05–1.25
    "body_w": 0.48,      # half the width of the hem
    "top_w": 0.29,       # half the width of the shoulders
    "coat": "#4f7a5a",   # coat colour: the character's main identifying colour
    "brow": SAMPLE_HAIR,    # eyebrow colour
    "top": -0.46,        # highest point relative to the head centre: -0.46 is a bare crown; more negative with a hat
    "mouth_default": "smile",
    "lineup_expr": "neutral",
    "body_details": sample_body, "neck": sample_neck, "hair": sample_hair, "prop": sample_prop,
}

CAST = [SAMPLE]
