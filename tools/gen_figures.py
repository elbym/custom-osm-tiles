#!/usr/bin/env python3
"""Zeichnet vendor/figures/<figur>/<pose>.svg (Figuren für figures im Stil, siehe make-tiles.py) aus Teilen:
Menschen aus Kopf, Rumpf, Armen und Beinen mit Winkeln je Pose, Tiere und Wesen aus Körper und Augen je Pose.
Alles eigene Zeichnungen: Genre-Archetypen und Volksmotive, keine bestimmten Figuren aus Manga oder Anime.
Nur Flächen; Tuschekontur und Sticker-Rand setzt poi_sprite(). Aufruf: tools/gen_figures.py (zeichnet alle neu)."""
import math, pathlib
OUT = pathlib.Path(__file__).resolve().parent.parent / "vendor" / "figures"
SKIN, BLUSH, Y = "#fde2c8", "#ff9fb2", "#ffd84a"
JUMP = "translate(0,-3) translate(32 64) scale(0.9) translate(-32 -64)"

def star4(x, y, r, fill=Y):
    return (f'<path d="M{x} {y-r} Q{x} {y} {x+r} {y} Q{x} {y} {x} {y+r} Q{x} {y} {x-r} {y} Q{x} {y} {x} {y-r} Z" '
            f'fill="{fill}" stroke-width="0.8"/>')

def eyes(kind, pts, iris="#2b2a3a", line=""):
    ln = f' stroke="{line}"' if line else ""
    s = ""
    for i, (x, y) in enumerate(pts):
        if kind in ("normal", "entschlossen"):
            if line:  # Tanuki: weiße Augen auf dunklem Fleck
                s += f'<circle cx="{x}" cy="{y}" r="2.3" fill="#fff" stroke="none"/><circle cx="{x}" cy="{y}" r="1.2" fill="#2b2a3a" stroke="none"/>'
            else:
                s += (f'<ellipse cx="{x}" cy="{y}" rx="2.6" ry="3.4" fill="{iris}" stroke-width="1"/>'
                      f'<circle cx="{x+0.9}" cy="{y-1.3}" r="1.1" fill="#fff" stroke="none"/>')
            if kind == "entschlossen":
                d = 1 if i == 0 else -1
                s += f'<path d="M{x-3*d} {y-6} L{x+2*d} {y-4.5}" fill="none" stroke-width="1.6"{ln}/>'
        elif kind == "froh":
            s += f'<path d="M{x-3} {y+1} Q{x} {y-3.5} {x+3} {y+1}" fill="none" stroke-width="2"{ln}/>'
        elif kind == "schlaeft":
            s += f'<path d="M{x-3} {y} Q{x} {y+2.5} {x+3} {y}" fill="none" stroke-width="2"{ln}/>'
    return s

def limb(sx, sy, a, w, l, fill, end=None):
    hx, hy = sx - l * math.sin(math.radians(a)), sy + l * math.cos(math.radians(a))
    s = f'<rect x="{sx-w/2}" y="{sy}" width="{w}" height="{l}" rx="{w/2}" fill="{fill}" transform="rotate({a} {sx} {sy})"/>'
    if end:
        s += f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="2.6" fill="{end}"/>'
    return s, (hx, hy)

MOUTH = {"normal": '<path d="M30 32 Q32 34 34 32" fill="none" stroke-width="1.4"/>',
         "froh": '<path d="M29 31 Q32 36.5 35 31 Z" fill="#d0485a" stroke-width="1.2"/>',
         "entschlossen": '<path d="M30 33 L34 33" fill="none" stroke-width="1.4"/>',
         "schlaeft": '<path d="M30.5 32.5 Q32 33.8 33.5 32.5" fill="none" stroke-width="1.3"/>'}
face = lambda skin=SKIN: f'<ellipse cx="32" cy="24" rx="14" ry="13" fill="{skin}"/>'
FACE = face()
WAND = lambda hx, hy: f'<path d="M{hx:.1f} {hy:.1f} l5 -12" fill="none" stroke-width="2.2"/>' + star4(round(hx + 5.5, 1), round(hy - 13.5, 1), 4.5)
MIC = lambda hx, hy: (f'<path d="M{hx:.1f} {hy:.1f} l1.5 -5" fill="none" stroke-width="2"/>'
                      f'<circle cx="{hx+2:.1f}" cy="{hy-7:.1f}" r="2.6" fill="#9aa0ad" stroke-width="1"/>')

H = {  # Menschenfiguren (Genre-Archetypen): Teile im 64er-Raster, Kopfmitte (32, 24)
 "ninja": dict(
    back='<path d="M46 16 L58 10 L55 17 L61 22 L47 20 Z" fill="#e5383b"/>',
    head='<circle cx="32" cy="23" r="16" fill="#3a3550"/><path d="M18 22 C24 19 40 19 46 22 L45 29 C38 31 26 31 19 29 Z" fill="#fde2c8"/>'
         '<path d="M17 15 C24 12 40 12 47 15 L47 19 C40 17 24 17 17 19 Z" fill="#e5383b"/><rect x="28" y="13.5" width="8" height="4.5" fill="#c9ccd8" stroke-width="1"/>',
    eyes_y=25, mouth=False, blush=False,
    torso='<path d="M25 36 L39 36 L40 50 L24 50 Z" fill="#3a3550"/><path d="M24 45 L40 45 L40 47.5 L24 47.5 Z" fill="#e5383b" stroke-width="1"/>',
    sleeve="#3a3550", hand="#3a3550", leg="#3a3550", legw=6),
 "zauberin": dict(
    back='<path d="M14 28 C12 10 22 6 32 6 C42 6 52 10 50 28 L49 38 L15 38 Z" fill="#9b6dff"/>',
    head=FACE + '<path d="M17 23 C21 13 29 14 32 18 C35 14 43 13 47 23 C40 19 36 21 32 22 C28 21 24 19 17 23 Z" fill="#9b6dff"/>'
         '<path d="M28 8 L32 3 L36 8 Z" fill="#ffd84a" stroke-width="1"/>',
    iris="#3a6fd8", torso='<path d="M25 36 L39 36 L45 52 L19 52 Z" fill="#ff7fb0"/><path d="M26 36 L32 41 L38 36 Z" fill="#fff" stroke-width="1"/>',
    sleeve="#ff7fb0", hand=SKIN, leg=SKIN, legw=4, item=WAND),
 "schulmaedchen": dict(
    back='<path d="M13 26 C11 10 22 7 32 7 C42 7 53 10 51 26 L53 46 L11 46 Z" fill="#6b4a35"/>',
    head=FACE + '<path d="M17 24 C19 12 45 12 47 24 C44 18 40 17 37 20 C34 16 28 16 26 20 C23 17 19 19 17 24 Z" fill="#6b4a35"/>',
    iris="#7a4a2a", mouth=False,
    top='<path d="M33 31 C33 28 37 28 37 30 C37 28 41 28 41 31 L41 37 L33 37 Z" fill="#f2c27a" stroke-width="1.2"/>'
        '<path d="M34.6 31.6 L39.4 31.6 L39.4 35.6 L34.6 35.6 Z" fill="#fff1d0" stroke="none"/>',
    torso='<path d="M25 36 L39 36 L40 45 L24 45 Z" fill="#fff"/><path d="M23 44 L41 44 L45 52 L19 52 Z" fill="#2f3e6e"/>'
          '<path d="M25 36 L32 42 L39 36 L39 39.5 L32 45 L25 39.5 Z" fill="#2f3e6e"/><path d="M30 42 L34 42 L32 46 Z" fill="#e5383b" stroke-width="1"/>',
    sleeve="#fff", hand=SKIN, leg=SKIN, legw=4),
 "samurai": dict(
    back='<path d="M28 5 C28 0 36 0 36 5 L35 10 L29 10 Z" fill="#3a3a48"/><path d="M16 24 C15 12 23 8 32 8 C41 8 49 12 48 24 Z" fill="#3a3a48"/>'
         '<path d="M17 17 L6 14 L9 20 L17 20 Z" fill="#fff"/>',
    head=FACE + '<path d="M17 22 C19 13 45 13 47 22 C42 17 22 17 17 22 Z" fill="#3a3a48"/>'
         '<path d="M17 16 C24 13 40 13 47 16 L47 20 C40 17.5 24 17.5 17 20 Z" fill="#fff"/>',
    brows=True, torso='<path d="M25 36 L39 36 L41 50 L23 50 Z" fill="#4a6a9a"/><path d="M28 36 L32 42 L36 36 Z" fill="#fff" stroke-width="1"/>',
    front='<path d="M17 50 L49 41 L49.6 43 L17.6 52 Z" fill="#3a3550"/><path d="M43 42.7 L49 41 L49.6 43 L43.6 44.7 Z" fill="#c9a04a" stroke-width="1"/>',
    sleeve="#4a6a9a", sleevew=6, hand=SKIN, leg="#3a3a48", legw=7),
 "miko": dict(
    back='<path d="M13 26 C11 10 22 7 32 7 C42 7 53 10 51 26 L50 48 L14 48 Z" fill="#2b2a3a"/>'
         '<path d="M46 9 L53 5 L53 13 Z M46 9 L41 4 L41 12 Z" fill="#fff"/>',
    head=FACE + '<path d="M17 24 L17 16 C20 10 44 10 47 16 L47 24 L45 20 L19 20 Z" fill="#2b2a3a"/>',
    iris="#6b3a2a", torso='<path d="M24 36 L40 36 L40 45 L24 45 Z" fill="#fff"/><path d="M22 44 L42 44 L45 53 L19 53 Z" fill="#d8342c"/>'
         '<path d="M28 36 L32 41 L36 36" fill="none" stroke="#d8342c" stroke-width="1.5"/>',
    sleeve="#fff", sleevew=7, hand=SKIN, leg="#d8342c", legw=6),
 "held": dict(
    back='<path d="M14 26 L8 16 L17 17 L14 6 L24 11 L28 2 L33 9 L40 2 L42 10 L51 6 L48 16 L57 15 L50 26 Z" fill="#d9482b"/>',
    head=FACE + '<path d="M18 22 L20 14 L24 19 L27 12 L31 19 L35 12 L38 19 L42 13 L44 19 L47 15 L46 22 C40 17 24 17 18 22 Z" fill="#d9482b"/>',
    iris="#2f7a4a", brows=True,
    top='<rect x="40" y="28" width="6" height="3" fill="#fff" stroke-width="0.8" transform="rotate(-15 43 29.5)"/>',
    torso='<path d="M25 36 L39 36 L41 50 L23 50 Z" fill="#3f8f5a"/><path d="M29.5 36 L34.5 36 L33.5 50 L30.5 50 Z" fill="#fff" stroke-width="1"/>',
    sleeve="#3f8f5a", sleevew=6, hand=SKIN, leg="#2f3e6e", legw=6),
 "idol": dict(
    back='<path d="M45 12 C59 9 62 28 54 38 C53 28 50 20 45 18 Z" fill="#ff8fc1"/>'
         '<path d="M15 27 C13 11 22 7 32 7 C42 7 51 11 49 27 L47 35 L17 35 Z" fill="#ff8fc1"/>',
    head=FACE + '<path d="M17 24 C20 13 30 13 33 19 C36 13 44 13 47 24 C40 18 30 20 17 24 Z" fill="#ff8fc1"/>' + star4(45, 12, 4),
    iris="#b04ad8", torso='<path d="M25 36 L39 36 L45 51 L19 51 Z" fill="#ffd84a"/>'
         '<path d="M19 50 L45 50 L46 53 Q42.5 56 39 53 Q35.5 56 32 53 Q28.5 56 25 53 Q21.5 56 18 53 Z" fill="#fff" stroke-width="1.2"/>'
         '<path d="M32 39 L27 36.5 L27 41.5 Z M32 39 L37 36.5 L37 41.5 Z" fill="#ff8fc1" stroke-width="1"/>',
    sleeve="#ffd84a", sleevew=6, hand=SKIN, leg=SKIN, legw=4, item=MIC),
 "mecha": dict(
    back='<path d="M32 9 L32 3" fill="none" stroke-width="1.6"/><circle cx="32" cy="3" r="2" fill="#ff9a3c" stroke-width="1"/>',
    head='<path d="M16 27 C16 12 24 8 32 8 C40 8 48 12 48 27 L46 35 L18 35 Z" fill="#d9dce4"/><path d="M19 19 L45 19 L44 29 L20 29 Z" fill="#2b2a3a"/>'
         '<path d="M21 31.5 L25 31.5 M39 31.5 L43 31.5" fill="none" stroke-width="1.2"/>',
    eyes_fn=lambda k: '<path d="M27 26 L32 21.5 L37 26" fill="none" stroke="#ff9a3c" stroke-width="2.4"/>' if k == "froh"
        else '<rect x="26" y="22" width="12" height="4" rx="2" fill="#ff9a3c" stroke="none"/>',
    mouth=False, blush=False,
    torso='<path d="M24 36 L40 36 L41 50 L23 50 Z" fill="#ff9a3c"/><path d="M28 39 L36 39 L35 45 L29 45 Z" fill="#d9dce4" stroke-width="1"/>',
    sleeve="#9aa0ad", sleevew=6, hand="#9aa0ad", leg="#9aa0ad", legw=7),
}

POSES = {  # Arme (links, rechts), Beine (links, rechts) in Grad, 0 = nach unten, positiv = nach links
 "steht":   dict(arms=(20, -20), legs=(4, -4), face="normal"),
 "winkt":   dict(arms=(20, -105), legs=(4, -4), face="froh", fx="winken"),
 "laeuft":  dict(arms=(55, -55), legs=(35, -35), face="entschlossen", t="rotate(8 32 58)", fx="tempo"),
 "springt": dict(arms=(105, -105), legs=(40, -40), face="froh", t=JUMP, fx="sprung"),
 "schlaeft": dict(arms=(6, -6), legs=(2, -2), face="schlaeft", fx="schlaf"),   # liegt auf dem Futon (Anime Nacht)
}
SHADOW = '<ellipse cx="32" cy="61" rx="11" ry="2" fill="#2b2a3a" fill-opacity="0.22" stroke="none"/>'
SPARK = star4(8, 16, 4) + star4(56, 26, 3.5) + star4(11, 40, 2.5)
TEMPO = '<path d="M2 30 L11 30 M0 38 L10 38 M3 46 L10 46" fill="none" stroke-width="1.6"/>'
ZZ = '<path d="M48 9 L53 9 L48 15 L53 15 M55 2 L58.5 2 L55 6 L58.5 6" fill="none" stroke-width="1.5"/>'

# Futon: Matratze und Kissen darunter, Decke über Rumpf und Beinen (der Kopf liegt nach dem Drehen bei etwa 24/40)
FUTON = ('<rect x="3" y="49" width="58" height="9" rx="3" fill="#f4efd8"/>'
         '<ellipse cx="16" cy="51" rx="10" ry="4.5" fill="#ffffff"/>')
BLANKET = ('<path d="M34 34 C40 31 56 31 61 35 L61 57 C52 59 40 59 34 57 C32 50 32 41 34 34 Z" fill="#9cc6ee"/>'
           '<path d="M34.5 38 C41 35.5 55 35.5 61 39 M34 52 C41 54 53 54 61 52" fill="none" stroke="#ffffff" stroke-width="1.6"/>'
           '<path d="M34 34 C33 42 33 50 34 57" fill="none" stroke-width="1.4"/>')

def human(f, p, look=None):
    """look (tools/gen_stickers.py): eigene eyes/blush/mouth, head_t (Transform für den Kopf), head_only; sonst Karten-Look."""
    lk = look or {}
    legl = 8 if p.get("fx") == "sprung" else 9
    parts = [f.get("back", "")]
    for (hx, a) in ((28, p["legs"][0]), (36, p["legs"][1])):
        parts.append(limb(hx, 48, a, f["legw"], legl, f["leg"])[0])
    parts.append(f["torso"] + f.get("front", ""))
    la, _ = limb(25, 38, p["arms"][0], f.get("sleevew", 5), 11, f["sleeve"], f["hand"])
    ra, hand = limb(39, 38, p["arms"][1], f.get("sleevew", 5), 11, f["sleeve"], f["hand"])
    parts += [la, ra + (f["item"](*hand) if "item" in f else "")]
    ey = f.get("eyes_y", 26)
    n_body = len(parts)   # Schlafpose: Körper liegt (gedreht), Kopf bleibt aufrecht auf dem Kissen
    parts.append(f["head"])
    parts.append(f["eyes_fn"](p["face"]) if "eyes_fn" in f else lk.get("eyes", eyes)(p["face"], [(26, ey), (38, ey)], f.get("iris", "#2b2a3a")))
    if f.get("brows") and p["face"] != "entschlossen":
        parts.append(f'<path d="M22 {ey-6} L28 {ey-4.5} M42 {ey-6} L36 {ey-4.5}" fill="none" stroke-width="1.6"/>')
    if f.get("blush", True):
        parts.append(lk.get("blush", f'<ellipse cx="20.5" cy="30" rx="3" ry="1.6" fill="{BLUSH}" stroke="none"/><ellipse cx="43.5" cy="30" rx="3" ry="1.6" fill="{BLUSH}" stroke="none"/>'))
    if f.get("mouth", True):
        parts.append(f["mouth_fn"](p["face"]) if "mouth_fn" in f else lk.get("mouth", MOUTH)[p["face"]])
    parts.append(f.get("top", ""))
    if p.get("fx") == "winken":
        x, y = hand
        parts.append(f'<path d="M{x+4:.1f} {y-5:.1f} q3 3 0 6 M{x+7:.1f} {y-8:.1f} q5 5.5 0 11" fill="none" stroke-width="1.4"/>')
    if p.get("fx") == "schlaf":   # Nutzerwunsch 2026-11-26: nachts schlafen alle; Körper liegt, Kopf aufrecht links auf dem Kissen
        body, head = "".join(parts[:n_body]), "".join(parts[n_body:])
        return (FUTON + f'<g transform="translate(0 8) rotate(-90 32 32)">{body}</g>' + BLANKET
                + f'<g transform="translate(-11 15) rotate(-14 32 24) scale(0.92) translate(2.8 2)">{head}</g>' + ZZ)
    if "head_t" in lk:
        parts[n_body:] = [f'<g transform="{lk["head_t"]}">' + "".join(parts[n_body:]) + "</g>"]
    if lk.get("head_only"):   # Kopf-Sticker: nur Haar hinten und Kopf
        return parts[0] + "".join(parts[n_body:])
    body = "".join(parts)
    if "t" in p:
        body = f'<g transform="{p["t"]}">{body}</g>'
    pre = {"sprung": SHADOW, "tempo": TEMPO}.get(p.get("fx"), "")
    post = SPARK if p.get("fx") == "sprung" else ""
    return pre + body + post

A = {  # Tiere und Wesen (Volksmotive): Körper ohne Augen, Augenpositionen
 "kitsune": dict(eyes=[(24, 25), (40, 25)], body=
    '<path d="M40 52 C58 50 62 30 50 22 C54 34 46 42 38 44 Z" fill="#f08a3c"/><path d="M50 22 C56 27 57 33 55 38 C52 32 50 27 50 22 Z" fill="#fff6ea"/>'
    '<path d="M20 56 C18 44 22 36 32 36 C42 36 46 44 44 56 Z" fill="#f08a3c"/><path d="M27 56 C27 47 29 42 32 42 C35 42 37 47 37 56 Z" fill="#fff6ea"/>'
    '<path d="M14 8 L22 20 L16 24 Z M50 8 L42 20 L48 24 Z" fill="#f08a3c"/>'
    '<path d="M12 26 C12 16 22 12 32 12 C42 12 52 16 52 26 C52 34 44 38 32 40 C20 38 12 34 12 26 Z" fill="#f08a3c"/>'
    '<path d="M18 30 C22 36 28 38 32 38 C36 38 42 36 46 30 C40 33 24 33 18 30 Z" fill="#fff6ea" stroke="none"/>'
    '<circle cx="32" cy="31" r="1.6" fill="#2b2a3a" stroke="none"/><path d="M30 15 L32 20 L34 15" fill="#d0342c" stroke-width="1"/>'),
 "neko": dict(eyes=[(23, 24), (41, 24)], body=
    '<path d="M18 58 C16 44 20 36 32 36 C44 36 48 44 46 58 Z" fill="#fff"/>'
    '<path d="M44 40 C48 36 50 30 49 24 C53 24 55 28 54 32 C53 36 50 40 47 43 Z" fill="#fff"/>'
    '<circle cx="32" cy="46" r="5" fill="#f5c542"/><path d="M20 38 L44 38" stroke="#e5383b" stroke-width="3"/>'
    '<path d="M14 6 L24 16 L14 22 Z M50 6 L40 16 L50 22 Z" fill="#fff"/><path d="M15 8 L21 15 L16 18 Z" fill="#ff9fb2" stroke="none"/>'
    '<path d="M11 24 C11 14 21 11 32 11 C43 11 53 14 53 24 C53 33 44 38 32 38 C20 38 11 33 11 24 Z" fill="#fff"/>'
    '<path d="M36 12 C42 11 50 14 52 20 C46 20 40 18 36 12 Z" fill="#f08a3c" stroke="none"/>'
    '<path d="M29 29 Q32 32 35 29" fill="none" stroke-width="1.5"/>'
    '<path d="M12 28 L4 26 M12 31 L4 32 M52 28 L60 26 M52 31 L60 32" fill="none" stroke-width="1"/>'
    '<ellipse cx="18" cy="29" rx="3" ry="1.6" fill="#ff9fb2" stroke="none"/><ellipse cx="46" cy="29" rx="3" ry="1.6" fill="#ff9fb2" stroke="none"/>'),
 "onigiri": dict(eyes=[(24, 30), (40, 30)], body=
    '<path d="M32 6 C40 6 58 40 56 50 C54 58 10 58 8 50 C6 40 24 6 32 6 Z" fill="#fff"/><path d="M18 40 L46 40 L48 57 L16 57 Z" fill="#2f4a3a"/>'
    '<path d="M29 34.5 Q32 37.5 35 34.5" fill="none" stroke-width="1.5"/>'
    '<ellipse cx="19" cy="35" rx="3" ry="1.6" fill="#ff9fb2" stroke="none"/><ellipse cx="45" cy="35" rx="3" ry="1.6" fill="#ff9fb2" stroke="none"/>'),
 "tanuki": dict(eyes=[(23, 25), (41, 25)], line="#ffffff", body=
    '<path d="M42 50 C52 50 58 44 56 36 C52 42 48 44 42 44 Z" fill="#8a6a4e"/><path d="M54 38 L56 36 L57 42 L53 44 Z" fill="#3a3550" stroke="none"/>'
    '<ellipse cx="32" cy="48" rx="15" ry="11" fill="#a07e5e"/><ellipse cx="32" cy="50" rx="9" ry="7" fill="#f3e2c8"/>'
    '<circle cx="17" cy="14" r="5" fill="#8a6a4e"/><circle cx="47" cy="14" r="5" fill="#8a6a4e"/><ellipse cx="32" cy="24" rx="19" ry="15" fill="#a07e5e"/>'
    '<path d="M16 25 C18 19 26 19 28 25 C26 30 18 30 16 25 Z M48 25 C46 19 38 19 36 25 C38 30 46 30 48 25 Z" fill="#3a3550" stroke="none"/>'
    '<ellipse cx="32" cy="31" rx="7" ry="5" fill="#f3e2c8"/><ellipse cx="32" cy="29.5" rx="2" ry="1.4" fill="#2b2a3a" stroke="none"/>'
    '<path d="M32 9 C26 2 36 0 40 4 C38 8 36 10 32 9 Z" fill="#7cc95a" stroke-width="1.2"/><path d="M32 9 L38 4" fill="none" stroke-width="0.8"/>'),
 "geist": dict(eyes=[(27, 29), (38, 29)], body=
    '<path d="M46 36 L52 40" fill="none" stroke-width="1.6"/>'
    '<path d="M18 30 C18 12 46 12 46 30 L46 52 L41 47 L36 53 L32 48 L27 53 L23 47 L18 52 Z" fill="#eef0ff"/>'
    '<path d="M44 36 C48 34 50 36 48 40 Z" fill="#eef0ff"/><path d="M28 15 L36 15 L32 21 Z" fill="#fff" stroke-width="1"/>'
    '<path d="M31 34 Q32.5 36 34 34" fill="none" stroke-width="1.3"/>'
    '<ellipse cx="22.5" cy="33" rx="2.6" ry="1.4" fill="#b8c8ff" stroke="none"/><ellipse cx="42" cy="33" rx="2.6" ry="1.4" fill="#b8c8ff" stroke="none"/>'
    '<rect x="50" y="38" width="8" height="3" fill="#2b2a3a"/><rect x="50" y="53" width="8" height="3" fill="#2b2a3a"/>'
    '<ellipse cx="54" cy="47.5" rx="7" ry="7" fill="#ff9a3c"/><path d="M47.5 45 L60.5 45 M47.5 50 L60.5 50" fill="none" stroke-width="1"/>'),
}

def animal(a, pose):
    if pose == "sitzt":
        return a["body"] + eyes("normal", a["eyes"], line=a.get("line", ""))
    if pose == "schlaeft":
        return a["body"] + eyes("schlaeft", a["eyes"], line=a.get("line", "")) + ZZ
    return SHADOW + f'<g transform="{JUMP}">{a["body"]}{eyes("froh", a["eyes"], line=a.get("line", ""))}</g>' + SPARK

HEAD = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
def write(name, pose, desc, body):
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{pose}.svg").write_text(f"<!-- {desc}, Pose {pose}; eigene Zeichnung, 64×64. Kontur/Sticker setzt poi_sprite() -->\n{HEAD}\n{body}\n</svg>\n")

DESC = {"ninja": "Chibi-Ninja mit Stirnband (Genre-Archetyp)", "zauberin": "Magical Girl mit Sternstab (Genre-Archetyp)",
        "schulmaedchen": "Schülerin mit Toast im Mund, zu spät (Genre-Archetyp)", "samurai": "Samurai mit Hachimaki (Genre-Archetyp)",
        "miko": "Schreinmädchen (Genre-Archetyp)", "held": "Shōnen-Held mit Strubbelhaar und Pflaster (Genre-Archetyp)",
        "idol": "Idol mit Mikrofon (Genre-Archetyp)", "mecha": "Chibi-Mecha (Genre-Archetyp)",
        "kitsune": "Kitsune (Volksmotiv)", "neko": "Winkekatze (Volksmotiv)", "onigiri": "Reisbällchen mit Gesicht (Chibi-Food)",
        "tanuki": "Tanuki mit Blatt (Volksmotiv)", "geist": "Geist mit Papierlaterne (Volksmotiv)"}
# --- Weitere Archetypen (Nutzerwunsch 2026-11-24) ---------------------------------------------------------------------
TRAY = lambda x, y: (f'<path d="M{x-7:.1f} {y-2:.1f} L{x+7:.1f} {y-2:.1f} L{x+6:.1f} {y:.1f} L{x-6:.1f} {y:.1f} Z" fill="#c9ccd8"/>'
                     f'<path d="M{x-3:.1f} {y-2:.1f} L{x-2.5:.1f} {y-7:.1f} L{x+2.5:.1f} {y-7:.1f} L{x+3:.1f} {y-2:.1f} Z" fill="#fff"/>')
SHINAI = lambda x, y: (f'<path d="M{x:.1f} {y:.1f} l9 -17" fill="none" stroke-width="2.4"/>'
                       f'<path d="M{x:.1f} {y-3.5:.1f} l4 2" fill="none" stroke-width="2"/>')
CLIPBOARD = lambda x, y: (f'<rect x="{x-4:.1f}" y="{y-10:.1f}" width="8" height="10" rx="1" fill="#c9a06a"/>'
                          f'<rect x="{x-2.8:.1f}" y="{y-8.5:.1f}" width="5.6" height="7" fill="#fff" stroke="none"/>')
POINTER = lambda x, y: f'<path d="M{x:.1f} {y:.1f} l11 -11" fill="none" stroke-width="1.5"/>'
BAT = lambda x, y: f'<path d="M{x-1:.1f} {y+1:.1f} L{x+5:.1f} {y-14:.1f} L{x+8.5:.1f} {y-12.5:.1f} L{x+1.5:.1f} {y+1.5:.1f} Z" fill="#d9a066"/>'
BOWL = lambda x, y: (f'<path d="M{x-6:.1f} {y-4:.1f} L{x+6:.1f} {y-4:.1f} C{x+6:.1f} {y+2:.1f} {x-6:.1f} {y+2:.1f} {x-6:.1f} {y-4:.1f} Z" fill="#e5383b"/>'
                     f'<path d="M{x-4:.1f} {y-4:.1f} q2 -3 4 0 q2 -3 4 0" fill="none" stroke-width="1"/>')
PEN = lambda x, y: f'<path d="M{x:.1f} {y:.1f} l6 -9" fill="none" stroke-width="2"/><path d="M{x+6:.1f} {y-9:.1f} l1.5 -2.5" fill="none" stroke-width="1"/>'
TEACUP = lambda x, y: (f'<path d="M{x-5:.1f} {y-1:.1f} L{x+5:.1f} {y-1:.1f}" fill="none" stroke-width="1.6"/>'
                       f'<path d="M{x-3:.1f} {y-6:.1f} L{x+3:.1f} {y-6:.1f} L{x+2:.1f} {y-1.5:.1f} L{x-2:.1f} {y-1.5:.1f} Z" fill="#fff"/>')
OFUDA = lambda x, y: (f'<g transform="rotate(12 {x:.1f} {y:.1f})"><rect x="{x:.1f}" y="{y-12:.1f}" width="5" height="11" fill="#fff8d8" stroke-width="1"/>'
                      f'<path d="M{x+2.5:.1f} {y-10:.1f} L{x+2.5:.1f} {y-3:.1f}" fill="none" stroke="#e5383b" stroke-width="1.2"/></g>')
STAFF = lambda top: lambda x, y: f'<path d="M{x-1:.1f} {y+7:.1f} L{x+3:.1f} {y-18:.1f}" fill="none" stroke-width="2"/>' + top(x + 3.3, y - 21)
RING = lambda x, y: f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="none" stroke-width="1.4"/>'
ORB = lambda x, y: f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="#8fd0ff" stroke-width="1"/>'
SWORD = lambda x, y: (f'<path d="M{x:.1f} {y:.1f} L{x+9:.1f} {y-17:.1f} L{x+11:.1f} {y-16:.1f} L{x+2:.1f} {y+1:.1f} Z" fill="#e6e9f0"/>'
                      f'<path d="M{x-2:.1f} {y-3:.1f} L{x+4:.1f} {y:.1f}" fill="none" stroke-width="2"/>')
FAN = lambda x, y: f'<path d="M{x:.1f} {y:.1f} C{x-5:.1f} {y-6:.1f} {x:.1f} {y-15:.1f} {x+7:.1f} {y-14:.1f} C{x+9:.1f} {y-8:.1f} {x+5:.1f} {y-2:.1f} {x:.1f} {y:.1f} Z" fill="#7cc95a"/>'
CLUB = lambda x, y: (f'<path d="M{x-1:.1f} {y+1:.1f} L{x+5:.1f} {y-15:.1f} L{x+10:.1f} {y-13:.1f} L{x+2:.1f} {y+2:.1f} Z" fill="#9aa0ad"/>'
                     f'<circle cx="{x+5:.1f}" cy="{y-9:.1f}" r="0.9" fill="#2b2a3a" stroke="none"/><circle cx="{x+7:.1f}" cy="{y-12:.1f}" r="0.9" fill="#2b2a3a" stroke="none"/>')
GLASSES = ('<circle cx="26" cy="26" r="4.6" fill="none" stroke-width="1.3"/><circle cx="38" cy="26" r="4.6" fill="none" stroke-width="1.3"/>'
           '<path d="M30.6 26 L33.4 26" fill="none" stroke-width="1.3"/>')
CAT = lambda k: MOUTH["froh"] if k == "froh" else '<path d="M29 32 Q30.5 34 32 32 Q33.5 34 35 32" fill="none" stroke-width="1.3"/>'
FANG = lambda k: MOUTH["froh" if k == "froh" else "normal"] + '<path d="M30.6 32.4 L31.3 34.8 L32 32.8 Z" fill="#fff" stroke-width="0.6"/>'
WINGS = lambda c: (f'<path d="M25 40 C14 28 4 32 6 42 C9 41 11 44 10 47 C15 46 20 47 25 46 Z '
                   f'M39 40 C50 28 60 32 58 42 C55 41 53 44 54 47 C49 46 44 47 39 46 Z" fill="{c}"/>')
CAPE = lambda c, inner: (f'<path d="M22 37 L42 37 L50 57 L14 57 Z" fill="{c}"/>'
                         f'<path d="M25 39 L39 39 L45 55 L19 55 Z" fill="{inner}" stroke="none"/>')
HAIR_SHORT = lambda c: f'<path d="M16 24 C15 12 23 9 32 9 C41 9 49 12 48 24 Z" fill="{c}"/>'
HAIR_LONG = lambda c: f'<path d="M13 26 C11 10 22 7 32 7 C42 7 53 10 51 26 L52 48 L12 48 Z" fill="{c}"/>'
HAIR_BOB = lambda c: f'<path d="M14 27 C12 12 22 8 32 8 C42 8 52 12 50 27 L48 35 L16 35 Z" fill="{c}"/>'
SPIKY = lambda c: (f'<path d="M17 23 L19 14 L24 19 L27 12 L31 18 L35 12 L38 18 L42 13 L44 18 L47 15 L47 23 '
                   f'C40 18 24 18 17 23 Z" fill="{c}"/>')
SHIRT = 'M25 36 L39 36 L41 50 L23 50 Z'
DRESS = 'M25 36 L39 36 L45 52 L19 52 Z'
ROBE = 'M24 36 L40 36 L45 57 L19 57 Z'

H.update({
 "maid": dict(
    back=HAIR_BOB("#8a4a2a"),
    head=FACE + '<path d="M17 24 C19 12 45 12 47 24 C43 18 37 18 32 21 C27 18 21 18 17 24 Z" fill="#8a4a2a"/>'
         '<path d="M19 13 Q22 9 25 12 Q28 8 32 11 Q36 8 39 12 Q42 9 45 13 L44 16 Q32 12 20 16 Z" fill="#fff"/>',
    iris="#8a4a2a", torso=f'<path d="{DRESS}" fill="#3a3550"/><path d="M27 40 L37 40 L40 51 L24 51 Z" fill="#fff"/>'
         '<path d="M28 36 L32 39 L36 36 Z" fill="#fff" stroke-width="1"/>',
    sleeve="#3a3550", hand=SKIN, leg="#3a3550", legw=4, item=TRAY),
 "kendo": dict(
    head='<path d="M14 27 C14 10 50 10 50 27 L49 37 L15 37 Z" fill="#2f3e6e"/><path d="M20 17 L44 17 L43 35 L21 35 Z" fill="#fde2c8"/>',
    top='<path d="M20 21 L44 21 M20 25.5 L44 25.5 M20 30 L44 30 M32 17 L32 35" fill="none" stroke="#c9ccd8" stroke-width="1.3"/>'
        '<path d="M20 17 L44 17 L43 35 L21 35 Z" fill="none" stroke-width="1.5"/>',
    mouth=False, blush=False,
    torso=f'<path d="{SHIRT}" fill="#3b4f86"/><path d="M25.5 37 L38.5 37 L39 46 C35 48 29 48 25 46 Z" fill="#5a3a3a"/>'
          '<path d="M23 46 L41 46 L42 52 L22 52 Z" fill="#2f3e6e"/>',
    sleeve="#3b4f86", sleevew=6, hand="#2f3e6e", leg="#2f3e6e", legw=7, item=SHINAI),
 "yankee": dict(
    back=HAIR_SHORT("#3a3a48"),
    head=FACE + '<path d="M17 19 C14 7 38 1 56 7 C48 8 42 11 40 16 C33 13 24 14 17 19 Z" fill="#3a3a48"/>',
    brows=True, top='<path d="M35 33 L42 31" fill="none" stroke="#c9a06a" stroke-width="1.4"/>',
    torso=f'<path d="M24 36 L40 36 L44 57 L20 57 Z" fill="#2b2a4a"/><path d="M27 36 L37 36 L36 39 L28 39 Z" fill="#2b2a4a"/>'
          '<circle cx="32" cy="42" r="1" fill="#ffd84a" stroke="none"/><circle cx="32" cy="47" r="1" fill="#ffd84a" stroke="none"/>'
          '<circle cx="32" cy="52" r="1" fill="#ffd84a" stroke="none"/>',
    sleeve="#2b2a4a", sleevew=6, hand=SKIN, leg="#2b2a4a", legw=6),
 "schulsprecherin": dict(
    back=HAIR_LONG("#2f3e6e"),
    head=FACE + '<path d="M17 23 C18 12 46 12 47 23 L44 20 L38 21 L32 19 L26 21 L20 20 Z" fill="#2f3e6e"/>',
    iris="#3a3a8a", top=GLASSES,
    torso='<path d="M25 36 L39 36 L40 45 L24 45 Z" fill="#7a2a3a"/><path d="M23 44 L41 44 L45 52 L19 52 Z" fill="#6c6f80"/>'
          '<path d="M29 36 L35 36 L32 42 Z" fill="#fff" stroke-width="1"/><path d="M31.2 37 L32.8 37 L32.6 41.5 L31.4 41.5 Z" fill="#2f3e6e" stroke="none"/>',
    sleeve="#7a2a3a", hand=SKIN, leg=SKIN, legw=4, item=CLIPBOARD),
 "lehrer": dict(
    back=HAIR_SHORT("#6b4a35"),
    head=FACE + '<path d="M17 22 C18 11 40 8 47 19 C40 15 30 16 17 22 Z" fill="#6b4a35"/>',
    top='<rect x="21.5" y="23" width="9" height="6" rx="1.5" fill="none" stroke-width="1.3"/>'
        '<rect x="33.5" y="23" width="9" height="6" rx="1.5" fill="none" stroke-width="1.3"/><path d="M30.5 25.5 L33.5 25.5" fill="none" stroke-width="1.3"/>',
    torso='<path d="M24 36 L40 36 L41 51 L23 51 Z" fill="#7a7f90"/><path d="M29 36 L35 36 L33.5 48 L30.5 48 Z" fill="#fff" stroke-width="1"/>'
          '<path d="M31.2 37 L32.8 37 L33 45 L32 47 L31 45 Z" fill="#e5383b" stroke-width="0.8"/>',
    sleeve="#7a7f90", sleevew=6, hand=SKIN, leg="#3a3a48", legw=6, item=POINTER),
 "baseball": dict(
    back='<path d="M16 26 L16 18 L48 18 L48 26 Z" fill="#3a3a48"/>',
    head=FACE + '<path d="M16 21 C16 7 48 7 48 21 Z" fill="#3a6fd8"/><path d="M42 20 L57 22 L55 25 L42 23 Z" fill="#3a6fd8"/>'
         '<path d="M30 13 L34 13" fill="none" stroke="#fff" stroke-width="2"/>',
    torso=f'<path d="{SHIRT}" fill="#fff"/><path d="M32 36 L32 50" fill="none" stroke="#3a6fd8" stroke-width="1.4"/>'
          '<path d="M24 47 L40 47" fill="none" stroke="#3a6fd8" stroke-width="2"/>',
    sleeve="#3a6fd8", hand=SKIN, leg="#f4f4f4", legw=6, item=BAT),
 "ramenkoch": dict(
    back=HAIR_SHORT("#3a3a48"),
    head=FACE + '<path d="M16 18 C22 12 42 12 48 18 L48 22 C42 18 22 18 16 22 Z" fill="#3a6fd8"/><path d="M47 18 L54 15 L53 21 L48 22 Z" fill="#3a6fd8"/>'
         '<circle cx="24" cy="17" r="0.9" fill="#fff" stroke="none"/><circle cx="32" cy="15.5" r="0.9" fill="#fff" stroke="none"/><circle cx="40" cy="17" r="0.9" fill="#fff" stroke="none"/>',
    torso=f'<path d="{SHIRT}" fill="#fff"/><path d="M26 41 L38 41 L40 52 L24 52 Z" fill="#2f3e6e"/>',
    sleeve="#fff", sleevew=6, hand=SKIN, leg="#3a3a48", legw=6, item=BOWL),
 "mangaka": dict(
    back=HAIR_BOB("#3f5a4a"),
    head=FACE + SPIKY("#3f5a4a") + '<path d="M17 14 C17 4 47 4 47 14 C40 16 24 16 17 14 Z" fill="#d9482b"/><path d="M32 5 L32 2" fill="none" stroke-width="1.6"/>',
    iris="#3f5a4a", top='<ellipse cx="42" cy="31" rx="2" ry="1" fill="#2b2a3a" stroke="none"/>',
    torso=f'<path d="{SHIRT}" fill="#9aa0ad"/><path d="M28 44 L36 44 L36 48 L28 48 Z" fill="none" stroke-width="1"/>',
    sleeve="#9aa0ad", sleevew=6, hand=SKIN, leg="#3a6fd8", legw=5, item=PEN),
 "butler": dict(
    back='<path d="M16 22 C15 11 23 8 32 8 C41 8 49 11 48 22 Z" fill="#9aa0ad"/>',
    head=FACE + '<path d="M17 21 C19 10 44 9 47 19 C40 14 26 14 17 21 Z" fill="#9aa0ad"/>',
    mouth=False, top='<circle cx="38" cy="26" r="4.3" fill="none" stroke="#c9a04a" stroke-width="1.3"/>'
        '<path d="M41 29.5 Q44 36 41 40" fill="none" stroke="#c9a04a" stroke-width="0.8"/>'
        '<path d="M28 31.5 Q30 30 32 31.5 Q34 30 36 31.5 Q34 33.5 32 32.4 Q30 33.5 28 31.5 Z" fill="#9aa0ad" stroke-width="0.8"/>',
    torso='<path d="M24 36 L40 36 L42 51 L22 51 Z" fill="#3a3550"/><path d="M29 36 L35 36 L32 46 Z" fill="#fff" stroke-width="1"/>'
          '<path d="M28.5 37 L32 38.5 L28.5 40 Z M35.5 37 L32 38.5 L35.5 40 Z" fill="#2b2a3a" stroke-width="0.6"/>',
    sleeve="#3a3550", hand="#ffffff", leg="#3a3550", legw=6, item=TEACUP),
 "onmyoji": dict(
    back='<path d="M24 13 L26 1 L38 1 L40 13 Z" fill="#3a3a48"/>' + HAIR_SHORT("#3a3a48"),
    head=FACE + '<path d="M17 22 C19 13 45 13 47 22 C42 17 22 17 17 22 Z" fill="#3a3a48"/>',
    iris="#6b4aa0", torso='<path d="M24 36 L40 36 L41 46 L23 46 Z" fill="#fff"/><path d="M22 45 L42 45 L45 54 L19 54 Z" fill="#6b4aa0"/>'
         '<path d="M27 36 L32 41 L37 36" fill="none" stroke="#6b4aa0" stroke-width="1.4"/>',
    sleeve="#fff", sleevew=7, hand=SKIN, leg="#6b4aa0", legw=7, item=OFUDA),
 "moench": dict(
    head=FACE + '<path d="M7 19 L32 4 L57 19 Q32 24 7 19 Z" fill="#d9b26a"/><path d="M19 12 L45 12 M14 16 L50 16" fill="none" stroke="#a8823a" stroke-width="0.9"/>',
    torso=f'<path d="{ROBE}" fill="#4a4a58"/><path d="M26 36 L30 36 L39 52 L35 52 Z" fill="#c9a04a"/>',
    sleeve="#4a4a58", sleevew=7, hand=SKIN, leg="#4a4a58", legw=6, item=STAFF(RING)),
 "nekomimi": dict(
    back='<path d="M40 50 C50 56 60 46 55 37 L52 39 C55 46 48 51 41 47 Z" fill="#f0a050"/>'
         '<path d="M15 16 L17 2 L28 10 Z M49 16 L47 2 L36 10 Z" fill="#f0a050"/>'
         '<path d="M18 12 L19 6 L24 10 Z M46 12 L45 6 L40 10 Z" fill="#ff9fb2" stroke="none"/>' + HAIR_BOB("#f0a050"),
    head=FACE + '<path d="M17 23 C20 13 29 13 32 17 C35 13 44 13 47 23 C42 18 37 19 32 21 C27 19 22 18 17 23 Z" fill="#f0a050"/>',
    iris="#3fa070", mouth_fn=CAT,
    torso=f'<path d="{DRESS}" fill="#8fd0ff"/><path d="M29 36 L35 36 L32 40 Z" fill="#fff" stroke-width="1"/><circle cx="32" cy="40.5" r="1.8" fill="#ffd84a" stroke-width="0.8"/>',
    sleeve="#8fd0ff", hand=SKIN, leg=SKIN, legw=4),
 "schwertkaempfer": dict(
    back=CAPE("#3a5a8a", "#2a4068") + '<path d="M15 25 C13 11 22 7 32 7 C42 7 51 11 49 25 L47 31 L17 31 Z" fill="#5a3a2a"/>',
    head=FACE + SPIKY("#5a3a2a"), brows=True, iris="#3a6fd8",
    torso=f'<path d="{SHIRT}" fill="#8a6a4e"/><path d="M23 44 L41 44 L41 46.5 L23 46.5 Z" fill="#5a3a2a" stroke-width="1"/>'
          '<path d="M25 35 L39 35 L39 38.5 L25 38.5 Z" fill="#d8342c"/><path d="M27 38 L24 45 L28 44 Z" fill="#d8342c"/>',
    sleeve="#f4efe4", hand="#5a3a2a", leg="#3a3a48", legw=6, item=SWORD),
 "magier": dict(
    back='<path d="M14 27 C12 18 52 18 50 27 L48 38 L16 38 Z" fill="#c9ccd8"/>',
    head=FACE + '<path d="M9 19 Q32 25 55 19 Q46 15 40 15 L33 1 L24 15 Q16 15 9 19 Z" fill="#4a4ab0"/>'
         '<path d="M23 15.5 Q32 18 41 15.5 L41.6 17.5 Q32 20.3 22.4 17.5 Z" fill="#ffd84a" stroke-width="0.8"/>' + star4(30, 9, 2.5),
    iris="#4a4ab0", torso=f'<path d="{ROBE}" fill="#4a4ab0"/><path d="M30 36 L34 36 L33 57 L31 57 Z" fill="#ffd84a" stroke-width="0.8"/>',
    sleeve="#4a4ab0", sleevew=7, hand=SKIN, leg="#4a4ab0", legw=6, item=STAFF(ORB)),
 "ritterin": dict(
    back='<path d="M44 14 C58 16 60 34 52 44 C52 34 50 24 44 20 Z" fill="#f5c542"/>'
         '<path d="M15 26 C13 11 22 7 32 7 C42 7 51 11 49 26 L47 34 L17 34 Z" fill="#f5c542"/>',
    head=FACE + '<path d="M17 23 C19 12 45 12 47 23 C43 18 36 17 32 20 C28 17 21 18 17 23 Z" fill="#f5c542"/>'
         '<path d="M17 17 Q32 12 47 17" fill="none" stroke="#c9ccd8" stroke-width="1.6"/>',
    iris="#3a6fd8", brows=True,
    torso='<path d="M25 36 L39 36 L40 44 L24 44 Z" fill="#c9ccd8"/><path d="M23 43 L41 43 L44 53 L20 53 Z" fill="#d8342c"/>'
          '<path d="M28 39.5 L36 39.5" fill="none" stroke-width="1"/>',
    sleeve="#c9ccd8", hand="#9aa0ad", leg="#9aa0ad", legw=5, item=SWORD),
 "daemonenkoenig": dict(
    back=CAPE("#2b2a4a", "#6b3a8a") + '<path d="M19 15 C11 10 11 3 15 1 C15 6 19 9 24 11 Z M45 15 C53 10 53 3 49 1 C49 6 45 9 40 11 Z" fill="#c9ccd8"/>'
         '<path d="M15 26 C13 11 22 7 32 7 C42 7 51 11 49 26 L47 32 L17 32 Z" fill="#6b3a8a"/>',
    head=FACE + SPIKY("#6b3a8a"), iris="#d8342c", mouth_fn=FANG, brows=True,
    torso=f'<path d="{SHIRT}" fill="#3a2a4a"/><path d="M29 38 L35 38 L32 43 Z" fill="#ffd84a" stroke-width="0.8"/>',
    sleeve="#3a2a4a", hand=SKIN, leg="#3a2a4a", legw=6),
 "engel": dict(
    back=WINGS("#fff") + '<ellipse cx="32" cy="4" rx="9" ry="2.6" fill="none" stroke="#ffd84a" stroke-width="2"/>'
         '<path d="M14 27 C11 12 22 7 32 7 C42 7 53 12 50 27 C52 31 48 35 46 33 L18 33 C16 35 12 31 14 27 Z" fill="#ffe08a"/>',
    head=FACE + '<path d="M17 23 C17 15 22 13 25 16 C27 12 31 12 32 15 C33 12 37 12 39 16 C42 13 47 15 47 23 C42 18 22 18 17 23 Z" fill="#ffe08a"/>',
    iris="#3a8fd8", torso=f'<path d="M25 36 L39 36 L45 54 L19 54 Z" fill="#fff"/><path d="M24 44 L40 44" fill="none" stroke="#ffd84a" stroke-width="1.6"/>',
    sleeve="#fff", hand=SKIN, leg=SKIN, legw=4),
 "vampir": dict(
    back=CAPE("#2b2a3a", "#a0283a") + '<path d="M22 37 L14 25 L26 33 Z M42 37 L50 25 L38 33 Z" fill="#a0283a"/>' + HAIR_SHORT("#3a3a48"),
    head=face("#f1e6f0") + '<path d="M17 21 C18 11 46 11 47 21 C42 15 36 15 32 21 C28 15 22 15 17 21 Z" fill="#3a3a48"/>',
    iris="#d8342c", mouth_fn=FANG,
    torso=f'<path d="{SHIRT}" fill="#3a3a48"/><path d="M29 36 L35 36 L32 42 Z" fill="#fff" stroke-width="1"/><circle cx="32" cy="40" r="1.6" fill="#d8342c" stroke-width="0.6"/>',
    sleeve="#3a3a48", hand="#f1e6f0", leg="#3a3a48", legw=6),
 "tengu": dict(
    back=WINGS("#3a3a48") + '<path d="M14 26 L9 18 L16 18 L13 9 L22 13 L32 6 L42 13 L51 9 L48 18 L55 18 L50 26 Z" fill="#f4f4f4"/>',
    head=face("#e5483b") + '<path d="M28 11 L32 6 L36 11 L36 14 L28 14 Z" fill="#2b2a3a"/>',
    top='<path d="M31 28 C36 27 44 29 48 31 C44 33 36 33 31 32 Z" fill="#e5483b"/>', mouth=False, blush=False, brows=True,
    torso=f'<path d="{SHIRT}" fill="#fff"/><circle cx="28" cy="40" r="1.8" fill="#ff8fc1" stroke-width="0.8"/>'
          '<circle cx="32" cy="40" r="1.8" fill="#ff8fc1" stroke-width="0.8"/><circle cx="36" cy="40" r="1.8" fill="#ff8fc1" stroke-width="0.8"/>',
    sleeve="#fff", sleevew=6, hand="#e5483b", leg="#6c6f80", legw=6, item=FAN),
 "oni": dict(
    back='<path d="M15 25 C13 12 22 8 32 8 C42 8 51 12 49 25 Z" fill="#3a3a48"/>',
    head=face("#6c8fd8") + '<path d="M17 22 C18 14 24 13 26 17 C28 12 36 12 38 17 C40 13 46 14 47 22 C42 18 22 18 17 22 Z" fill="#3a3a48"/>'
         '<path d="M21 15 L18 3 L26 12 Z M43 15 L46 3 L38 12 Z" fill="#ffd84a"/>',
    mouth_fn=FANG, brows=True, blush=False,
    torso='<path d="M25 36 L39 36 L41 46 L23 46 Z" fill="#6c8fd8"/><path d="M22 45 L42 45 L43 52 L21 52 Z" fill="#ffd84a"/>'
          '<path d="M26 45 L27 52 M32 45 L32.5 52 M38 45 L37 52" fill="none" stroke-width="1.6"/>',
    sleeve="#6c8fd8", sleevew=6, hand="#6c8fd8", leg="#6c8fd8", legw=6, item=CLUB),
})

A.update({
 "kappa": dict(eyes=[(25, 24), (39, 24)], body=
    '<ellipse cx="32" cy="48" rx="15" ry="11" fill="#5a8f3a"/><path d="M20 58 C18 46 22 38 32 38 C42 38 46 46 44 58 Z" fill="#7cc95a"/>'
    '<path d="M26 57 C26 48 28 44 32 44 C36 44 38 48 38 57 Z" fill="#f3e2a0"/><ellipse cx="32" cy="25" rx="16" ry="14" fill="#7cc95a"/>'
    '<path d="M17 18 L20 12 L23 16 L26 10 L29 15 L32 9 L35 15 L38 10 L41 16 L44 12 L47 18 C40 14 24 14 17 18 Z" fill="#2f5a2a"/>'
    '<ellipse cx="32" cy="12" rx="8" ry="3" fill="#cfeaff" stroke-width="1"/><path d="M28 30 Q32 36 36 30 Q32 28 28 30 Z" fill="#f5c542"/>'),
 "karakasa": dict(eyes=[(30, 19)], body=
    '<rect x="30.5" y="34" width="3" height="18" fill="#d9b26a"/><rect x="26" y="52" width="12" height="3" rx="1" fill="#8a6a4e"/>'
    '<path d="M32 6 L32 1" fill="none" stroke-width="1.6"/>'
    '<path d="M6 36 Q32 0 58 36 Q51 31 45 36 Q38.5 31 32 36 Q25.5 31 19 36 Q12.5 31 6 36 Z" fill="#9b6dff"/>'
    '<path d="M32 6 L19 34 M32 6 L45 34" fill="none" stroke-width="0.8"/>'
    '<path d="M25 26 Q31 29 37 26" fill="none" stroke-width="1.4"/><path d="M32 27.5 Q33 34 36.5 27" fill="#ff7fb0" stroke-width="1"/>'),
 "daruma": dict(eyes=[(26.5, 27), (37.5, 27)], body=
    '<path d="M12 38 C12 8 52 8 52 38 C52 60 12 60 12 38 Z" fill="#e5383b"/>'
    '<path d="M18 27 C18 16 46 16 46 27 C46 38 18 38 18 27 Z" fill="#fff"/>'
    '<path d="M21 21.5 Q25 18.5 29 21.5 M35 21.5 Q39 18.5 43 21.5" fill="none" stroke-width="2.4"/>'
    '<path d="M25 33.5 Q28.5 31 32 33.5 Q35.5 31 39 33.5" fill="none" stroke-width="2"/>'
    '<path d="M22 46 Q32 52 42 46" fill="none" stroke="#ffd84a" stroke-width="2.4"/>'),
 "mondhase": dict(eyes=[(26, 27), (38, 27)], body=
    '<path d="M50 4 A8 8 0 1 0 58 14 A6 6 0 1 1 50 4 Z" fill="#ffd84a" stroke-width="1"/>'
    '<path d="M22 20 C16 4 22 0 26 4 C28 8 28 14 27 20 Z M42 20 C48 4 42 0 38 4 C36 8 36 14 37 20 Z" fill="#fff"/>'
    '<path d="M23 16 C20 7 23 4 25 6 C26 9 26 13 25.5 16 Z M41 16 C44 7 41 4 39 6 C38 9 38 13 38.5 16 Z" fill="#ff9fb2" stroke="none"/>'
    '<path d="M18 58 C16 46 21 38 32 38 C43 38 48 46 46 58 Z" fill="#fff"/><ellipse cx="32" cy="28" rx="15" ry="12" fill="#fff"/>'
    '<ellipse cx="32" cy="48" rx="7" ry="5" fill="#fdf6e8"/>'
    '<path d="M30.5 31 L33.5 31 L32 32.5 Z" fill="#ff9fb2" stroke-width="0.8"/>'
    '<path d="M32 32.5 Q30.5 34.5 29 33.5 M32 32.5 Q33.5 34.5 35 33.5" fill="none" stroke-width="1.1"/>'
    '<ellipse cx="21" cy="32" rx="2.6" ry="1.4" fill="#ff9fb2" stroke="none"/><ellipse cx="43" cy="32" rx="2.6" ry="1.4" fill="#ff9fb2" stroke="none"/>'),
 "drache": dict(eyes=[(27, 28), (38, 28)], body=
    '<path d="M10 52 L3 47 L7 54 L2 58 L11 56 Z" fill="#ffd84a"/>'
    '<circle cx="14" cy="52" r="5" fill="#3fb59a"/><circle cx="23" cy="54" r="6" fill="#3fb59a"/><circle cx="34" cy="53" r="6.5" fill="#3fb59a"/>'
    '<circle cx="44" cy="48" r="6.5" fill="#3fb59a"/>'
    '<path d="M44 22 L53 19 L49 26 L55 29 L46 31 Z" fill="#e5383b"/>'
    '<path d="M24 18 L19 6 L23 8 L26 4 L27 16 Z M41 17 L46 5 L42 7 L39 3 L37 15 Z" fill="#ffd84a"/>'
    '<path d="M20 30 C20 16 44 14 46 26 C47 36 40 42 32 42 C24 42 20 38 20 30 Z" fill="#3fb59a"/>'
    '<ellipse cx="33" cy="36" rx="9" ry="5" fill="#9fe6cf"/>'
    '<circle cx="30" cy="35" r="0.9" fill="#2b2a3a" stroke="none"/><circle cx="36" cy="35" r="0.9" fill="#2b2a3a" stroke="none"/>'
    '<path d="M25 37 C18 38 14 34 10 36 M41 37 C48 38 52 34 56 36" fill="none" stroke-width="1.2"/>'),
 "shiba": dict(eyes=[(25, 25), (39, 25)], body=
    '<path d="M44 46 C54 46 56 36 50 34 C46 34 46 40 50 40 C52 42 48 44 44 42 Z" fill="#e0a15a"/>'
    '<path d="M19 58 C17 46 22 38 32 38 C42 38 47 46 45 58 Z" fill="#e0a15a"/>'
    '<path d="M26 58 C26 48 28 43 32 43 C36 43 38 48 38 58 Z" fill="#fff6ea"/>'
    '<path d="M14 18 L18 4 L27 13 Z M50 18 L46 4 L37 13 Z" fill="#e0a15a"/><ellipse cx="32" cy="26" rx="18" ry="14" fill="#e0a15a"/>'
    '<path d="M16 29 C20 40 44 40 48 29 C44 34 38 33 32 33 C26 33 20 34 16 29 Z" fill="#fff6ea" stroke="none"/>'
    '<ellipse cx="25" cy="19" rx="2" ry="1.2" fill="#fff6ea" stroke="none"/><ellipse cx="39" cy="19" rx="2" ry="1.2" fill="#fff6ea" stroke="none"/>'
    '<ellipse cx="32" cy="30" rx="2.2" ry="1.5" fill="#2b2a3a" stroke="none"/>'
    '<path d="M32 31.5 Q30 34 28.5 33 M32 31.5 Q34 34 35.5 33" fill="none" stroke-width="1.2"/>'),
 "panda": dict(eyes=[(25, 25), (39, 25)], line="#ffffff", body=
    '<circle cx="17" cy="13" r="5.5" fill="#2b2a3a"/><circle cx="47" cy="13" r="5.5" fill="#2b2a3a"/>'
    '<path d="M18 58 C16 46 21 38 32 38 C43 38 48 46 46 58 Z" fill="#fff"/>'
    '<path d="M18 44 C14 48 16 54 22 52 L24 44 Z M46 44 C50 48 48 54 42 52 L40 44 Z" fill="#2b2a3a"/>'
    '<ellipse cx="24" cy="57" rx="5" ry="3.5" fill="#2b2a3a"/><ellipse cx="40" cy="57" rx="5" ry="3.5" fill="#2b2a3a"/>'
    '<ellipse cx="32" cy="25" rx="18" ry="15" fill="#fff"/>'
    '<ellipse cx="25" cy="25" rx="4.5" ry="5.5" fill="#2b2a3a" stroke="none" transform="rotate(25 25 25)"/>'
    '<ellipse cx="39" cy="25" rx="4.5" ry="5.5" fill="#2b2a3a" stroke="none" transform="rotate(-25 39 25)"/>'
    '<ellipse cx="32" cy="31" rx="2" ry="1.4" fill="#2b2a3a" stroke="none"/>'
    '<path d="M32 32.4 Q30.5 34.4 29 33.4 M32 32.4 Q33.5 34.4 35 33.4" fill="none" stroke-width="1.1"/>'),
 "koi": dict(eyes=[(17, 34)], body=
    '<path d="M14 54 Q20 50 26 54 Q32 50 38 54 Q44 50 50 54" fill="none" stroke="#3d9ad6" stroke-width="1.6"/>'
    '<path d="M48 32 L60 24 L57 33 L60 42 Z" fill="#fff"/><path d="M26 27 L32 20 L38 27 Z" fill="#e5383b"/>'
    '<path d="M10 40 C14 26 36 22 50 32 C44 42 24 48 10 40 Z" fill="#fff"/><path d="M28 42 L24 50 L34 44 Z" fill="#fff"/>'
    '<path d="M22 30 C26 26 32 26 34 30 C30 34 25 34 22 30 Z" fill="#e5383b" stroke="none"/>'
    '<path d="M37 31 C41 29 45 31 47 33 C43 36 39 35 37 31 Z" fill="#e5383b" stroke="none"/>'
    '<path d="M10 39 Q12 41 14 40" fill="none" stroke-width="1.2"/><path d="M11 41 Q8 44 9 47" fill="none" stroke-width="0.9"/>'),
 "taiyaki": dict(eyes=[(17, 31)], body=
    '<path d="M8 34 C12 20 34 16 46 28 L58 20 L56 34 L58 48 L46 40 C34 52 12 48 8 34 Z" fill="#d99a4a"/>'
    '<path d="M30 30 q3 3 6 0 M30 37 q3 3 6 0 M37 33.5 q3 3 6 0" fill="none" stroke="#a8682a" stroke-width="1.1"/>'
    '<path d="M10 38 Q13 40 15 38" fill="none" stroke-width="1.2"/>'
    '<ellipse cx="21" cy="37" rx="2.4" ry="1.3" fill="#ff9fb2" stroke="none"/>'),
 "dango": dict(eyes=[(28.5, 30), (35.5, 30)], body=
    '<path d="M32 4 L32 60" fill="none" stroke="#c9a06a" stroke-width="2.5"/>'
    '<circle cx="32" cy="14" r="9" fill="#ff9fb2"/><circle cx="32" cy="31" r="9" fill="#fff8f0"/><circle cx="32" cy="48" r="9" fill="#9fd88a"/>'
    '<path d="M30.5 34.5 Q32 36 33.5 34.5" fill="none" stroke-width="1.2"/>'
    '<ellipse cx="25.5" cy="34" rx="2" ry="1.1" fill="#ff9fb2" stroke="none"/><ellipse cx="38.5" cy="34" rx="2" ry="1.1" fill="#ff9fb2" stroke="none"/>'),
 "sushi": dict(eyes=[(25, 43), (39, 43)], body=
    '<path d="M10 40 C10 32 54 32 54 40 L54 50 C54 56 10 56 10 50 Z" fill="#fff"/>'
    '<path d="M6 36 C8 22 56 22 58 36 C50 32 14 32 6 36 Z" fill="#ff9a5a"/>'
    '<path d="M18 27 L22 34 M28 25 L31 33 M38 25 L40 33 M48 27 L49 34" fill="none" stroke="#fff3e8" stroke-width="1.6"/>'
    '<path d="M30 47.5 Q32 49.5 34 47.5" fill="none" stroke-width="1.3"/>'
    '<ellipse cx="20" cy="47" rx="2.6" ry="1.4" fill="#ff9fb2" stroke="none"/><ellipse cx="44" cy="47" rx="2.6" ry="1.4" fill="#ff9fb2" stroke="none"/>'),
})

# Wasserfiguren (Nutzerwunsch 2026-11-25): stehen nur im Wasser (places = ["water"] im Stil), Wellen vorn im Bild
WAVES = lambda y: (f'<path d="M6 {y} Q12 {y-5} 18 {y} Q25 {y-5} 32 {y} Q39 {y-5} 46 {y} Q52 {y-5} 58 {y} L56 {y+7} L8 {y+7} Z" fill="#6ec3e8"/>'
                   f'<path d="M10 {y-1} Q13 {y-4} 16 {y-2} M38 {y-1} Q41 {y-4} 44 {y-2}" fill="none" stroke="#fff" stroke-width="1.4"/>')
WAVELINE = lambda y: f'<path d="M8 {y} Q14 {y-4} 20 {y} Q26 {y-4} 32 {y} Q38 {y-4} 44 {y} Q50 {y-4} 56 {y}" fill="none" stroke="#3d9ad6" stroke-width="1.6"/>'
A.update({
 "umibozu": dict(eyes=[(25, 25), (39, 25)], line="#ffffff", body=
    '<path d="M11 54 C10 30 17 8 32 8 C47 8 54 30 53 54 Z" fill="#3d4a66"/>'
    '<ellipse cx="23" cy="17" rx="5" ry="2.6" fill="#6a7a9c" stroke="none" transform="rotate(-35 23 17)"/>'
    '<path d="M27 35 Q32 38.5 37 35" fill="none" stroke="#cfd8ea" stroke-width="1.5"/>' + WAVES(50)),
 "amabie": dict(eyes=[(27.5, 21), (36.5, 21)], body=
    '<path d="M14 22 C12 8 22 4 32 4 C42 4 52 8 50 22 C54 34 52 44 49 50 L40 42 L24 42 L15 50 C12 44 10 34 14 22 Z" fill="#7fd6c8"/>'
    '<path d="M22 45 L17 55 L26 53 Z M29 46 L28 56 L36 56 L35 46 Z M42 45 L47 55 L38 53 Z" fill="#f0789a"/>'
    '<path d="M23 32 C25 30 39 30 41 32 L43 47 L21 47 Z" fill="#ff9fb2"/>'
    '<path d="M25 37 q2 2 3.5 0 q2 2 3.5 0 q2 2 3.5 0 q2 2 3.5 0 M23.5 42 q2 2 3.5 0 q2 2 3.5 0 q2 2 3.5 0 q2 2 3.5 0 q2 2 3.5 0" '
    'fill="none" stroke="#e0567c" stroke-width="0.9"/>'
    '<ellipse cx="32" cy="22" rx="11" ry="10" fill="#fff4ea"/>'
    '<path d="M20 19 C21 9 43 9 44 19 C40 14 36 16 32 12.5 C28 16 24 14 20 19 Z" fill="#7fd6c8"/>'
    '<path d="M28 27.5 L32 25.3 L36 27.5 L32 31.5 Z" fill="#ffb347" stroke-width="1"/><path d="M28 27.5 L36 27.5" fill="none" stroke-width="0.8"/>'
    '<ellipse cx="24" cy="26" rx="2.2" ry="1.2" fill="#ff9fb2" stroke="none"/><ellipse cx="40" cy="26" rx="2.2" ry="1.2" fill="#ff9fb2" stroke="none"/>'
    + WAVELINE(58)),
 "kawauso": dict(eyes=[(25, 23), (39, 23)], body=
    '<path d="M19 56 C16 42 22 34 32 34 C42 34 48 42 45 56 Z" fill="#8a5a3a"/>'
    '<path d="M26 56 C26 46 28 40 32 40 C36 40 38 46 38 56 Z" fill="#f3e2c8"/>'
    '<path d="M22 45 C26 41 36 41 40 45 L45 41.5 L44 48.5 L40 46 C36 49.5 26 49.5 22 45 Z" fill="#ff9a5a"/>'
    '<circle cx="25.5" cy="44.3" r="0.9" fill="#2b2a3a" stroke="none"/>'
    '<ellipse cx="22" cy="46" rx="3" ry="2.4" fill="#8a5a3a"/><ellipse cx="41" cy="46.5" rx="3" ry="2.4" fill="#8a5a3a"/>'
    '<circle cx="15" cy="20" r="2.6" fill="#8a5a3a"/><circle cx="49" cy="20" r="2.6" fill="#8a5a3a"/>'
    '<ellipse cx="32" cy="24" rx="18" ry="11.5" fill="#8a5a3a"/>'
    '<path d="M15 25 C19 38 45 38 49 25 C45 29 40 28 32 28 C24 28 19 29 15 25 Z" fill="#f3e2c8" stroke="none"/>'
    '<ellipse cx="32" cy="27.5" rx="2.6" ry="1.7" fill="#2b2a3a" stroke="none"/>'
    '<path d="M32 29 Q30.5 31.5 29 30.5 M32 29 Q33.5 31.5 35 30.5" fill="none" stroke-width="1.1"/>'
    '<path d="M23 30 L13 28.5 M23 32 L14 33 M41 30 L51 28.5 M41 32 L50 33" fill="none" stroke-width="0.8"/>' + WAVES(51)),
 "ruderboot": dict(eyes=[(27.5, 22), (36.5, 22)], body=
    '<path d="M24 40 L5 53 M40 40 L59 53" fill="none" stroke="#8a5a3a" stroke-width="2.2"/>'
    '<ellipse cx="6" cy="53" rx="3.5" ry="1.8" fill="#c9844a" transform="rotate(-34 6 53)"/>'
    '<ellipse cx="58" cy="53" rx="3.5" ry="1.8" fill="#c9844a" transform="rotate(34 58 53)"/>'
    '<path d="M25 33 L39 33 L41 45 L23 45 Z" fill="#5aa0e6"/>'
    '<circle cx="24" cy="40" r="2.4" fill="' + SKIN + '"/><circle cx="40" cy="40" r="2.4" fill="' + SKIN + '"/>'
    '<ellipse cx="32" cy="22" rx="11" ry="10" fill="' + SKIN + '"/>'
    '<path d="M21 21 C20 11 26 9 32 9 C38 9 44 11 43 21 C40 15 35 17 32 14 C29 17 24 15 21 21 Z" fill="#6b4a32"/>'
    '<path d="M30 27.5 Q32 29.5 34 27.5" fill="none" stroke-width="1.2"/>'
    '<ellipse cx="24.5" cy="26" rx="2.2" ry="1.2" fill="' + BLUSH + '" stroke="none"/><ellipse cx="39.5" cy="26" rx="2.2" ry="1.2" fill="' + BLUSH + '" stroke="none"/>'
    '<path d="M8 44 L56 44 L51 55 L13 55 Z" fill="#c9844a"/><path d="M10.5 49 L53.5 49" fill="none" stroke="#9a5f30" stroke-width="1.2"/>'
    + WAVELINE(59)),
})

DESC.update({
 "maid": "Café-Maid mit Tablett (Genre-Archetyp)", "kendo": "Kendō-Kämpfer mit Schutzhelm (Genre-Archetyp)",
 "yankee": "Delinquent mit Tolle und langem Mantel (Genre-Archetyp)", "schulsprecherin": "Schulsprecherin mit Brille und Klemmbrett (Genre-Archetyp)",
 "lehrer": "Lehrer mit Zeigestock (Genre-Archetyp)", "baseball": "Baseball-Junge (Genre-Archetyp)", "ramenkoch": "Ramen-Koch mit Schale (Genre-Archetyp)",
 "mangaka": "Mangaka mit Zeichenfeder (Genre-Archetyp)", "butler": "Butler mit Teetasse (Genre-Archetyp)",
 "onmyoji": "Onmyōji mit Papiertalisman (Genre-Archetyp)", "moench": "Wandermönch mit Strohhut und Stab (Genre-Archetyp)",
 "nekomimi": "Katzenmädchen (Genre-Archetyp)", "schwertkaempfer": "Schwertkämpfer mit Umhang (Fantasy-Archetyp)",
 "magier": "Magier mit Spitzhut und Stab (Fantasy-Archetyp)", "ritterin": "Ritterin (Fantasy-Archetyp)",
 "daemonenkoenig": "Mini-Dämonenkönig (Fantasy-Archetyp)", "engel": "Engel (Fantasy-Archetyp)", "vampir": "Vampir-Chibi (Fantasy-Archetyp)",
 "tengu": "Tengu mit Blattfächer (Yōkai, Volksmotiv)", "oni": "Oni mit Keule (Yōkai, Volksmotiv)", "kappa": "Kappa (Yōkai, Volksmotiv)",
 "karakasa": "Schirmgeist (Yōkai, Volksmotiv)", "daruma": "Daruma (Volksmotiv)", "mondhase": "Mondhase mit Mochi (Volksmotiv)",
 "drache": "Östlicher Drache (Volksmotiv)", "shiba": "Shiba-Hund", "panda": "Panda", "koi": "Koi", "taiyaki": "Taiyaki (Chibi-Food)",
 "dango": "Dango (Chibi-Food)", "sushi": "Nigiri-Sushi (Chibi-Food)",
 "umibozu": "Umibōzu, Meermönch (Yōkai, Volksmotiv)", "amabie": "Amabie, Glücksbringer aus dem Meer (Yōkai, Volksmotiv)",
 "kawauso": "Kawauso, Fischotter mit Fisch (Yōkai, Volksmotiv)", "ruderboot": "Ruderboot am Parkteich (Genre-Szene)",
})

import shutil
for d in OUT.iterdir():
    if d.is_dir():
        shutil.rmtree(d)

for n, f in H.items():
    for p, spec in POSES.items():
        write(n, p, DESC[n], human(f, spec))
for n, a in A.items():
    for p in ("sitzt", "schlaeft", "springt"):
        write(n, p, DESC[n], animal(a, p))

# --- Fabelwesen für Historisch und Kupferstich (Nutzerwunsch 2026-11-25) ----------------------------------------------
# Nach alten Wappen und kolorierten Holzschnitten (16. Jh.), nicht Chibi: schlanke Leiber, Profilköpfe, Klauen, Feuer in
# Strähnen, helle Glanzstreifen und Querlinien wie im Wappen. Jedes Wesen zweimal: <name> handkoloriert (Historisch),
# <name>-sepia in Sepia-Flächen (Kupferstich). Leiber als verjüngter Schlauch entlang einer Mittellinie (tube()).
PAL = {"": dict(body="#4f8a3c", top="#86b263", light="#f4efd8", belly="#3c6e2e", mouth="#7a1f18", fire="#d8392b", fire2="#f08a2a", claw="#f4efd8",
                green="#4f8a3c", green_l="#86b263", red="#b8473a", red_l="#d9806a", ochre="#c99a3a", ochre_l="#e6c675",
                blue="#5f86a8", blue_l="#a9c4d6", brown="#7d5a3a", brown_l="#a8855e", grey="#8f8a80", grey_l="#c4bfb2",
                white="#e9dfc6", white_l="#fbf6e6", skin="#e8b894", skin_l="#f5d6bc", dark="#3a2c22"),
       "-sepia": dict(body="#8c6440", top="#b8956a", light="#f0e2c0", belly="#6e4b2e", mouth="#4a2a14", fire="#9a5a32", fire2="#c99a64", claw="#f0e2c0",
                      green="#8c6440", green_l="#b8956a", red="#7a4628", red_l="#a8754e", ochre="#b08452", ochre_l="#d4b282",
                      blue="#9aa592", blue_l="#c4ccb4", brown="#6e4b2e", brown_l="#957049", grey="#a08a6a", grey_l="#c8b490",
                      white="#e6d4ae", white_l="#f7ecd2", skin="#d9b48a", skin_l="#ead0ac", dark="#3b2614"),
       # Kupferplatte: dunkle Kupferflächen, Glanz wie frisch gestochen (Schraffur = helle Tusche), Blau als Grünspan
       "-kupfer": dict(body="#5a3420", top="#7a4a2c", light="#f0c890", belly="#3e2416", mouth="#1e120a", fire="#c8783c", fire2="#f0b070", claw="#f0c890",
                       green="#5a3420", green_l="#7a4a2c", red="#6e2e1c", red_l="#94503a", ochre="#7a5424", ochre_l="#a87a3e",
                       blue="#2f5a50", blue_l="#4f8070", brown="#4a2c1a", brown_l="#6a4428", grey="#4e3e32", grey_l="#6e5a48",
                       white="#8a6a4a", white_l="#b08a60", skin="#7a5034", skin_l="#9a6a46", dark="#1a0f08")}
FSHADOW = '<ellipse cx="30" cy="61" rx="13" ry="2" fill="#3b2614" fill-opacity="0.22" stroke="none"/>'
tint = lambda c, k: dict(c, body=c[k], top=c[k + "_l"])   # Leibfarbe wechseln (body/top), z. B. tint(c, "ochre")

ID = {"p": "", "n": 0}   # eindeutige Ids für clipPath je Bild (poi_sprite setzt alle Bilder in ein SVG)

def hat(d, fill, region=None, ang=45, gap=1.5, w=0.35, attrs=""):
    """Fläche d mit Kontur und Holzschnitt-Schraffur: parallele Linien im Winkel ang, beschnitten auf d und (falls
    angegeben) auf region, die Schattenseite."""
    ID["n"] += 1
    i = f'{ID["p"]}{ID["n"]}'
    lines = "".join(f"M-40 {-40 + k * gap:.2f}H104" for k in range(int(144 / gap)))
    g = f'<path d="{lines}" fill="none" stroke-width="{w}" transform="rotate({ang} 32 32)"/>'
    if region:
        g = f'<clipPath id="r{i}"><path d="{region}"/></clipPath><g clip-path="url(#r{i})">{g}</g>'
    return f'<path d="{d}" fill="{fill}"{attrs}/><clipPath id="c{i}"><path d="{d}"/></clipPath><g clip-path="url(#c{i})">{g}</g>'

below = lambda y: f"M-20 {y} H90 V90 H-20 Z"
right = lambda x: f"M{x} -20 H90 V90 H{x} Z"
left = lambda x: f"M-20 -20 H{x} V90 H-20 Z"
def spline(pts, n=8):
    """Catmull-Rom durch pts, n Punkte je Abschnitt."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in (0, 1)))
    return out + [pts[-1]]

def _frame(pts, ws, n=8):
    c = spline(pts, n)
    w = [ws[min(i // n, len(ws) - 1)] + (ws[min(i // n + 1, len(ws) - 1)] - ws[min(i // n, len(ws) - 1)]) * (i % n) / n for i in range(len(c))]
    nrm = []
    for i in range(len(c)):
        a, b = c[max(i - 1, 0)], c[min(i + 1, len(c) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; l = math.hypot(dx, dy) or 1
        nrm.append((-dy / l, dx / l))
    return c, w, nrm

def tube(pts, ws, fill, side=0.0, scale=1.0, attrs=""):
    """Gefüllter Schlauch durch pts mit Breiten ws je Punkt; side/scale: schmalerer Streifen, zur Seite versetzt."""
    c, w, nrm = _frame(pts, ws)
    L = [(x + nx * (side * wi / 2 + wi * scale / 2), y + ny * (side * wi / 2 + wi * scale / 2)) for (x, y), wi, (nx, ny) in zip(c, w, nrm)]
    R = [(x + nx * (side * wi / 2 - wi * scale / 2), y + ny * (side * wi / 2 - wi * scale / 2)) for (x, y), wi, (nx, ny) in zip(c, w, nrm)]
    # runde Enden: Halbkreis um die Endpunkte (sonst wirken dicke Leiber wie abgeschnittene Kisten)
    def cap(i, sgn):
        (x, y), wi, (nx, ny) = c[i], w[i], nrm[i]
        cx, cy, r = x + nx * side * wi / 2, y + ny * side * wi / 2, wi * scale / 2
        return [(cx + r * (nx * math.cos(t) + sgn * ny * math.sin(t)), cy + r * (ny * math.cos(t) - sgn * nx * math.sin(t)))
                for t in (k * math.pi / 8 for k in range(1, 8))]
    poly = L + cap(len(c) - 1, -1)[::-1] + R[::-1] + cap(0, 1)
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in poly) + " Z"
    return f'<path d="{d}" fill="{fill}"{attrs}/>'

def hatch(pts, ws, side, t0, t1, peak=0.7):
    """Schraffurlinie wie im Holzschnitt: folgt dem Leib (Versatz side × halbe Breite), schwillt an und ab.
    Fläche in currentColor (= Tusche, siehe poi_sprite)."""
    c, w, nrm = _frame(pts, ws)
    i0, i1 = int(t0 * (len(c) - 1)), int(t1 * (len(c) - 1))
    L, R = [], []
    for i in range(i0, i1 + 1):
        u = (i - i0) / max(i1 - i0, 1)
        (x, y), wi, (nx, ny) = c[i], w[i], nrm[i]
        o, h = side * wi / 2, peak * math.sin(math.pi * u) / 2
        L.append((x + nx * (o + h), y + ny * (o + h))); R.append((x + nx * (o - h), y + ny * (o - h)))
    return '<path d="M' + " L".join(f"{x:.2f} {y:.2f}" for x, y in L + R[::-1]) + ' Z" fill="currentColor" stroke="none"/>'

HATCH = [(-0.3, 0.06, 0.7, 0.22), (-0.45, 0.02, 0.85, 0.26), (-0.6, 0.05, 0.92, 0.3), (-0.75, 0.02, 0.97, 0.34),
         (-0.88, 0.0, 0.99, 0.36)]

def scales(pts, ws, rows=(-0.7, -0.42, -0.14, 0.14, 0.42, 0.7), size=0.085):
    """Schuppen wie im Holzschnitt: kleine Bögen (offen zum Kopf) in versetzten Reihen über dem Leib; Bauchseite
    kräftiger, Oberseite fein."""
    c, w, nrm = _frame(pts, ws, n=16)
    d_top, d_bot, run, col = "", "", 0.0, 0
    for i in range(1, len(c)):
        run += math.dist(c[i], c[i - 1])
        r = max(w[i] * size, 0.6)
        if run < 1.7 * r or w[i] < 2.5:
            continue
        run, col = 0.0, col + 1
        (x, y), (nx, ny) = c[i], nrm[i]
        tx, ty = ny, -nx                                   # Richtung zum Schwanz (pts laufen Kopf -> Schwanz): Bogen zeigt dorthin
        for k, v in enumerate(rows):
            v += (0.14 if col % 2 else 0) - 0.07
            px, py = x + nx * v * w[i] / 2, y + ny * v * w[i] / 2
            a = (px + nx * r, py + ny * r); b = (px - nx * r, py - ny * r)
            q = (px + tx * r * 2.2, py + ty * r * 2.2)
            arc = f"M{a[0]:.1f} {a[1]:.1f} Q{q[0]:.1f} {q[1]:.1f} {b[0]:.1f} {b[1]:.1f} "
            if v < 0: d_bot += arc
            else: d_top += arc
    return (f'<path d="{d_top}" fill="none" stroke-width="0.3"/>' + f'<path d="{d_bot}" fill="none" stroke-width="0.45"/>')

def creature(c, pts, ws, behind=(), front=(), skin="scales", extra=""):
    """Leib (Schlauch) mit Beinen. behind: Beine ganz hinter dem Leib. front: Beine vor dem Leib, nahtlos angesetzt:
    ihre Tuschekontur liegt hinter dem Leib (nur außerhalb sichtbar), ihre Fläche über dem Leib (verdeckt dessen Kontur
    am Ansatz), darüber Schuppen und Schraffur des Leibs, die so ohne Kante ins Bein übergehen."""
    tex = "".join(hatch(pts, ws, *h) for h in HATCH) + (scales(pts, ws) if skin == "scales" else "") + extra
    return ("".join(l["back"] + l["front"] for l in behind) + "".join(l["back"] for l in front)
            + tube(pts, ws, c["body"]) + tube(pts[:-2], ws, c["top"], side=0.42, scale=0.42, attrs=' stroke="none"')
            + "".join(l["front"] for l in front) + tex)

def claws(c, x, y, a=0):
    """Pfote ohne eigene Kontur (sitzt auf der Tuschefläche des Beins), drei helle Krallen mit feinem Rand."""
    return (f'<g transform="translate({x} {y}) rotate({a})"><path d="M-0.5 -2.6 C-3 -5 -6.5 -5.5 -9 -4 C-6.5 -3.4 -4.5 -2 -2.6 -0.2 Z M-1.5 -0.9 C-4.5 -1.6 -7.5 -0.8 -9.5 1.2 C-7 0.9 -4.5 1.1 -1.8 1.6 Z M-1 1.4 C-3.5 2.6 -5.5 4.6 -6.5 7 C-4.5 5.4 -2.5 4.2 0.2 3.2 Z" '
            f'fill="{c["claw"]}" stroke-width="0.5"/><ellipse cx="0.5" cy="0" rx="3.3" ry="3.1" fill="currentColor" stroke="none"/>'
            f'<ellipse cx="0.5" cy="0" rx="2.6" ry="2.4" fill="{c["body"]}" stroke="none"/></g>')

def foot(c, kind, x, y, a):
    if kind == "claw":
        return claws(c, x, y, a)
    if kind == "hoof":   # gespaltener Huf, dunkel
        return (f'<g transform="translate({x} {y}) rotate({a})"><path d="M-2.2 -1.5 L2.2 -1.5 L3 2 L-3 2 Z" fill="{c["dark"]}" stroke-width="0.6"/>'
                f'<path d="M0 0 V2" fill="none" stroke="{c["light"]}" stroke-width="0.5"/></g>')
    if kind == "hand":
        return f'<ellipse cx="{x}" cy="{y}" rx="2" ry="1.8" fill="{c["skin"]}" stroke-width="0.6"/>'
    if kind == "paw":    # Tatze, Krallen klein
        return (f'<g transform="translate({x} {y}) rotate({a})"><ellipse cx="0" cy="0" rx="3.4" ry="2.4" fill="{c["body"]}" stroke-width="0.7"/>'
                f'<path d="M-2 -1 l-1.6 -0.4 M-2.4 0.4 l-1.8 0.2 M-2 1.6 l-1.5 0.8" fill="none" stroke-width="0.5"/></g>')
    return ""

def leg(c, pts, a, ws=(6.5, 5, 4), kind="claw", skin="scales"):
    """Bein ohne eigene Kontur: back = Tuschefläche, die zur Schulter hin auf die Beinbreite schrumpft (Kontur 0 an
    der Schulter), front = Fläche, Schraffur, Schuppen, Fuß (claw, hoof, hand, paw). Zusammensetzen über creature()."""
    out = [w + e for w, e in zip(ws, (0, 1.6, 2.4))]
    return {"back": tube(pts, out, "currentColor", attrs=' stroke="none"'),
            "front": (tube(pts, list(ws), c["body"], attrs=' stroke="none"')
                      + hatch(pts, list(ws), -0.45, 0.2, 0.9, 0.25) + hatch(pts, list(ws), -0.75, 0.1, 0.95, 0.3)
                      + (scales(pts, list(ws), rows=(-0.5, 0, 0.5), size=0.13) if skin == "scales" else "")
                      + foot(c, kind, *pts[-1], a))}

HEAD_SCALE = 0.8   # Kopf kleiner als der Leib, wie bei Gessner

def lhead(c, x, y, a=0, open_=True, eye=True, flame=False, horns=True, fl_scale=1.0, tongue=True):
    """Profilkopf (Wolfsschnauze, zwei Hörner) mit Ursprung am Halsansatz, Blick nach +x; schraffiert wie der Leib:
    An- und abschwellende Linien auf der unteren Kopfhälfte (Schatten), feine Falten an Stirn und Schnauze."""
    mid = [(-2, -2), (8, -3.2), (20, -3.2)]
    shade = "".join(hatch(mid, [9, 8, 4.5], *h) for h in ((0.25, 0.05, 0.9, 0.28), (0.5, 0.0, 0.95, 0.32), (0.75, 0.0, 0.8, 0.36)))
    if open_:
        shade += hatch([(3, 4.3), (10, 5), (16, 5.2)], [3, 3, 2], 0.2, 0.0, 1, 0.3)
    if open_:
        jaw = (f'<path d="M7 -1 L18 -1.5 L17 5 L7 1.5 Z" fill="{c["mouth"]}"/>'
               f'<path d="M3 2 L8 1 L17 4.5 C17.5 6.5 15 7 12 6.8 C8 6.8 4 6.5 2 5 Z" fill="{c["body"]}"/>'
               f'<path d="M10 -1.2 l0.9 2 l0.9 -2 Z M13 -1.3 l0.9 2 l0.9 -2 Z M16 -1.4 l0.8 1.8 l0.8 -1.8 Z M11 3 l0.8 -1.6 l0.8 1.8 Z M14 4 l0.8 -1.6 l0.8 1.8 Z" fill="{c["light"]}" stroke-width="0.5"/>')
        top = "M-3 -3 C0 -9 7 -10 12 -8 C15 -7 18 -6.4 21.5 -5 C23 -4.2 22.8 -2 21 -1.6 L9 -0.8 C6 1.5 1 3 -3 3.5 Z"
    else:
        jaw = (f'<path d="M21 0 L26 1 M26 1 L28 -0.4 M26 1 L28 2.4" fill="none" stroke="{c["fire"]}" stroke-width="0.9"/>') if tongue else ""
        top = "M-3 -3 C0 -9 7 -10 12 -8 C15 -7 18 -6.4 21.5 -5 C23 -4 23 -0.5 21 0.5 C15 2.5 8 3.5 3 3.8 C0 4 -2 4 -3 3.5 Z"
    fl = ""
    if flame:
        fl = (f'<path d="M18 0 C22 -3 25 1 29 -2 C33 -5 36 -1 40 -4 C38 1 33 2 29 3 C25 4 22 4 18 3 Z" fill="{c["fire"]}"/>'
              f'<path d="M19 1 C23 0 26 2 30 0.5 C27 2.5 23 3 19 2.4 Z" fill="{c["fire2"]}" stroke="none"/>'
              f'<path d="M31 5 C34 3 36 6 40 4 C38 8 34 8 31 7 Z" fill="{c["fire"]}"/>')
        fl = f'<g transform="translate(18 1) scale({fl_scale}) translate(-18 -1)">{fl}</g>'
    ears = ('<path d="M3 -7.5 C0 -10 -3 -13 -7 -13.5 C-4 -11.5 -1 -8 1 -5.5 Z M7 -8.6 C6 -11 4 -13 1 -14 C3 -12 4.5 -10 5 -8 Z"' if horns
            else '<path d="M1 -6.5 L-1 -14 L6 -8.5 Z"')
    ey = (f'<path d="M7.5 -5.5 C9 -7 11 -7 12 -5.8 C11 -4.6 9 -4.4 7.5 -5.5 Z" fill="{c["light"]}" stroke-width="0.7"/>'
          f'<circle cx="10.2" cy="-5.6" r="0.9" fill="#1f1a14" stroke="none"/>') if eye else \
         '<path d="M7.5 -5.4 C9 -4.4 11 -4.4 12 -5.4" fill="none" stroke-width="0.9"/>'
    return (f'<g transform="translate({x} {y}) rotate({a}) scale({HEAD_SCALE})">{fl}{jaw}{ears} fill="{c["body"]}"/>'
            f'<path d="{top}" fill="{c["body"]}"/><path d="M2 -8 C7 -9.6 13 -8.6 20 -5.4" fill="none" stroke="{c["top"]}" stroke-width="1.4"/>'
            f'{shade}{ey}<path d="M20.5 -4.2 q1.2 -0.4 1.2 0.8" fill="none" stroke-width="0.7"/>'
            f'<path d="M4 -6.5 q2 -1.4 4 -0.8 M5 -4.6 q2 -1 3.4 -0.4 M13.5 -6.4 q1.5 0.4 2.6 1.4 '
            f'M14 -4.4 l0.6 1.6 M16 -4 l0.6 1.6 M18 -3.6 l0.5 1.4" fill="none" stroke-width="0.4"/></g>')

def lindwurm(c, pose):
    """Lindwurm wie im Wappen: flügelloser Schlangenleib, zwei Vorderbeine mit Klauen."""
    if pose == "speit":   # aufgerichtet im S, Feuer aus dem Maul (Wappenhaltung)
        pts = [(26, 16), (19, 22), (20, 32), (30, 37), (43, 35), (51, 43), (46, 53), (33, 56), (19, 58), (8, 56), (5, 51), (9, 49)]
        ws = [8, 10, 12, 13.5, 14, 13, 11, 8.5, 6, 4, 2.5, 1.5]
        return (creature(c, pts, ws, behind=[leg(c, [(39, 39), (31, 49), (24, 54)], 10)], front=[leg(c, [(25, 33), (17, 39), (10, 40)], -10)])
                + lhead(c, 24, 16, -12, open_=True, flame=True))
    if pose == "kriecht":   # flach in Wellen, Zunge
        pts = [(36, 38), (28, 41), (20, 47), (12, 46), (7, 50), (8, 55), (14, 57), (25, 56), (32, 58)]
        ws = [8, 10.5, 11.5, 10.5, 9, 7, 5, 2.8, 1.2]
        return (creature(c, pts, ws, behind=[leg(c, [(26, 44), (28, 51), (33, 54)], 180)], front=[leg(c, [(34, 41), (38, 48), (44, 50)], 175)])
                + lhead(c, 34, 38, 6, open_=False))
    # ruht: eingerollt, Kopf auf der Windung, Augen zu
    pts = [(28, 33), (20, 36), (14, 44), (18, 53), (31, 57), (45, 54), (51, 45), (46, 38), (38, 40), (36, 47), (40, 50)]
    ws = [8, 10.5, 12.5, 13.5, 13.5, 12, 10, 7.5, 5, 3, 1.5]
    smoke = '<path d="M45 31 c2 -2 0 -4 2 -6 c2 -2 0 -4 2 -6" fill="none" stroke-width="0.9"/>'
    return creature(c, pts, ws, front=[leg(c, [(19, 43), (27, 48), (32, 49)], 185)]) + lhead(c, 27, 33, -4, open_=False, eye=False) + smoke

def batwing(c, root, tips, back, fill):
    """Fledermausflügel: Rippen von root zu den Spitzen, Rand dazwischen nach innen geschwungen, Haut schraffiert."""
    P = lambda q: f"{q[0]:.1f} {q[1]:.1f}"
    d = f"M{P(root)} L{P(tips[0])}"
    for a, b in zip(tips, tips[1:]):
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        d += f" Q{P((m[0] + (root[0] - m[0]) * 0.3, m[1] + (root[1] - m[1]) * 0.3))} {P(b)}"
    m = ((tips[-1][0] + back[0]) / 2, (tips[-1][1] + back[1]) / 2)
    d += f" Q{P((m[0] + (root[0] - m[0]) * 0.3, m[1] + (root[1] - m[1]) * 0.3))} {P(back)} Z"
    ribs = "".join(f"M{P(root)} L{P(t)} " for t in tips[1:])
    return hat(d, fill, ang=-60, gap=1.3, w=0.3) + f'<path d="{ribs}" fill="none" stroke-width="0.8"/>'

def featherwing(c, root, angs, lens, fill, w=4.5):
    """Federflügel: Schwungfedern als Fächer von root (Winkel in Grad, 0 = rechts, -90 = oben), mit Kiel."""
    out = ""
    for a, l in zip(angs, lens):
        r = math.radians(a)
        tip = (root[0] + l * math.cos(r), root[1] + l * math.sin(r))
        mid = (root[0] + l * 0.55 * math.cos(r), root[1] + l * 0.55 * math.sin(r))
        out += tube([root, mid, tip], [w * 0.5, w, 0.8], fill) + hatch([root, mid, tip], [w * 0.5, w, 0.8], -0.45, 0.2, 0.95, 0.3)
        out += f'<path d="M{root[0]:.1f} {root[1]:.1f} L{tip[0]:.1f} {tip[1]:.1f}" fill="none" stroke-width="0.35"/>'
    return out

def spots(pts, ws, fill, side=0.35, every=10, rel=0.16):
    """Flecken auf dem Leib (wie im kolorierten Holzschnitt), auf der Oberseite."""
    c, w, nrm = _frame(pts, ws)
    return "".join(f'<ellipse cx="{x + nx * side * wi / 2:.1f}" cy="{y + ny * side * wi / 2:.1f}" rx="{wi * rel:.1f}" ry="{wi * rel * 0.8:.1f}" fill="{fill}" stroke-width="0.4"/>'
                   for i, ((x, y), wi, (nx, ny)) in enumerate(zip(c, w, nrm)) if i % every == every // 2 and wi > 3)

def tuft(c, x, y, a=0, fill=None):
    """Schwanzquaste (Löwe, Einhorn, Greif)."""
    return (f'<g transform="translate({x} {y}) rotate({a})">' + hat("M0 0 C-2 -3 -1 -7 1 -9 C1 -6 3 -5 3 -8 C5 -5 5 -2 4 0 C3 2 1 2 0 0 Z",
            fill or c["body"], ang=20, gap=1.2) + '</g>')

def water(c, y=52, x0=-4, x1=68):
    """Wasser mit Wellen, vor allem, was eintaucht."""
    d = f"M{x0} {y} " + "".join(f"Q{x + 3} {y - 2.2} {x + 6} {y} " for x in range(x0, x1, 6)) + f"V66 H{x0} Z"
    waves = "".join(f"M{x} {y + 4 + (x // 6 % 2) * 3} q2 -1.4 4 0 " for x in range(x0 + 2, x1, 7))
    return f'<path d="{d}" fill="{c["blue_l"]}"/><path d="{waves}" fill="none" stroke-width="0.5"/>'

def flugdrache(c, pose):
    """Geflügelter Drache wie im kolorierten Holzschnitt (Gessner): vier Beine, Fledermausflügel, Ringelschwanz mit Flecken."""
    k = c
    if pose == "fliegt":
        pts = [(40, 21), (34, 26), (26, 29), (16, 29), (8, 26), (4, 19), (8, 13), (13, 13), (13, 17)]
        ws = [7, 10, 13, 13, 11, 7, 4, 2.5, 1.5]
        far = batwing(c, (28, 25), [(44, 1), (38, -1), (32, 2)], (31, 24), c["ochre"])
        near = batwing(c, (24, 26), [(10, -2), (4, 4), (2, 12), (4, 20)], (16, 27), c["ochre_l"])
        body = creature(k, pts, ws, behind=[leg(k, [(15, 31), (10, 35), (5, 36)], 0, ws=(6, 4.5, 3.5)), leg(k, [(30, 31), (27, 37), (23, 39)], 10, ws=(6, 4.5, 3.5))],
                        front=[leg(k, [(18, 31), (14, 37), (9, 38)], 0, ws=(6.5, 5, 4)), leg(k, [(33, 31), (31, 37), (27, 40)], 10, ws=(6.5, 5, 4))],
                        extra=spots(pts[3:], ws[3:], c["red"]))
        return FSHADOW + f'<g transform="translate(2 6)">{far + body + near + lhead(k, 39, 20, -8, open_=False, tongue=True)}</g>'
    pts = [(40, 24), (36, 31), (28, 36), (18, 36), (11, 32), (8, 24), (10, 16), (15, 13), (18, 16)]
    ws = [7, 10, 13, 14, 12, 8, 5, 3, 1.5]
    far = batwing(c, (28, 31), [(40, 6), (36, 3), (31, 5)], (32, 30), c["ochre"])
    near = batwing(c, (24, 32), [(30, 4), (22, 4), (15, 9), (12, 17)], (18, 32), c["ochre_l"])
    lw = (6.5, 5, 4)
    body = creature(k, pts, ws, behind=[leg(k, [(31, 38), (33, 46), (31, 51), (35, 57)], 180, ws=lw), leg(k, [(20, 38), (17, 45), (21, 51), (24, 57)], 180, ws=lw)],
                    front=[leg(k, [(35, 37), (39, 45), (37, 51), (42, 57)], 180, ws=lw), leg(k, [(16, 37), (11, 44), (15, 51), (17, 57)], 180, ws=lw)],
                    extra=spots(pts[3:], ws[3:], c["red"]))
    if pose == "speit":
        return far + body + near + lhead(k, 39, 23, 18, open_=True, flame=True, fl_scale=0.55)
    return far + body + near + lhead(k, 39, 23, -14, open_=False)

def ghead(c, x, y, a=0, open_=False):
    """Adlerkopf mit Hakenschnabel und Ohrbüschel (Greif), Ursprung am Halsansatz."""
    beak = ('<path d="M9 -5 C14 -6.5 17.5 -3.5 16.5 2 C15.5 0 13.5 -1 11.5 -0.5 L9 0.5 Z" fill="{o}"/>'
            + ('<path d="M9.5 1 L14 1.5 C14 3.5 12 4.5 9.5 3.5 Z" fill="{o}"/><path d="M11 0 L15 1.2" fill="none" stroke="{r}" stroke-width="1"/>' if open_ else ""))
    beak = beak.format(o=c["ochre"], r=c["red"])
    skull = "M-4 3 C-5 -5 1 -9.5 7 -8 C10 -7.5 11 -5.5 11 -3.5 L9 1.5 C5 4 -1 5.5 -4 3 Z"
    return (f'<g transform="translate({x} {y}) rotate({a}) scale({HEAD_SCALE})">'
            + '<path d="M0 -7 L-4 -14 L3 -8.5 Z" fill="{}"/>'.format(c["body"]) + hat(skull, c["body"], region=below(-1), ang=30, gap=1.2)
            + beak + f'<circle cx="5.5" cy="-4" r="1.5" fill="{c["light"]}" stroke-width="0.6"/><circle cx="5.9" cy="-4" r="0.7" fill="#1f1a14" stroke="none"/>'
            + '<path d="M-2 -2 q2 1 4 0 M-3 1 q3 1.2 6 0" fill="none" stroke-width="0.4"/></g>')

def greif(c, pose):
    """Greif: Adlerkopf, Flügel und Fänge vorn, Löwenleib und Quastenschwanz (Heraldik)."""
    k, f = tint(c, "ochre"), tint(c, "brown")
    if pose == "fliegt":
        pts = [(42, 24), (34, 29), (24, 31), (14, 30)]
        ws = [10, 13, 13, 11]
        tail = tube([(14, 30), (8, 31), (3, 27), (2, 21)], [3, 2.5, 2, 1.5], k["body"]) + tuft(k, 2, 22, -20)
        wings = featherwing(f, (30, 26), [-150, -135, -120, -105, -90], [22, 25, 25, 22, 18], f["top"])
        far = featherwing(f, (34, 25), [-80, -65, -50], [18, 18, 15], f["body"])
        body = creature(k, pts, ws, skin="none",
                        behind=[leg(k, [(18, 32), (12, 36), (7, 36)], 0, ws=(6, 4.5, 3.5), kind="paw", skin="none")],
                        front=[leg(k, [(38, 31), (35, 37), (30, 39)], 0, ws=(5, 4, 3), skin="scales"), leg(k, [(22, 33), (17, 37), (12, 38)], 0, ws=(6.5, 5, 4), kind="paw", skin="none")])
        return FSHADOW + far + tail + body + wings + ghead(f, 42, 21, -5, open_=True)
    pts = [(38, 27), (37, 34), (32, 42), (24, 47), (16, 50)]
    ws = [10, 12.5, 14.5, 14, 12]
    tail = tube([(13, 53), (5, 53), (2, 46), (6, 40), (11, 37)], [3, 2.6, 2.2, 1.8, 1.5], k["body"]) + tuft(k, 11, 38, 70)
    wings = featherwing(f, (31, 34), [-172, -158, -143, -128, -113, -98], [14, 19, 24, 27, 27, 23], f["top"], w=4)
    far = featherwing(f, (34, 31), [-92, -76, -60], [21, 21, 17], f["body"], w=4)
    if pose == "schreit":   # aufgerichtet, ein Fang erhoben, Schnabel offen
        fr = [leg(k, [(36, 38), (42, 34), (46, 28)], 220, ws=(5, 4, 3)), leg(k, [(37, 41), (39, 50), (41, 58)], 180, ws=(5, 4, 3))]
        head = ghead(f, 39, 23, -25, open_=True)
    else:
        fr = [leg(k, [(36, 39), (38, 49), (41, 58)], 180, ws=(5, 4, 3)), leg(k, [(33, 40), (34, 50), (36, 58)], 180, ws=(5, 4, 3))]
        head = ghead(f, 39, 23, -5)
    body = creature(k, pts, ws, skin="none", behind=[fr[1]],
                    front=[fr[0], leg(k, [(20, 50), (26, 56), (32, 58)], 180, ws=(7, 5.5, 4), kind="paw", skin="none")],
                    extra=scales([(38, 26), (36, 34), (33, 39)], [10, 12, 10], size=0.12))
    return far + tail + body + wings + head

def ehead(c, x, y, a=0):
    """Einhornkopf: Pferd mit Ziegenbart, gedrehtes Horn."""
    head = "M-3 -3 C0 -6.5 5 -6.5 8 -4.5 L15 0 C16.5 2 15.5 4.5 13 4.5 L6 4 C2 4 -3 2.5 -3 -3 Z"
    horn = f'<path d="M4 -5.5 L13 -19 L6.5 -4.5 Z" fill="{c["ochre_l"]}" stroke-width="0.6"/><path d="M5.6 -7.5 l2 0.6 M7.2 -10 l1.8 0.6 M8.8 -12.5 l1.6 0.5 M10.4 -15 l1.3 0.5" fill="none" stroke-width="0.5"/>'
    return (f'<g transform="translate({x} {y}) rotate({a}) scale({HEAD_SCALE})">'
            + f'<path d="M0 -5 L-1 -11 L3 -6 Z" fill="{c["body"]}"/>' + hat(head, c["body"], region=below(1), ang=-30, gap=1.3)
            + horn + f'<path d="M10 4.5 C10 7 9 9 8 10 C8 8 7.5 6 7.5 4.3 Z" fill="{c["grey_l"]}" stroke-width="0.5"/>'
            + f'<circle cx="5" cy="-2.2" r="1" fill="#1f1a14" stroke="none"/><path d="M13.5 1 q0.8 -0.6 1.3 0.4" fill="none" stroke-width="0.5"/></g>')

def mane(c, pts):
    """Mähne: Strähnen entlang des Halses (pts von Kopf zu Widerrist)."""
    out = ""
    for a, b in zip(pts, pts[1:]):
        out += (f'<path d="M{a[0]} {a[1]} C{a[0] - 4} {a[1] + 1} {b[0] - 6} {b[1] - 1} {b[0] - 5} {b[1] + 3} C{b[0] - 3} {b[1] + 1} {b[0] - 1} {b[1]} {b[0]} {b[1]} Z" '
                f'fill="{c["ochre_l"]}" stroke-width="0.5"/>')
    return out

def einhorn(c, pose):
    """Einhorn der Heraldik: weißes Pferd mit Ziegenbart, gedrehtem Horn, Löwenschweif, gespaltenen Hufen."""
    k = tint(c, "white")
    lw = (4.6, 3.6, 2.8)
    if pose == "steigt":
        pts = [(36, 12), (34, 20), (30, 28), (24, 36), (17, 42)]
        ws = [6, 8, 11, 13, 12]
        body = creature(k, pts, ws, skin="none",
                        behind=[leg(k, [(19, 44), (22, 51), (24, 58)], 180, ws=lw, kind="hoof", skin="none"),
                                leg(k, [(28, 31), (35, 30), (37, 36)], 90, ws=lw, kind="hoof", skin="none")],
                        front=[leg(k, [(16, 45), (14, 52), (16, 58)], 180, ws=lw, kind="hoof", skin="none"),
                               leg(k, [(30, 29), (38, 26), (42, 31)], 70, ws=lw, kind="hoof", skin="none")])
        tail = tube([(15, 44), (9, 48), (6, 55), (9, 58)], [3, 2.5, 2, 1.5], k["body"]) + tuft(k, 9, 57, 120, c["ochre_l"])
        return tail + body + mane(c, [(35, 10), (32, 16), (30, 22), (27, 28)]) + ehead(k, 36, 12, 10)
    pts = [(42, 20), (39, 27), (32, 33), (22, 34), (14, 31)]
    ws = [6, 9, 12, 13, 11]
    tail = tube([(13, 31), (8, 34), (6, 42), (8, 47)], [3, 2.5, 2, 1.5], k["body"]) + tuft(k, 8, 46, 160, c["ochre_l"])
    body = creature(k, pts, ws, skin="none",
                    behind=[leg(k, [(33, 37), (34, 45), (32, 51), (33, 58)], 180, ws=lw, kind="hoof", skin="none"),
                            leg(k, [(21, 37), (18, 44), (22, 51), (23, 58)], 180, ws=lw, kind="hoof", skin="none")],
                    front=[leg(k, [(36, 36), (38, 44), (36, 51), (38, 58)], 180, ws=lw, kind="hoof", skin="none"),
                           leg(k, [(17, 36), (13, 43), (17, 51), (17, 58)], 180, ws=lw, kind="hoof", skin="none")])
    if pose == "grast":
        pts = [(46, 46), (44, 38), (39, 31), (32, 33), (22, 34), (14, 31)]
        ws = [5, 7, 9, 12, 13, 11]
        body = creature(k, pts, ws, skin="none",
                        behind=[leg(k, [(33, 37), (34, 45), (32, 51), (33, 58)], 180, ws=lw, kind="hoof", skin="none"),
                                leg(k, [(21, 37), (18, 44), (22, 51), (23, 58)], 180, ws=lw, kind="hoof", skin="none")],
                        front=[leg(k, [(36, 36), (38, 44), (36, 51), (38, 58)], 180, ws=lw, kind="hoof", skin="none"),
                               leg(k, [(17, 36), (13, 43), (17, 51), (17, 58)], 180, ws=lw, kind="hoof", skin="none")])
        grass = '<path d="M50 59 l-1 -4 M53 59 l0 -5 M56 59 l1 -4 M47 59 l-2 -3" fill="none" stroke-width="0.6"/>'
        return tail + body + mane(c, [(45, 44), (43, 38), (40, 32)]) + ehead(k, 46, 47, 75) + grass
    return tail + body + mane(c, [(41, 18), (39, 24), (36, 29)]) + ehead(k, 42, 19, 20)

def seeschlange(c, pose):
    """Seeschlange wie auf alten Seekarten (Carta Marina): Windungen über dem Wasser, Rückenflosse, Hörnerkopf."""
    k = tint(c, "green")
    def fin(pts, ws):   # rote Rückenstacheln auf der Oberseite
        cc, w, nrm = _frame(pts, ws)
        d = ""
        for i in range(2, len(cc) - 2, 4):
            (x, y), wi, (nx, ny) = cc[i], w[i], nrm[i]
            if wi < 4: continue
            bx, by = x + nx * wi / 2, y + ny * wi / 2
            d += f"M{bx - ny * 1.5:.1f} {by + nx * 1.5:.1f} L{bx + nx * 3.5:.1f} {by + ny * 3.5:.1f} L{bx + ny * 1.5:.1f} {by - nx * 1.5:.1f} Z "
        return f'<path d="{d}" fill="{c["red"]}" stroke-width="0.5"/>'
    def hump(pts, ws):
        return fin(pts, ws) + creature(k, pts, ws)
    if pose == "ringelt":   # Schlinge über dem Wasser
        neck = [(36, 22), (30, 30), (28, 40), (34, 50), (44, 52), (48, 44), (42, 38), (36, 44), (38, 56)]
        nws = [8, 9, 10, 10, 10, 9, 8, 7, 6]
        tail = [(14, 58), (10, 48), (5, 46), (3, 50)]
        return (hump(tail, [6, 5, 3, 1.5]) + hump(neck, nws) + water(c, 53)
                + lhead(k, 35, 22, 12, open_=False, horns=False))
    neck = [(46, 19), (40, 26), (38, 38), (40, 56)]
    h1 = [(30, 56), (27, 44), (20, 42), (15, 50), (14, 56)]
    h2 = [(9, 56), (5, 48), (2, 47)]
    head = (lhead(k, 45, 19, 25, open_=True, horns=False) +
            '<path d="M57 26 c1 -3 3 -5 5 -5 M56 24 c0 -4 1 -7 3 -9 M58 28 c2 -2 4 -2 6 -1" fill="none" stroke="{}" stroke-width="0.9"/>'.format(c["blue"])
            if pose == "speit" else lhead(k, 45, 19, 8, open_=False, horns=False))
    return (hump(h2, [6, 4, 2]) + hump(h1, [8, 9, 9, 8, 7]) + hump(neck, [8, 10, 11, 11])
            + water(c, 53) + head)

def phead(c, x, y, a=0, skin=None, eye=True, sc=0.75):
    """Menschlicher Kopf im Profil (Blick nach +x), Schatten am Hinterkopf. Ursprung = Kopfmitte."""
    d = "M-4.5 -1 C-4.5 -6 -1 -8.5 2.5 -8 C6 -7.5 7 -5 7 -3 L8.6 0.2 L7 0.8 L7.2 2.2 L6.4 2.6 C6.6 4 5 5.4 2 5.2 C-2 5 -4.5 3 -4.5 -1 Z"
    ey = '<circle cx="4.3" cy="-2.6" r="0.7" fill="#1f1a14" stroke="none"/>' if eye else '<path d="M3.4 -2.4 q0.9 0.7 1.8 0" fill="none" stroke-width="0.5"/>'
    return (f'<g transform="translate({x} {y}) rotate({a}) scale({sc})">' + hat(d, skin or c["skin"], region=left(0), ang=60, gap=1.4)
            + ey + '<path d="M-0.5 -2 q-1.5 1 0 2.4" fill="none" stroke-width="0.5"/></g>')

def arm(c, pts, fill, ws=(3.4, 2.8, 2.3), hand=True):
    """Arm im Ärmel (fill), Hand in Hautfarbe; nahtlos wie leg()."""
    k = dict(c, body=fill)
    return leg(k, pts, 0, ws=ws, kind="hand" if hand else "", skin="none")

def person(back=(), base="", front=(), tex=""):
    """Wie creature() für Figuren aus Flächen: Arme hinter, Kontur hinten, Fläche vorn, dann Schraffur."""
    return ("".join(l["back"] + l["front"] for l in back) + "".join(l["back"] for l in front)
            + base + "".join(l["front"] for l in front) + tex)

def nixe(c, pose):
    """Nixe: Frau mit Fischschwanz und langem Haar, auf einem Stein (Sage, Volksmotiv)."""
    t = tint(c, "green")
    fin = lambda x, y, a: (f'<g transform="translate({x} {y}) rotate({a})">' + hat("M0 0 C3 -6 7 -7 10 -6 C7 -3 7 0 10 3 C7 4 3 3 0 0 Z", c["green_l"], ang=0, gap=1.1) + '</g>')
    hair = hat("M22 19 C17 21 16 29 15 37 C14 43 16 47 18 49 C18 43 20 37 22 31 C23 27 24 24 27 21 Z", c["ochre"], region=left(19), ang=75, gap=1.2)
    torso = hat("M20 45 C19 39 20 33 24 31 C28 31 30 34 30 38 C30 41 29 43 28 46 Z", c["skin"], region=left(23), ang=60, gap=1.4)
    if pose == "taucht":   # taucht ab: nur Schwanz und Flosse über dem Wasser
        tail = [(26, 56), (28, 46), (33, 38), (38, 33)]
        return (creature(t, tail, [9, 8, 6, 4]) + fin(37, 33, -60) + water(c, 52)
                + '<path d="M18 50 q-3 -4 -6 -3 M44 50 q3 -4 6 -2 M22 47 q-1 -3 -3 -4" fill="none" stroke-width="0.6"/>')
    rock = hat("M8 60 C6 52 12 46 21 46 C30 45 37 50 38 60 Z", c["grey_l"], region=right(24), ang=-40, gap=1.3)
    tail = creature(t, [(24, 44), (22, 52), (30, 57), (42, 57), (49, 53)], [9, 8, 6, 4, 2.5])
    if pose == "winkt":
        arms = [arm(c, [(27, 33), (33, 27), (36, 20)], c["skin"]), arm(c, [(23, 34), (20, 41), (20, 46)], c["skin"])]
        extra = '<path d="M38 17 q2 -1 3 1 M39 14 q3 -2 5 1" fill="none" stroke-width="0.5"/>'
    else:   # kämmt sich mit goldenem Kamm
        arms = [arm(c, [(27, 33), (31, 27), (28, 21)], c["skin"]), arm(c, [(23, 34), (20, 41), (20, 46)], c["skin"])]
        extra = f'<path d="M26 19 l4 -2 l0.6 1.2 l-4 2 Z" fill="{c["ochre_l"]}" stroke-width="0.5"/>'
    return (rock + tail + fin(48, 54, -30) + hair + person(base=torso, front=arms) + phead(c, 25, 24)
            + hat("M21 19 C22 15 28 14 31 17 C29 17 26 18 24 21 Z", c["ochre"], ang=75, gap=1.2) + extra)

def wassermann(c, pose):
    """Wassermann (Nix): grüne Haut, Bart aus Wasserpflanzen, Dreizack, bis zur Hüfte im Wasser."""
    g = c["green_l"]
    beard = hat("M28 26 C27 32 29 37 32 40 C34 36 35 31 34 26 Z", c["blue_l"], ang=80, gap=1.2)
    hair = hat("M21 18 C19 22 18 28 19 33 C21 30 22 26 24 22 L27 18 Z", c["blue_l"], ang=80, gap=1.2)
    if pose == "taucht":
        return (hat("M18 54 C16 46 22 40 29 40 C36 40 40 46 39 54 Z", g, region=right(30), ang=60)
                + phead(c, 29, 40, skin=g) + hat("M28 42 C28 46 30 49 32 50 C34 47 35 44 34 42 Z", c["blue_l"], ang=80, gap=1.2)
                + hat("M23 34 C25 30 32 30 35 34 C32 33 27 33 23 36 Z", c["blue_l"], ang=80, gap=1.2)
                + water(c, 50) + f'<ellipse cx="16" cy="50" rx="2.4" ry="1.6" fill="{g}" stroke-width="0.6"/><ellipse cx="44" cy="50" rx="2.4" ry="1.6" fill="{g}" stroke-width="0.6"/>')
    torso = hat("M19 52 C18 42 20 35 25 33 L33 33 C38 35 40 42 39 52 Z", g, region=right(31), ang=60)
    trident = (f'<path d="M44 60 L44 10" fill="none" stroke="{c["dark"]}" stroke-width="1.6"/>'
               f'<path d="M40 15 V8 M44 13 V4 M48 15 V8 M40 15 Q44 18 48 15" fill="none" stroke="{c["ochre"]}" stroke-width="1.4"/>')
    arms = [arm(c, [(35, 36), (41, 40), (44, 35)], g)]
    if pose == "winkt":
        arms.append(arm(c, [(23, 36), (17, 30), (15, 22)], g))
    else:
        arms.append(arm(c, [(23, 36), (19, 43), (21, 48)], g))
    return (hair + person(base=torso, front=arms[::-1][:1]) + trident + person(front=arms[:1]) + phead(c, 29, 24, skin=g) + beard
            + water(c, 50))

def waldschrat(c, pose):
    """Waldschrat: kleiner Waldgeist mit Rindenhaut, Moosbart und Zweighaar, Knotenstock (Sage)."""
    b = c["brown_l"]
    lean = {"schleicht": 18, "winkt": 0}.get(pose, 4)
    body = hat("M22 50 C20 42 21 34 26 31 L34 31 C38 34 40 42 38 50 Z", b, ang=85, gap=1.6)
    legs = [leg(dict(c, body=b), [(26, 48), (25, 54), (22, 58)], 180, ws=(4.5, 4, 3.5), kind="", skin="none"),
            leg(dict(c, body=b), [(34, 48), (36, 54), (39, 58)], 180, ws=(4.5, 4, 3.5), kind="", skin="none")]
    toes = '<path d="M22 58 l-3 1 M22 58 l-2 2 M39 58 l3 1 M39 58 l2 2" fill="none" stroke-width="0.7"/>'
    staff = (f'<path d="M46 60 C45 50 47 38 45 24 M45.5 34 l4 -4 M45 27 l-3 -3" fill="none" stroke="{c["dark"]}" stroke-width="1.5"/>')
    a_front = arm(c, [(34, 34), (40, 36), (45, 33)], b, hand=False)
    a_back = arm(c, [(26, 34), (19, 28), (16, 20)], b, hand=False) if pose == "winkt" else arm(c, [(26, 34), (21, 40), (21, 45)], b, hand=False)
    hands = f'<circle cx="45" cy="33" r="2" fill="{b}" stroke-width="0.6"/>' + (f'<circle cx="16" cy="20" r="2" fill="{b}" stroke-width="0.6"/>' if pose == "winkt" else "")
    twigs = '<path d="M27 19 l-3 -6 l-2 -1 M24 13 l1 -3 M31 18 l1 -7 l3 -2 M32 11 l-2 -2 M35 19 l4 -5" fill="none" stroke-width="1"/>'
    beard = hat("M29 27 C27 35 28 42 31 47 C33 43 34 38 36 34 C37 31 37 28 36 26 Z", c["green"], ang=85, gap=1.1)
    upper = (twigs + phead(c, 31, 23, skin=b, sc=0.8) + beard)
    return (staff + person(back=[a_back], base=body + "".join(l["back"] + l["front"] for l in legs) + toes, front=[a_front])
            + f'<g transform="rotate({lean} 30 50)">{upper}</g>' + hands)

def roggenmuhme(c, pose):
    """Roggenmuhme: alte Feldgeist-Frau im Kornfeld, Kopftuch, Ährenkranz, Sichel (Sage)."""
    step = pose == "geht"
    skirt = hat("M17 59 C19 50 22 42 24 36 L34 36 C36 42 39 50 43 59 Z" if not step else "M15 59 C19 50 22 42 24 36 L34 36 C37 42 42 50 46 57 Z",
                c["brown"], region=right(30), ang=80, gap=1.3)
    bodice = hat("M23 37 C23 32 25 29 29 29 C33 29 35 32 35 37 Z", c["red"], region=right(30), ang=60)
    sickle = (f'<path d="M44 34 C50 30 52 22 47 17 C50 23 48 29 43 32 Z" fill="{c["grey_l"]}" stroke-width="0.6"/>'
              f'<path d="M43 33 L41 38" fill="none" stroke="{c["dark"]}" stroke-width="1.6"/>')
    arms = [arm(c, [(33, 31), (38, 35), (42, 36)], c["red"]), arm(c, [(25, 31), (22, 37), (23, 42)], c["red"])]
    scarf = hat("M25 29 C22 26 22 18 25 15 C28 12 33 13 35 17 L36 19 L28 19 C27 22 27 26 28 29 Z", c["red_l"], ang=60, gap=1.3)
    ears = "".join(f'<ellipse cx="{x}" cy="{y}" rx="1.1" ry="2" fill="{c["ochre_l"]}" stroke-width="0.5" transform="rotate({r} {x} {y})"/>'
                   for x, y, r in ((24, 16, -40), (27, 14, -15), (30, 13.5, 10), (33, 15, 35)))
    stalks = '<path d="M8 60 q1 -8 3 -14 M11 60 q0 -6 -1 -12 M54 60 q-1 -7 1 -13 M57 60 q1 -5 3 -10" fill="none" stroke-width="0.6"/>'
    return (stalks + skirt + person(base=bodice, front=arms) + phead(c, 30, 23, sc=0.72) + scarf + ears + sickle
            + "".join(f'<ellipse cx="{x}" cy="{y}" rx="1" ry="2.2" fill="{c["ochre_l"]}" stroke-width="0.5"/>' for x, y in ((9, 45), (10, 47), (55, 46), (60, 50))))

def zwerg(c, pose):
    """Zwerg / Bergmann: rote Zipfelmütze, langer Bart, Grubenlampe, Hacke oder Sack (Sage)."""
    tunic = hat("M21 50 C20 44 21 38 25 35 L35 35 C39 38 40 44 39 50 Z", c["brown_l"], region=right(31), ang=60)
    belt = f'<path d="M21 45 L39 45 L39 47.5 L21 47.5 Z" fill="{c["dark"]}" stroke-width="0.5"/><rect x="28.5" y="44.6" width="3" height="3.2" fill="{c["ochre"]}" stroke-width="0.5"/>'
    lg = dict(c, body=c["dark"])
    legs = [leg(lg, [(26, 49), (26, 54), (25, 58)], 0, ws=(5, 4.5, 4.5), kind="", skin="none"),
            leg(lg, [(34, 49), (35, 54), (36, 58)], 0, ws=(5, 4.5, 4.5), kind="", skin="none")]
    boots = f'<path d="M21 56 L28 56 L28 60 L20 60 Z M33 56 L40 56 L42 60 L33 60 Z" fill="{c["dark"]}" stroke-width="0.6"/>'
    hood = hat("M25 30 C22 26 22 18 26 12 C30 6 38 3 44 8 C40 7 37 9 36 13 L38 21 L29 21 C28 24 28 27 28 30 Z", c["red"], region=right(32), ang=60, gap=1.3)
    beard = hat("M29 27 C28 35 29 42 32 46 C34 42 36 36 37 28 C35 29 31 29 29 27 Z", c["white_l"], region=right(32), ang=85, gap=1.3)
    if pose == "hackt":
        tool = (f'<path d="M36 34 L46 14" fill="none" stroke="{c["brown"]}" stroke-width="1.8"/>'
                f'<path d="M39 12 C44 9 50 11 54 16 C50 14 46 14 43 16 Z" fill="{c["grey_l"]}" stroke-width="0.6"/>')
        arms = [arm(c, [(34, 38), (39, 32), (41, 26)], c["brown_l"]), arm(c, [(26, 38), (32, 33), (39, 28)], c["brown_l"])]
        back = ""
    elif pose == "traegt":
        tool = ""
        back = hat("M8 30 C6 22 14 18 20 22 C24 26 24 36 20 40 C14 42 9 38 8 30 Z", c["ochre_l"], region=below(32), ang=40)
        arms = [arm(c, [(26, 37), (21, 31), (19, 25)], c["brown_l"]), arm(c, [(34, 38), (38, 43), (38, 48)], c["brown_l"])]
    else:   # steht mit Grubenlampe
        tool = (f'<path d="M42 38 L42 41" fill="none" stroke-width="0.6"/><path d="M39.5 41 L44.5 41 L45 47 L39 47 Z" fill="{c["ochre_l"]}" stroke-width="0.6"/>'
                f'<circle cx="42" cy="44" r="1.3" fill="{c["fire2"]}" stroke="none"/>'
                '<path d="M47 41 l3 -1 M47.5 44 l3.5 0 M47 47 l3 1.2" fill="none" stroke-width="0.4"/>')
        arms = [arm(c, [(34, 38), (39, 38), (42, 38)], c["brown_l"]), arm(c, [(26, 38), (22, 43), (23, 48)], c["brown_l"])]
        back = ""
    return (back + person(back=legs, base=tunic + belt + boots, front=arms) + phead(c, 31, 25, sc=0.72) + hood + beard + tool)

def gespenst(c, pose):
    """Gespenst im Laken mit Kette und Kugel (Sage), Augenlöcher, keine Comic-Züge."""
    up = pose == "erschrickt"
    sheet = ("M18 54 C14 46 16 28 20 20 C24 11 40 11 44 20 C48 28 50 46 46 54 L42 50 L38 55 L34 50 L30 55 L26 50 L22 55 Z")
    arms = ""
    if up:
        arms = (hat("M20 38 C14 36 8 30 6 23 C11 24 16 29 20 31 Z", c["white_l"], region=below(32), ang=30)
                + hat("M44 38 C50 36 56 30 58 23 C53 24 48 29 44 31 Z", c["white_l"], region=below(32), ang=30))
    lift = -6 if pose == "schwebt" else 0
    chain = "".join(f'<ellipse cx="{x}" cy="{y}" rx="1.6" ry="1" fill="none" stroke-width="0.7" transform="rotate({r} {x} {y})"/>'
                    for x, y, r in ((47, 42, 60), (49, 45, 20), (51, 48, 60), (53, 51, 20)))
    ball = f'<circle cx="56" cy="56" r="4.2" fill="{c["dark"]}" stroke-width="0.6"/><path d="M54 54 q1.5 -1 3 0" fill="none" stroke="{c["grey_l"]}" stroke-width="0.6"/>'
    face = f'<ellipse cx="28" cy="23" rx="1.8" ry="2.6" fill="{c["dark"]}" stroke="none"/><ellipse cx="36" cy="23" rx="1.8" ry="2.6" fill="{c["dark"]}" stroke="none"/>'
    face += f'<ellipse cx="32" cy="{31 if up else 30}" rx="{2 if up else 1.6}" ry="{3 if up else 1.2}" fill="{c["dark"]}" stroke="none"/>'
    body = arms + hat(sheet, c["white_l"], region=right(36), ang=70, gap=1.4) + face
    shadow = FSHADOW if pose == "schwebt" else ""
    return shadow + f'<g transform="translate(0 {lift})">{body}</g>' + ("" if pose == "schwebt" else chain + ball)

def irrlicht(c, pose):
    """Irrlicht: Flämmchen über Moor und Friedhof, mit Strahlen wie im Holzschnitt."""
    def flame(x, y, s=1.0):
        return (f'<g transform="translate({x} {y}) scale({s})">'
                f'<path d="M0 -14 C4 -8 7 -4 6 1 C5 5 2 7 0 7 C-2 7 -5 5 -6 1 C-7 -4 -3 -6 -2 -11 C-1 -8 0 -6 1 -6 C1 -9 0 -12 0 -14 Z" fill="{c["fire2"]}"/>'
                f'<path d="M0 -5 C2 -2 3 0 2.5 2.5 C2 4.5 1 5 0 5 C-1 5 -2.5 4 -2.5 2 C-2.5 0 -1 -2 0 -5 Z" fill="{c["ochre_l"]}" stroke-width="0.5"/>'
                + "".join(f'<path d="M{9 * math.cos(math.radians(a)):.1f} {9 * math.sin(math.radians(a)) - 2:.1f} L{12 * math.cos(math.radians(a)):.1f} {12 * math.sin(math.radians(a)) - 2:.1f}" fill="none" stroke-width="0.6"/>'
                          for a in range(0, 360, 30)) + '</g>')
    if pose == "tanzt":
        return flame(16, 40, 0.75) + flame(34, 26, 0.9) + flame(50, 44, 0.7)
    if pose == "flackert":
        return flame(26, 36, 1.1) + flame(42, 46, 0.7)
    return flame(32, 34, 1.3)

def froschkoenig(c, pose):
    """Froschkönig (Grimm): Frosch mit goldenem Krönchen, am Brunnen."""
    k = tint(c, "green")
    crown = (f'<path d="M-4 0 L-4.5 -5 L-2 -2.5 L0 -6 L2 -2.5 L4.5 -5 L4 0 Z" fill="{c["ochre_l"]}" stroke-width="0.5"/>'
             f'<circle cx="0" cy="-6" r="0.8" fill="{c["red"]}" stroke-width="0.4"/>')
    if pose == "springt":
        body = hat("M14 30 C18 22 30 20 40 24 C46 26 50 30 48 34 C44 38 30 38 20 36 C16 35 13 33 14 30 Z", k["body"], region=below(30), ang=30, gap=1.3)
        legs = (tube([(20, 34), (12, 40), (4, 46)], [6, 4, 2.5], k["body"]) + tube([(22, 36), (14, 44), (8, 52)], [5, 3.5, 2], k["body"])
                + tube([(42, 34), (48, 40), (52, 46)], [3.5, 3, 2], k["body"]))
        eye = f'<circle cx="40" cy="24" r="3" fill="{k["top"]}" stroke-width="0.6"/><circle cx="41" cy="24" r="1.2" fill="#1f1a14" stroke="none"/>'
        return FSHADOW + legs + body + eye + f'<g transform="translate(40 20) rotate(15)">{crown}</g>' + spots([(18, 28), (30, 26), (42, 28)], [6, 8, 6], k["top"], every=6)
    body = hat("M14 57 C11 49 15 41 23 37 C29 34 37 32 43 33 C48 34 52 38 52 42 C52 46 48 48 43 48 C40 52 37 56 33 57 Z",
               k["body"], region=below(44), ang=30, gap=1.3)
    belly = hat("M43 48 C40 52 37 56 33 57 L26 57 C30 54 34 50 38 46 Z", c["white_l"], ang=30, gap=1.5)
    thigh = hat("M14 57 C13 50 18 45 25 47 C30 49 31 54 28 57 Z", k["body"], region=below(51), ang=30, gap=1.2)
    foot = (f'<path d="M24 57 L36 57 L40 59 L35 59 L37 61 L31 59.5 L24 59.5 Z" fill="{k["body"]}" stroke-width="0.6"/>'
            + leg(dict(k, body=k["body"]), [(41, 46), (42, 52), (43, 57)], 0, ws=(3.4, 2.8, 2.4), kind="", skin="none")["back"]
            + leg(dict(k, body=k["body"]), [(41, 46), (42, 52), (43, 57)], 0, ws=(3.4, 2.8, 2.4), kind="", skin="none")["front"]
            + '<path d="M43 57 l-2 2 M43 57 l0.5 2.6 M43 57 l3 1.6" fill="none" stroke-width="0.6"/>')
    eye = (f'<circle cx="44" cy="33" r="3" fill="{k["top"]}" stroke-width="0.6"/><ellipse cx="44.6" cy="33" rx="1.6" ry="1" fill="#1f1a14" stroke="none"/>'
           '<path d="M41 31 q3 -2.5 6 0" fill="none" stroke-width="0.5"/>')
    mouth = '<path d="M52 42 C48 44.5 43 44.5 38 42.5" fill="none" stroke-width="0.7"/><circle cx="50.5" cy="38" r="0.5" fill="#1f1a14" stroke="none"/>'
    sac = hat("M42 44 C42 51 51 51 50 44 C47 46 45 46 42 44 Z", c["white_l"], ang=0, gap=1.3) if pose == "quakt" else ""
    well = hat("M2 60 L2 50 L12 50 L12 60 Z", c["grey_l"], region=right(7), ang=0, gap=1.4) + '<path d="M2 55 H12 M7 50 V55" fill="none" stroke-width="0.5"/>'
    return (well + body + belly + thigh + foot + spots([(18, 46), (26, 38), (36, 35)], [7, 7, 6], k["top"], every=6) + eye + mouth + sac
            + f'<g transform="translate(43 29.5) rotate(10)">{crown}</g>')

def kornwolf(c, pose):
    """Kornwolf / Roggenwolf: Feldgeist in Wolfsgestalt, Ähren im Fell (Sage)."""
    k = tint(c, "ochre")
    lw = (5, 4, 3.2)
    ears = lambda pts: "".join(f'<ellipse cx="{x}" cy="{y}" rx="1" ry="2.4" fill="{c["ochre_l"]}" stroke-width="0.5" transform="rotate({r} {x} {y})"/>' for x, y, r in pts)
    tail = lambda pts: tube(pts, [4, 4.5, 3.5, 1.5], k["body"]) + hatch(pts, [4, 4.5, 3.5, 1.5], -0.4, 0, 1, 0.4)
    if pose == "heult":   # sitzt, Kopf hoch
        pts = [(36, 22), (34, 32), (28, 42), (20, 48)]
        ws = [8, 11, 13, 12]
        body = creature(k, pts, ws, skin="none",
                        behind=[leg(k, [(33, 36), (34, 47), (36, 58)], 180, ws=lw, kind="paw", skin="none")],
                        front=[leg(k, [(36, 36), (38, 47), (40, 58)], 180, ws=lw, kind="paw", skin="none"),
                               leg(k, [(20, 50), (27, 56), (32, 58)], 180, ws=(7, 5.5, 4), kind="paw", skin="none")])
        notes = '<path d="M52 8 q2 -2 4 0 M55 4 q2 -2 4 0" fill="none" stroke-width="0.5"/>'
        return (tail([(16, 54), (8, 56), (4, 52), (6, 46)]) + body + ears([(26, 38, -30), (30, 33, -20), (22, 44, -40)])
                + lhead(k, 36, 22, -50, open_=True, horns=False) + notes)
    low = pose == "schleicht"
    y0 = 6 if low else 0
    pts = [(42, 30 + y0), (34, 34 + y0), (24, 35 + y0), (14, 33 + y0)]
    ws = [9, 12, 12, 10]
    L = lambda x, y, dx: [(x, y + y0), (x + dx, 46 + y0 * 0.6), (x, 58)]
    body = creature(k, pts, ws, skin="none",
                    behind=[leg(k, L(33, 38, 2), 180, ws=lw, kind="paw", skin="none"), leg(k, L(19, 38, -3), 180, ws=lw, kind="paw", skin="none")],
                    front=[leg(k, L(37, 37, 3), 180, ws=lw, kind="paw", skin="none"), leg(k, L(15, 37, -3), 180, ws=lw, kind="paw", skin="none")])
    return (tail([(13, 33 + y0), (6, 34 + y0), (3, 40 + y0), (4, 46 + y0)]) + body
            + ears([(22, 30 + y0, -60), (28, 30 + y0, -50), (34, 30 + y0, -40)])
            + lhead(k, 41, 28 + y0, 15 if low else -10, open_=False, horns=False, tongue=False))

def basilisk(c, pose):
    """Basilisk: Hahn mit Krone und Schlangenschwanz (Bestiarien des Mittelalters)."""
    k = tint(c, "ochre")
    t = tint(c, "green")
    tail = creature(t, [(20, 40), (12, 44), (8, 52), (14, 57), (24, 55), (28, 50)], [9, 8, 7, 5, 3, 1.5])
    body = hat("M20 46 C16 38 20 28 30 26 C36 25 40 28 40 34 C40 42 34 48 26 49 C23 49 21 48 20 46 Z", k["body"], region=below(38), ang=30, gap=1.3)
    wing = hat("M22 34 C26 30 34 31 36 36 C32 40 26 42 20 42 C22 40 22 37 22 34 Z", c["brown_l"], region=below(37), ang=-20, gap=1.1)
    legs = (f'<path d="M28 48 L27 57 M33 47 L35 57" fill="none" stroke="{c["ochre"]}" stroke-width="1.6"/>'
            '<path d="M27 57 l-3 1 M27 57 l2 1.5 M35 57 l3 1 M35 57 l-2 1.5" fill="none" stroke-width="0.7"/>')
    crow = pose == "kraeht"
    a = -25 if crow else 0
    head = (f'<g transform="translate(37 24) rotate({a})">'
            + hat("M-4 4 C-5 -2 -2 -6 2 -6 C6 -6 8 -3 7 1 C6 5 0 7 -4 4 Z", k["body"], region=below(0), ang=30, gap=1.2)
            + f'<path d="M6 -2 L12 0 L6 2 Z" fill="{c["ochre_l"]}" stroke-width="0.5"/>'
            + (f'<path d="M6 1 L11 3.5 L6 2.6 Z" fill="{c["ochre_l"]}" stroke-width="0.5"/>' if crow else "")
            + f'<path d="M-2 -6 L-3 -10 L0 -8 L1 -12 L3 -8 L5 -11 L5 -6 Z" fill="{c["ochre_l"]}" stroke-width="0.5"/>'
            + f'<path d="M4 3 C4 6 6 8 7 7 C7 5 6 4 5 3 Z" fill="{c["red"]}" stroke-width="0.5"/>'
            + '<circle cx="2.5" cy="-2" r="0.8" fill="#1f1a14" stroke="none"/></g>')
    rays = '<path d="M50 14 l4 -2 M51 18 l5 0 M50 22 l4 2" fill="none" stroke-width="0.6"/>' if crow else ""
    return tail + legs + body + wing + head + rays

def wolpertinger(c, pose):
    """Wolpertinger: Hase mit Geweih und kleinen Flügeln (bayerisches Fabeltier)."""
    k = tint(c, "brown")
    antler = (f'<path d="M0 0 C-1 -5 -3 -8 -6 -10 M-3 -7 L-1 -11 M-5 -9 L-8 -9 M2 -1 C3 -6 5 -9 8 -10 M5 -8 L4 -12 M7 -9.5 L10 -8" '
              f'fill="none" stroke="{c["brown"]}" stroke-width="1.3"/>')
    wing = featherwing(c, (0, 0), [-150, -130, -110], [9, 10, 8], c["white_l"], w=3)
    if pose == "springt":
        body = hat("M10 38 C12 30 24 26 36 28 C42 29 46 32 46 36 C44 41 34 42 22 42 C14 42 10 41 10 38 Z", k["body"], region=below(36), ang=30, gap=1.3)
        legs = tube([(14, 40), (6, 46), (2, 48)], [5, 3, 2], k["body"]) + tube([(40, 38), (48, 42), (54, 46)], [3, 2.5, 2], k["body"])
        head = (f'<g transform="translate(46 28)">' + hat("M-5 4 C-6 -1 -2 -4 2 -4 C6 -4 8 -1 8 2 C7 5 2 7 -5 4 Z", k["body"], region=below(1), ang=30, gap=1.2)
                + f'<path d="M-3 -3 C-6 -10 -5 -14 -3 -14 C-1 -12 0 -7 0 -3 Z M0 -3 C0 -9 2 -12 4 -11 C4 -8 3 -5 2 -3 Z" fill="{k["body"]}" stroke-width="0.6"/>'
                + '<circle cx="3" cy="0" r="0.8" fill="#1f1a14" stroke="none"/>' + f'<g transform="translate(-1 -6)">{antler}</g></g>')
        return FSHADOW + f'<g transform="translate(0 4)">' + legs + f'<g transform="translate(28 30)">{wing}</g>' + body + head + '</g>'
    body = hat("M14 58 C10 50 14 38 24 34 C32 32 40 36 40 44 C40 52 36 58 30 58 Z", k["body"], region=right(30), ang=60, gap=1.3)
    belly = hat("M28 58 C28 52 32 46 36 46 C38 50 38 56 36 58 Z", c["white_l"], ang=60, gap=1.5)
    feet = f'<path d="M14 58 C14 55 22 55 26 58 Z M32 58 C32 55 38 55 42 58 Z" fill="{k["body"]}" stroke-width="0.7"/>'
    tail = f'<circle cx="12" cy="50" r="3" fill="{c["white_l"]}" stroke-width="0.6"/>'
    head = (f'<g transform="translate(38 30)">' + hat("M-6 5 C-7 -1 -3 -5 2 -5 C6 -5 9 -2 9 2 C8 6 2 8 -6 5 Z", k["body"], region=below(2), ang=30, gap=1.2)
            + f'<path d="M-4 -4 C-8 -12 -7 -17 -4 -17 C-2 -15 -1 -9 -1 -4 Z M0 -4 C0 -11 3 -15 5 -14 C5 -10 4 -6 2.5 -4 Z" fill="{k["body"]}" stroke-width="0.6"/>'
            + '<circle cx="3.5" cy="0" r="0.9" fill="#1f1a14" stroke="none"/><path d="M8.5 2 l3 -1 M8.5 2.6 l3 1" fill="none" stroke-width="0.4"/>'
            + f'<g transform="translate(-1 -8)">{antler}</g></g>')
    return tail + f'<g transform="translate(24 40)">{wing}</g>' + body + belly + feet + head

FABEL = {"lindwurm": (lindwurm, ("ruht", "kriecht", "speit"), "Lindwurm (Wappentier und Sagenwesen)"),
         "flugdrache": (flugdrache, ("steht", "speit", "fliegt"), "Geflügelter Drache (nach kolorierten Holzschnitten des 16. Jh.)"),
         "greif": (greif, ("sitzt", "schreit", "fliegt"), "Greif (Wappentier)"),
         "einhorn": (einhorn, ("steht", "steigt", "grast"), "Einhorn (Wappentier)"),
         "seeschlange": (seeschlange, ("taucht", "speit", "ringelt"), "Seeschlange (nach alten Seekarten)"),
         "nixe": (nixe, ("kaemmt", "winkt", "taucht"), "Nixe (Sage)"),
         "wassermann": (wassermann, ("steht", "winkt", "taucht"), "Wassermann (Sage)"),
         "waldschrat": (waldschrat, ("steht", "schleicht", "winkt"), "Waldschrat (Sage)"),
         "roggenmuhme": (roggenmuhme, ("steht", "geht"), "Roggenmuhme (Feldgeist der Sage)"),
         "zwerg": (zwerg, ("steht", "hackt", "traegt"), "Zwerg / Bergmann (Sage)"),
         "gespenst": (gespenst, ("schwebt", "erschrickt", "spukt"), "Gespenst (Sage)"),
         "irrlicht": (irrlicht, ("schwebt", "flackert", "tanzt"), "Irrlicht (Sage)"),
         "froschkoenig": (froschkoenig, ("sitzt", "quakt", "springt"), "Froschkönig (Märchen, Grimm)"),
         "kornwolf": (kornwolf, ("steht", "schleicht", "heult"), "Kornwolf (Feldgeist der Sage)"),
         "basilisk": (basilisk, ("steht", "kraeht"), "Basilisk (Bestiarium)"),
         "wolpertinger": (wolpertinger, ("sitzt", "springt"), "Wolpertinger (Fabeltier)")}
for n, (fn, poses, desc) in FABEL.items():
    for sfx, c in PAL.items():
        for p in poses:
            ID.update(p=f"{n}{sfx}-{p}-", n=0)
            write(n + sfx, p, desc + {"": ", koloriert", "-sepia": ", Sepia", "-kupfer": ", Kupferplatte"}[sfx], fn(c, p))

# --- Island (Nutzerwunsch 2026-11-25, Probe) ----------------------------------------------------------------------------
# Skandinavische Bilderbuch-/Volkskunst: flache Flächen ohne Schraffur, Schatten nur als dunklere Fläche, Punktaugen,
# Ornamente (Lopapeysa-Passe, Zickzack, Punkte) ohne eigene Kontur. Feste Palette aus Wollweiß, Ochsenblut, Moos, Petrol,
# Senf, Lava. Kontur (nachtblau, dünn) setzt poi_sprite() wie bei allen Figuren.
ISL = dict(wool="#f3ead8", wool_d="#ddd0b4", ox="#9e3b2f", ox_l="#c9614f", moss="#6f8a4a", moss_l="#93ab68", petrol="#2f6b73",
           mustard="#d9a53a", lava="#4a4a52", lava_l="#6c6c76", skin="#f1c9a5", cheek="#e8857a", ink="#22304a",
           horse="#b7773f", horse_d="#8f5a2e", flax="#f0dca8", flax_d="#d6bd82", troll="#9aa58a", troll_d="#7f8a70",
           nose="#b9ab8c", water="#8fd0d6", deer="#8a6648", deer_d="#6a4c34", bone="#efe4c8", lupin="#8a6cc8", lupin_l="#c4b0ef", wing="#cfeef0",
           beard="#ddd6c6", nyk="#a4acb4", nyk_d="#7c848e", nyk_m="#54606c", merskin="#c9dcc0", petrol_l="#5a9aa2", whale="#3c4c5c", whale_l="#6f8294",
           eider="#b8dcb0", eider_b="#c9c0a0", bird="#2a2d36", bird_l="#454a5a", beak="#e0602f", beak_b="#8a9ab0", foot="#e8742f", fish="#8fa8b4")
N = ' stroke="none"'

def clip(d, inner):
    """inner auf die Fläche d beschnitten (Ornament ohne Kontur in einer Form)."""
    ID["n"] += 1
    i = f'{ID["p"]}{ID["n"]}'
    return f'<clipPath id="c{i}"><path d="{d}"/></clipPath><g clip-path="url(#c{i})">{inner}</g>'

def zigzag(x0, x1, y, h, fill, step=3.0):
    """Reihe kleiner Dreiecke (Strickmuster), Spitzen nach oben, Grundlinie y."""
    return "".join(f'<path d="M{x:.1f} {y} l{step/2:.1f} {-h} l{step/2:.1f} {h} Z" fill="{fill}"{N}/>' for x in [x0 + k * step for k in range(int((x1 - x0) / step))])

def dots(pts, r, fill):
    return "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"{N}/>' for x, y in pts)

def zz(x, y):
    """Schlaf-Z an beliebiger Stelle (ZZ sitzt fest oben rechts)."""
    return (f'<path d="M{x} {y} h5 l-5 6 h5 M{x+7} {y-7} h3.5 l-3.5 4 h3.5" fill="none" stroke-width="1.4"/>')

def islandpferd(c, pose):
    """Islandpferd im Profil: gedrungen, kurze Beine, dicke Flachsmähne mit Stirnschopf, Satteldecke mit Zickzack-Borte."""
    leg = lambda pts, fill: tube(pts, [5.4, 4.6, 4.4], fill) + f'<ellipse cx="{pts[-1][0]}" cy="{pts[-1][1]+1.2}" rx="2.9" ry="1.7" fill="{c["lava"]}"/>'
    if pose == "toelt":   # Tölt: Vorderbein hoch angewinkelt, Kopf hoch, Hinterbein greift unter den Leib
        far = leg([(21, 40), (25, 47), (27, 54)], c["horse_d"]) + leg([(42, 40), (40, 47), (41, 54)], c["horse_d"])
        near = leg([(24, 40), (20, 47), (17, 54)], c["horse"]) + leg([(45, 39), (51, 42), (50, 47)], c["horse"])
        tilt, tail_a = -8, 18
    elif pose == "schlaeft":   # döst im Stehen, Kopf unten, ein Hinterhuf aufgekippt
        far = leg([(21, 40), (21, 47), (21, 54)], c["horse_d"]) + leg([(42, 40), (42, 47), (42, 54)], c["horse_d"])
        near = leg([(25, 40), (27, 47), (28, 53)], c["horse"]) + leg([(46, 40), (46, 47), (46, 54)], c["horse"])
        tilt, tail_a = 30, 0
    else:
        far = leg([(21, 40), (21, 47), (21, 54)], c["horse_d"]) + leg([(42, 40), (42, 47), (42, 54)], c["horse_d"])
        near = leg([(25, 40), (25, 47), (25, 54)], c["horse"]) + leg([(46, 40), (46, 47), (46, 54)], c["horse"])
        tilt, tail_a = 0, 8
    tail = (f'<g transform="rotate({tail_a} 17 31)"><path d="M18 29 C10 31 8 40 9 51 C11 47 12 45 14 43 C13 47 14 50 16 52 C18 45 19 38 20 32 Z" fill="{c["flax"]}"/>'
            f'<path d="M15 33 C13 39 13 44 14 48" fill="none" stroke="{c["flax_d"]}" stroke-width="1"/></g>')
    body = (f'<path d="M16 34 C15 27 22 24 30 25 C37 25.5 42 24.5 46 26.5 C50 29 50 37 47 41 C41 44 22 44 18 42 C16 40 16 37 16 34 Z" fill="{c["horse"]}"/>'
            f'<path d="M19 40 C26 43 40 43 47 40 C46 42 41 44 32 44 C24 44 20 43 19 40 Z" fill="{c["horse_d"]}"{N}/>')
    blanket_d = "M26 25.2 C30 25.5 36 25.5 40 25 L41 35 C36 36 30 36 25 35 Z"
    blanket = (f'<path d="{blanket_d}" fill="{c["ox"]}"/>'
               + clip(blanket_d, f'<rect x="20" y="32" width="26" height="4" fill="{c["mustard"]}"{N}/>' + zigzag(24, 44, 32.2, 2.2, c["ox"], 2.6)
                      + dots([(29, 28.5), (33, 28.2), (37, 28.5)], 0.9, c["wool"])))
    eye = (f'<path d="M52.6 15.6 q1.4 1 2.8 0" fill="none" stroke-width="1"/>' if pose == "schlaeft"
           else f'<circle cx="54" cy="15.2" r="1.3" fill="{c["ink"]}"{N}/><circle cx="54.4" cy="14.7" r="0.4" fill="#fff"{N}/>')
    head = (f'<path d="M40 31 C41 23 44 17 49 13 L55 18 C52 22 50 28 48.5 35 Z" fill="{c["horse"]}"/>'
            f'<path d="M51 11 L51.5 5.5 L54.5 10 Z" fill="{c["horse"]}"/>'
            f'<path d="M47 15 C49 10 54 9 57 12 C59 15 61 19 62 23 C62.5 26 60 27.5 57.5 26.5 C55 25.5 52 22 49 20 Z" fill="{c["horse"]}"/>'
            f'<path d="M58 21 C60 22 62 23 62 24.5 C61.5 26.5 59.5 27 57.5 26.4 C58.5 25 58.5 23 58 21 Z" fill="{c["horse_d"]}"{N}/>'
            f'<ellipse cx="60" cy="22.8" rx="0.8" ry="0.6" fill="{c["ink"]}"{N}/>' + eye
            + f'<path d="M49 9.5 C44 11 41 17 39.5 24 C38.5 29 36.5 31 34 31.5 C38 32.5 41.5 30.5 42.5 27 C43.5 22 46 17 50.5 13.5 Z" fill="{c["flax"]}"/>'
            f'<path d="M50 9 C54 7.5 57.5 11 56.5 16.5 C55.5 14 53 13 51 13.5 Z" fill="{c["flax"]}"/>'
            f'<path d="M45 15 C43 19 42 23 41 27" fill="none" stroke="{c["flax_d"]}" stroke-width="1"/>')
    head = f'<g transform="rotate({tilt} 43 31)">{head}</g>'
    z = zz(3, 14) if pose == "schlaeft" else ""
    dx = -9 if pose == "schlaeft" else -2
    if not c.get("blanket", True):
        blanket = ""
    return f'<g transform="translate({dx} 0)">' + far + tail + near + body + blanket + head + '</g>' + z

def troll(c, pose):
    """Troll von vorn: moosgraue Haut, Knollennase, Moosbüschel mit Blümchen, Lopapeysa mit Passe; schläft = wird zu Stein."""
    if pose == "schlaeft":   # im Sonnenlicht versteinert: Felsbrocken mit Moos, Nase und geschlossenen Augen
        rock = "M8 58 C5 48 9 36 18 30 C24 26 40 25 48 31 C56 37 59 49 56 58 Z"
        return (f'<path d="{rock}" fill="{c["lava_l"]}"/>'
                + clip(rock, f'<path d="M30 26 C36 34 50 36 60 40 V70 H40 C44 56 40 42 30 26 Z" fill="{c["lava"]}"{N}/>')
                + f'<path d="M17 31 C20 25 28 22 33 25 C38 21 46 24 49 31 C42 29 36 31 33 29 C28 31 22 30 17 31 Z" fill="{c["moss"]}"/>'
                + dots([(26, 26), (41, 26.5)], 1.1, c["wool"]) + dots([(26, 26), (41, 26.5)], 0.45, c["mustard"])
                + f'<path d="M22 40 q3 2 6 0 M36 40 q3 2 6 0" fill="none" stroke-width="1.3"/>'
                + f'<path d="M29 41 C27 47 30 51 32.5 51 C35.5 51 37 47 35 41 Z" fill="{c["lava_l"]}"/>'
                + f'<path d="M27 52 Q32 55 38 52" fill="none" stroke-width="1"/>'
                + f'<path d="M11 51 C13 49 15 50 16 52 M47 54 C49 52 51 52 52 54" fill="none" stroke="{c["moss"]}" stroke-width="1.6"/>' + ZZ)
    sk, skd = c["troll"], c["troll_d"]
    arm_r = [(45, 31), (49, 39), (50, 46)]
    arm_l = [(19, 31), (11, 23), (10, 14)] if pose == "winkt" else [(19, 31), (15, 39), (14, 46)]
    sleeve = lambda pts: (tube(pts, [7, 6.5, 6], c["wool_d"]) + tube(pts[-2:], [6.5, 6], c["petrol"], scale=1.0)
                          + f'<circle cx="{pts[-1][0]}" cy="{pts[-1][1]}" r="3.8" fill="{sk}"/>')
    arms = sleeve([arm_l[0], arm_l[1], ((arm_l[1][0] * 2 + arm_l[2][0]) / 3, (arm_l[1][1] * 2 + arm_l[2][1]) / 3), arm_l[2]]) \
        + sleeve([arm_r[0], arm_r[1], ((arm_r[1][0] * 2 + arm_r[2][0]) / 3, (arm_r[1][1] * 2 + arm_r[2][1]) / 3), arm_r[2]])
    legs = (tube([(25, 49), (25, 56)], [6.5, 6], c["lava"]) + tube([(39, 49), (39, 56)], [6.5, 6], c["lava"])
            + f'<ellipse cx="23.5" cy="58.5" rx="5.5" ry="2.8" fill="{sk}"/><ellipse cx="40.5" cy="58.5" rx="5.5" ry="2.8" fill="{sk}"/>')
    sweater_d = "M17 35 C17 28 23 26 32 26 C41 26 47 28 47 35 L48.5 50 C42 53 22 53 15.5 50 Z"
    hem = f'<rect x="10" y="47.5" width="44" height="6" fill="{c["petrol"]}"{N}/>' + zigzag(12, 52, 47.6, 1.6, c["ox_l"], 2.4)
    sweater = f'<path d="{sweater_d}" fill="{c["wool"]}"/>' + clip(sweater_d, hem)
    yoke_d = "M14.5 32 C15 27 22 25 32 25 C42 25 49 27 49.5 32 C49 36 42 38.5 32 38.5 C22 38.5 15 36 14.5 32 Z"
    yoke = (f'<path d="{yoke_d}" fill="{c["petrol"]}"/>'
            + clip(yoke_d, zigzag(12, 52, 38.6, 2.6, c["wool"], 3.2) + dots([(x, 31) for x in range(19, 46, 4)], 0.9, c["mustard"])))
    head = (f'<path d="M20 16 C15 12 11 12 9 14 C11 18 15 21 20 21 Z M44 16 C49 12 53 12 55 14 C53 18 49 21 44 21 Z" fill="{sk}"/>'
            f'<ellipse cx="32" cy="18" rx="13.5" ry="12" fill="{sk}"/>'
            f'<path d="M21 23 C24 29 40 29 43 23 C42 28 37 30.5 32 30.5 C27 30.5 22 28 21 23 Z" fill="{skd}"{N}/>'
            f'<path d="M20 10 C21 4.5 26 6 28 3.5 C30 6.5 34 2.5 36.5 5.5 C39 4 43.5 6.5 44 11 C38 8 27 8 20 10 Z" fill="{c["moss"]}"/>'
            + dots([(36.5, 5.8)], 1.2, c["wool"]) + dots([(36.5, 5.8)], 0.5, c["mustard"])
            + f'<path d="M23 13.5 q3 -2 6 0 M35 13.5 q3 -2 6 0" fill="none" stroke="{c["moss"]}" stroke-width="2"/>'
            + f'<circle cx="26" cy="17" r="1.5" fill="{c["ink"]}"{N}/><circle cx="38" cy="17" r="1.5" fill="{c["ink"]}"{N}/>'
            f'<ellipse cx="22" cy="22" rx="2.4" ry="1.3" fill="{c["cheek"]}" fill-opacity="0.7"{N}/><ellipse cx="42" cy="22" rx="2.4" ry="1.3" fill="{c["cheek"]}" fill-opacity="0.7"{N}/>'
            f'<path d="M28 18 C26 23 28 26.5 32 26.5 C36 26.5 38 23 36 18 C35 16 29 16 28 18 Z" fill="{c["nose"]}"/>'
            f'<path d="M27 27.5 Q32 30 37 27.5" fill="none" stroke-width="1.1"/><path d="M33.5 28.6 v1.8 h1.6 v-2.2" fill="{c["wool"]}" stroke-width="0.6"/>')
    return legs + sweater + arms + yoke + head

def papageitaucher(c, pose):
    """Papageitaucher im Profil: schwarzer Rücken, weißes Gesicht und Bauch, bunter Dreiecksschnabel, orange Füße."""
    feet = (f'<path d="M27 55 l-5 3.5 h9 Z M35 55 l-1 3.5 h8 Z" fill="{c["foot"]}"/>')
    body = (f'<path d="M22 56 C16 50 16 36 21 28 C24 21 29 16 34 16 C40 16 43.5 20 43.5 27 C44.5 36 44 48 40 56 Z" fill="{c["bird"]}"/>'
            f'<path d="M32.5 30 C38 30 42.5 35 42.5 43 C42.5 50 40.5 54 38 56 L27 56 C31 50 31 40 32.5 30 Z" fill="{c["wool"]}"/>'
            f'<path d="M32 19 C37 17.5 42.5 20 43 26 C40.5 28.5 36 28.6 32.5 26.5 C31 24 31 21 32 19 Z" fill="{c["wool"]}"/>')
    wing = (f'<path d="M20 34 C24 31 30 33 31 40 C31.5 46 28 52 21 54 C18 48 17 40 20 34 Z" fill="{c["bird_l"]}"/>'
            f'<path d="M22 46 q3 -1 5 1 M21.5 50 q3 -1 5 1" fill="none" stroke-width="0.7"/>')
    beak = (f'<path d="M42 20.5 C47 20.5 51.5 23.5 52.5 27.5 C49.5 30 45 31 42 31 Z" fill="{c["beak"]}"/>'
            f'<path d="M42 20.5 C43.6 22 43.6 29.5 42 31 L40.6 31 C41.8 28 41.8 23.5 40.6 20.5 Z" fill="{c["beak_b"]}"/>'
            f'<path d="M46 21.8 C47.6 24.5 47.6 28 46 30.2 M48.6 23.4 C49.6 25.4 49.6 27.6 48.8 29.2" fill="none" stroke="{c["mustard"]}" stroke-width="1"/>'
            f'<path d="M42 26.2 C45 26.6 49 27 52.4 27.4" fill="none" stroke-width="0.7"/>')
    if pose == "schlaeft":
        eye = f'<path d="M35.2 23 q1.6 1.2 3.2 0" fill="none" stroke-width="1"/>'
        g = f'<g transform="rotate(14 34 30)">{beak}</g>'
        return feet + body + wing + g + eye + f'<path d="M33.5 20.5 l2 -1.2 M38.5 20.3 l1.4 1" fill="none" stroke-width="0.6"/>' + zz(46, 12)
    eye = (f'<circle cx="37" cy="23" r="1.9" fill="{c["ox"]}"{N}/><circle cx="37" cy="23" r="1.2" fill="{c["ink"]}"{N}/>'
           f'<circle cx="37.4" cy="22.5" r="0.4" fill="#fff"{N}/><path d="M35 20.5 l2 -1.4 l2 1.4 M35.3 25.4 l1.7 1.4 l1.7 -1.4" fill="{c["beak_b"]}" stroke-width="0.4"/>')
    fish = ""
    if pose == "fisch":   # drei Sandaale quer im Schnabel
        fish = "".join(tube([(44 + k * 4, 26), (43.5 + k * 4, 31), (44.5 + k * 4, 37)], [3.8, 3.4, 1.4], c["fish"])
                       + f'<path d="M{44.5 + k * 4} {36.5} l-2.4 3.4 h4.8 Z" fill="{c["fish"]}"/>' for k in range(2))
    return feet + body + wing + fish + beak + eye


def isl_water(c, y):
    """Wasser vorn im Bild (Island): Wellenkante, Gletschertürkis, helle Wellenstriche ohne Kontur."""
    d = f"M-2 {y} " + "".join(f"Q{x + 4} {y - 2.6} {x + 8} {y} " for x in range(-2, 66, 8)) + f"V66 H-2 Z"
    return (f'<path d="{d}" fill="{c["water"]}"/>'
            f'<path d="M6 {y+4} q3 -1.6 6 0 M30 {y+6} q3 -1.6 6 0 M50 {y+3.5} q3 -1.6 6 0" fill="none" stroke="#fff" stroke-width="1.1"/>')

def fluff(cx, cy, rx, ry, n=14, k=1.22, rot=0):
    """Wolliger Umriss: Ellipse aus n nach außen gewölbten Bögen (Schaf, Moos)."""
    P = lambda t, f: (cx + rx * f * math.cos(t + rot), cy + ry * f * math.sin(t + rot))
    ts = [2 * math.pi * i / n for i in range(n + 1)]
    d = "M%.1f %.1f " % P(ts[0], 1)
    for a, b in zip(ts, ts[1:]):
        d += "Q%.1f %.1f " % P((a + b) / 2, k) + "%.1f %.1f " % P(b, 1)
    return d + "Z"

def eye(x, y, c, closed=False, light=False):
    """Punktauge; light: helles Auge auf dunklem Fell; closed: Schlafbogen."""
    if closed:
        return f'<path d="M{x-1.6} {y} q1.6 1.3 3.2 0" fill="none" stroke-width="1"{" stroke=" + chr(34) + c["wool"] + chr(34) if light else ""}/>'
    ring = f'<circle cx="{x}" cy="{y}" r="1.8" fill="{c["wool"]}"{N}/>' if light else ""
    return ring + f'<circle cx="{x}" cy="{y}" r="1.25" fill="{c["ink"]}"{N}/><circle cx="{x+0.4}" cy="{y-0.45}" r="0.4" fill="#fff"{N}/>'

def bone(d, fill, w=1.8):
    """Linie mit Kontur (Geweih, Horn, Löffel): Tusche breit darunter, Farbe darüber."""
    return (f'<path d="{d}" fill="none" stroke="currentColor" stroke-width="{w + 1.6}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{fill}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')

def cheeks(x0, x1, y, c):
    return "".join(f'<ellipse cx="{x}" cy="{y}" rx="2.2" ry="1.2" fill="{c["cheek"]}" fill-opacity="0.7"{N}/>' for x in (x0, x1))

def schaf(c, pose):
    """Isländisches Schaf im Profil: wolliger Leib, dunkles Gesicht, gebogene Hörner."""
    lg = lambda x0, x1, f: tube([(x0, 40), (x1, 55)], [3.6, 3.2], f) + f'<ellipse cx="{x1}" cy="56" rx="2.2" ry="1.3" fill="{c["ink"]}"{N}/>'
    head = (f'<path d="M45 24 C47 19 53 18 56 21 C59 24 59 30 56 32 C53 33.5 48 32 46 30 Z" fill="{c["lava"]}"/>'
            f'<path d="M47 24 l-6 1.6 l5 2 Z" fill="{c["lava"]}"/>' + f'<path d="{fluff(48, 21, 5, 3.6, 8)}" fill="{c["wool"]}"/>'
            + bone("M48 20 C44 16 40 19 41.5 23 C42.5 26 46 25.5 45.5 22.5", c["wool_d"], 1.6)
            + eye(52, 24.5, c, closed=pose == "schlaeft", light=True) + f'<ellipse cx="57" cy="29" rx="0.8" ry="0.6" fill="{c["wool"]}"{N}/>')
    if pose == "schlaeft":
        body = f'<path d="{fluff(31, 46, 19, 10, 16)}" fill="{c["wool"]}"/>'
        feet = f'<ellipse cx="22" cy="56.5" rx="3" ry="1.4" fill="{c["ink"]}"{N}/><ellipse cx="42" cy="56.5" rx="3" ry="1.4" fill="{c["ink"]}"{N}/>'
        return feet + body + f'<g transform="translate(-2 18) rotate(10 50 26)">{head}</g>' + zz(44, 12)
    body = f'<path d="{fluff(31, 34, 17, 11.5, 16)}" fill="{c["wool"]}"/>' + f'<path d="{fluff(31, 37, 13, 6, 10)}" fill="{c["wool_d"]}" fill-opacity="0.5"{N}/>'
    legs_far, legs_near = lg(20, 20, c["lava_l"]) + lg(40, 40, c["lava_l"]), lg(24, 24, c["lava"]) + lg(44, 44, c["lava"])
    if pose == "grast":
        head = f'<g transform="rotate(48 45 30)">{head}</g>' + '<path d="M54 56 l1 -4 M57 56 l-0.5 -5 M60 56 l-1.5 -4" fill="none" stroke="#6f8a4a" stroke-width="1.2"/>'
    return legs_far + legs_near + body + head

def polarfuchs(c, pose):
    """Polarfuchs (Winterfell) im Profil: weiß, buschiger Schwanz, kleine runde Ohren."""
    W, D = c["wool"], c["wool_d"]
    head = (f'<path d="M37 21 L37 14.5 L42 19 Z M41 19.5 L42.5 13.5 L45.5 19 Z" fill="{W}"/>'
            f'<path d="M33 30 C32 22 38 18 44 19 C48 20 51 22 55 24.5 C56 26.5 54 28 51 28 C47 29.5 41 32 36 33 Z" fill="{W}"/>'
            f'<circle cx="55" cy="25" r="1.1" fill="{c["ink"]}"{N}/>' + eye(45, 23, c, closed=pose == "schlaeft"))
    if pose == "schlaeft":
        body = f'<path d="{fluff(30, 46, 17, 11, 12, 1.12)}" fill="{W}"/>'
        tail = f'<path d="M14 48 C14 60 46 62 52 52 C46 56 30 58 22 52 C20 50 18 48 14 48 Z" fill="{D}"/>'
        return body + tail + f'<g transform="translate(-4 20) rotate(8 44 25)">{head}</g>' + zz(44, 10)
    if pose == "springt":   # Mäusesprung: Bogen in der Luft, Kopf voran nach unten in den Schnee
        tail = (f'<path d="M17 45 C9 46 2 38 3 26 C5 25 8 28 10 31 C12 34 16 36 19 40 Z" fill="{W}"/>'
                f'<path d="M3.5 27 C5 26 7 28 8.5 30.5 C7 31.5 5 31 3.8 30 Z" fill="{D}"{N}/>')
        legs = tube([(22, 40), (16, 46), (10, 50)], [6, 4, 3], W) + tube([(45, 40), (51, 50)], [3.8, 3], W)
        body = tube([(15, 44), (24, 31), (37, 28), (46, 37)], [7, 11, 10.5, 8], W)
        head = (f'<path d="M44 39 L39.5 33.5 L46 35 Z M47 36 L45.5 29.5 L50.5 34 Z" fill="{W}"/>'
                f'<path d="M43 39 C45 34 52 33.5 55 37.5 C57.5 42 57.5 48 55.5 54.5 C53.5 55.5 51.5 54.5 50.5 51.5 C47 48 43.5 44.5 43 39 Z" fill="{W}"/>'
                f'<circle cx="55.5" cy="54" r="1.1" fill="{c["ink"]}"{N}/>' + eye(52, 42, c))
        return (legs + tail + body + head + '<ellipse cx="34" cy="60.5" rx="9" ry="1.6" fill="#22304a" fill-opacity="0.18" stroke="none"/>'
                + '<path d="M50 58 q2 -2 4 0 q2 -2 4 0" fill="none" stroke-width="0.8"/>')
    tail = f'<path d="M23 54 C10 58 4 48 8 41 C11 36 18 38 18 43 C16 46 17 50 23 50 Z" fill="{W}"/><path d="M9 42 C8 45 9 48 11 50 C10 46 11 43 13 41 Z" fill="{D}"{N}/>'
    body = f'<path d="M22 56 C18 48 20 36 28 32 C34 29 40 31 41.5 38 C42.5 46 41 52 39 56 Z" fill="{W}"/>'
    legs = tube([(34, 44), (34, 56)], [4, 3.4], D) + tube([(38, 44), (39.5, 56)], [4, 3.4], W)
    return tail + body + legs + f'<path d="M23 54 C20 50 22 45 26 46 C28 48 28 53 26 56 Z" fill="{D}"{N}/>' + head

def kolkrabe(c, pose):
    """Kolkrabe im Profil: schwarz mit blauem Schimmer, dicker Schnabel, struppige Kehle."""
    B, L = c["bird"], c["bird_l"]
    legs = tube([(30, 48), (29, 57)], [2, 1.8], c["lava"]) + tube([(35, 48), (36, 57)], [2, 1.8], c["lava"]) + \
        f'<path d="M25 57.5 h8 M32 57.5 h8" fill="none" stroke-width="1.6"/>'
    tail = f'<path d="M22 44 L7 52 L10 55.5 L26 49 Z" fill="{B}"/>'
    body = f'<path d="M18 46 C17 36 25 29 34 29 C42 29 46 33 46.5 39 C47 46 39 50 30 50 C25 50 20 49 18 46 Z" fill="{B}"/>'
    wing = f'<path d="M20 40 C24 34 34 33 38 38 C38 44 30 48 20 47 Z" fill="{L}"/><path d="M24 44 q4 -1 7 1 M23 41 q5 -1 9 1" fill="none" stroke="{B}" stroke-width="0.8"/>'
    throat = f'<path d="M40 30 L43 35 L44.5 31 L47 36 L48 31" fill="{B}" stroke-width="0.8"/>'
    if pose == "ruft":
        beak = (f'<path d="M48 21 C53 19 58 18 61 19 C58 21 54 23 50 24.5 Z" fill="{c["lava_l"]}"/>'
                f'<path d="M50 26 C54 27 57 29 59 31 C55 31 52 30 49 28.5 Z" fill="{c["lava_l"]}"/>'
                f'<path d="M58 12 l3 -3 M60 16 l4 -1.5" fill="none" stroke-width="1.2"/>')
    else:
        beak = f'<path d="M49 21 C54 20.5 58.5 22.5 60 26 C56 26.5 53 27 50 28.5 Z" fill="{c["lava_l"]}"/>'
    head = f'<circle cx="44" cy="25" r="7.5" fill="{B}"/>' + beak + eye(46, 23, c, closed=pose == "schlaeft", light=True)
    if pose == "schlaeft":
        head = f'<g transform="translate(-3 6) rotate(28 44 30)">{head}</g>' + zz(48, 10)
    return tail + legs + body + throat + wing + head

def rentier(c, pose):
    """Rentier im Profil: braun mit heller Halskrause, Geweih mit Kontur, kurzer Schwanz."""
    R, Rd, W = c["deer"], c["deer_d"], c["wool"]
    lg = lambda pts, f: tube(pts, [3.8, 3.2, 3], f) + f'<ellipse cx="{pts[-1][0]}" cy="{pts[-1][1] + 1}" rx="2.4" ry="1.4" fill="{c["lava"]}"/>'
    antler = bone("M47 15 C45 10 41 7 37 6 M43 9 L44 4 M40 7 L38 2.5 M49 14 C50 9 53 6 57 5 M52 8 L51 3.5 M55 6 L57 2", c["bone"], 1.5)
    head = (antler + f'<path d="M45 14 l-4 -1 l3 4 Z" fill="{R}"/>'
            f'<path d="M45 16 C47 12 52 12 54 15 C56 18 58 22 58 25 C57.5 27 55 27.5 53 26 C50 24 47 21 45 19 Z" fill="{R}"/>'
            f'<ellipse cx="57" cy="24.5" rx="1" ry="0.8" fill="{c["ink"]}"{N}/>' + eye(50, 17, c, closed=pose == "schlaeft"))
    neck = f'<path d="M38 31 C40 25 43 20 46 16 L52 20 C50 25 48 30 46 36 Z" fill="{W}"/>'
    if pose == "schlaeft":
        body = f'<path d="M14 50 C13 43 20 40 30 40 C40 40 46 42 48 47 C50 52 47 56 40 56.5 L18 56.5 C15 56 14 53 14 50 Z" fill="{R}"/>'
        feet = f'<ellipse cx="22" cy="57" rx="4" ry="1.6" fill="{Rd}"/><ellipse cx="40" cy="57" rx="4" ry="1.6" fill="{Rd}"/>'
        return feet + body + f'<g transform="translate(-4 14)">{neck}{head}</g>' + zz(4, 16)
    body = (f'<path d="M16 34 C15 28 21 26 29 26 C36 26 42 26 46 28 C49 30 49 37 46 40 C40 43 22 43 18 41 C16 39 16 37 16 34 Z" fill="{R}"/>'
            f'<path d="M15 31 l-3 -1 l2 4 Z" fill="{W}"/><path d="M22 41 C28 43 38 43 45 40.5 C42 43 32 44 24 43.5 Z" fill="{W}"{N}/>')
    legs = (lg([(21, 39), (21, 47), (21, 55)], Rd) + lg([(41, 39), (42, 47), (42, 55)], Rd)
            + lg([(25, 39), (25, 47), (25, 55)], R) + lg([(45, 39), (45, 47), (46, 55)], R))
    hn = neck + head
    if pose == "grast":
        hn = f'<g transform="rotate(52 42 32)">{hn}</g>' + '<path d="M56 56 l1 -4 M59 56 l-0.5 -5" fill="none" stroke="#6f8a4a" stroke-width="1.2"/>'
    return legs + body + hn

def isl_lying(body, head, hc, c):
    """Schlafende Person (Nordlicht, Nutzerwunsch 2026-11-26): Körper liegt auf einem Moospolster unter einer Wolldecke mit
    Zickzackborte, der Kopf (Mitte hc) aufrecht und leicht geneigt links auf dem Kissen."""
    blanket_d = "M33 35 C40 32 55 32 61 36 L61 57 C52 59 40 59 33 57 C31 50 31 42 33 35 Z"
    return (f'<path d="M2 58 C3 50 12 47 32 47 C52 47 62 50 62 58 Z" fill="{c["moss"]}"/>'
            f'<ellipse cx="15" cy="51" rx="9" ry="4" fill="{c["wool"]}"/>'
            f'<g transform="translate(0 6) rotate(-90 32 32)">{body}</g>'
            f'<path d="{blanket_d}" fill="{c["ox_l"]}"/>' + clip(blanket_d, zigzag(30, 64, 41, 2.4, c["wool"], 3) + zigzag(30, 64, 51, 2.4, c["mustard"], 3))
            + f'<g transform="translate({20 - hc[0]} {38 - hc[1]}) rotate(-14 {hc[0]} {hc[1]})">{head}</g>'
            + zz(46, 18))

def huldufolk(c, pose):
    """Huldufólk (verborgenes Volk): Frau in isländischer Tracht (Peysuföt) mit Skotthúfa und Quaste, Flachszöpfe."""
    K = c["lava"]
    arm_r = [(39, 30), (42, 37), (40, 42)]
    arm_l = [(25, 30), (19, 23), (17, 15)] if pose == "winkt" else [(25, 30), (22, 37), (24, 42)]
    arms = "".join(tube(a, [4.2, 3.8, 3.6], K) + f'<circle cx="{a[-1][0]}" cy="{a[-1][1]}" r="2.3" fill="{c["skin"]}"/>' for a in (arm_l, arm_r))
    skirt = f'<path d="M23 39 L41 39 L46 57 L18 57 Z" fill="{K}"/>'
    apron_d = "M26 40 L38 40 L40 55 L24 55 Z"
    apron = f'<path d="{apron_d}" fill="{c["ox"]}"/>' + clip(apron_d, "".join(f'<rect x="{x}" y="38" width="1.6" height="20" fill="{col}"{N}/>' for x, col in zip(range(25, 41, 3), [c["mustard"], c["petrol"]] * 3)))
    jacket = (f'<path d="M24 31 C24 28.5 28 27.5 32 27.5 C36 27.5 40 28.5 40 31 L41.5 40.5 L22.5 40.5 Z" fill="{K}"/>'
              f'<path d="M30 28 L32 33 L34 28 Z" fill="{c["wool"]}"/>' + dots([(32, 35), (32, 38)], 0.8, c["mustard"]))
    shoes = f'<ellipse cx="27" cy="58" rx="3" ry="1.5" fill="{K}"/><ellipse cx="37" cy="58" rx="3" ry="1.5" fill="{K}"/>'
    braids = tube([(24, 17), (23, 24), (24, 31)], [3.4, 3, 2.4], c["flax"]) + tube([(40, 17), (41, 24), (40, 31)], [3.4, 3, 2.4], c["flax"])
    head = (f'<ellipse cx="32" cy="19" rx="8.5" ry="9" fill="{c["skin"]}"/>'
            f'<path d="M23.5 18 C23 11 28 9 32 9 C36 9 41 11 40.5 18 C38 14 34 13.5 32 13.5 C30 13.5 26 14 23.5 18 Z" fill="{c["flax"]}"/>'
            f'<path d="M26 11 C27 7 37 7 38 11 C35 10 29 10 26 11 Z" fill="{K}"/>'
            + tube([(37.5, 10), (42, 13), (44, 20)], [1.4, 1.2, 1.2], K) + f'<rect x="42" y="13.5" width="2.6" height="3.6" rx="0.6" fill="{c["mustard"]}" transform="rotate(-20 43 15)"/>'
            + f'<path d="M44 19 l-1.6 5 h3.4 Z" fill="{K}"/>'
            + eye(29, 19.5, c, closed=pose == "schlaeft") + eye(35, 19.5, c, closed=pose == "schlaeft") + cheeks(26.5, 37.5, 22.5, c) + '<path d="M30.5 24 q1.5 1 3 0" fill="none" stroke-width="0.9"/>')
    fig = shoes + skirt + apron + arms + jacket + braids + head
    if pose == "schlaeft":
        return isl_lying(shoes + skirt + apron + arms + jacket, braids + head, (32, 19), c)
    if pose == "verschwindet":   # verborgenes Volk: nur halb sichtbar, Funkeln
        return f'<g opacity="0.45">{fig}</g>' + star4(14, 20, 3, c["wool"]) + star4(50, 34, 2.5, c["wool"]) + star4(48, 12, 2, c["wool"])
    return fig

def elfenhaus(c, pose):
    """Álfhóll: Felsbrocken mit Moos, darin ein winziges Giebelhaus (Wohnung des verborgenen Volks)."""
    rock = "M5 58 C3 46 9 34 21 30 C30 27 43 28 51 34 C59 40 61 50 59 58 Z"
    lit = pose == "offen"   # "schlaeft" (Nordlicht) = zu: Lichter aus
    win = c["mustard"] if lit else c["petrol"]
    house = (f'<path d="M24 58 L24 45 L32 38 L40 45 L40 58 Z" fill="{c["wool"]}"/>'
             f'<path d="M22 46 L32 36.5 L42 46" fill="none" stroke="currentColor" stroke-width="3.6" stroke-linecap="round"/>'
             f'<path d="M22 46 L32 36.5 L42 46" fill="none" stroke="{c["ox"]}" stroke-width="2" stroke-linecap="round"/>'
             f'<path d="M29 58 L29 52 C29 49.5 35 49.5 35 52 L35 58 Z" fill="{c["mustard"] if lit else c["ox"]}"/>'
             f'<rect x="30" y="42" width="4" height="4" fill="{win}"/>')
    if lit:
        house += (f'<path d="M35 58 L35 52 L38.5 50.5 L38.5 58 Z" fill="{c["ox"]}"/>'
                  f'<circle cx="32" cy="44" r="5" fill="{c["mustard"]}" fill-opacity="0.35"{N}/><circle cx="32" cy="54" r="6" fill="{c["mustard"]}" fill-opacity="0.3"{N}/>')
    return (f'<path d="{rock}" fill="{c["lava_l"]}"/>'
            + clip(rock, f'<path d="M36 26 C42 34 54 38 64 42 V70 H44 C48 56 44 40 36 26 Z" fill="{c["lava"]}"{N}/>')
            + f'<path d="M14 34 C18 27 27 25 32 27 C38 24 47 26 51 33 C44 31 38 32 32 30.5 C26 32 20 32 14 34 Z" fill="{c["moss"]}"/>'
            + dots([(24, 28.5), (44, 29)], 1.1, c["wool"]) + house
            + f'<path d="M10 52 C12 50 14 51 15 53 M49 55 C51 53 53 53 54 55" fill="none" stroke="{c["moss"]}" stroke-width="1.6"/>')

def fee(c, pose):
    """Fee: kleine Gestalt mit Libellenflügeln, Kleid aus Lupinenblüten, Pusteblume als Stab."""
    V = c["lupin"]
    wings = (f'<path d="M30 30 C20 18 8 20 10 28 C11 34 22 35 30 32 Z M34 30 C44 18 56 20 54 28 C53 34 42 35 34 32 Z" fill="{c["wing"]}" fill-opacity="0.75"/>'
             f'<path d="M30 33 C22 36 14 42 18 46 C22 48 28 41 31 35 Z M34 33 C42 36 50 42 46 46 C42 48 36 41 33 35 Z" fill="{c["wing"]}" fill-opacity="0.75"/>')
    if pose == "schlaeft":   # schläft auf einem Fliegenpilz
        shroom = (f'<path d="M28 58 L29 46 L35 46 L36 58 Z" fill="{c["wool"]}"/>'
                  f'<path d="M14 47 C14 37 50 37 50 47 Z" fill="{c["ox_l"]}"/>' + dots([(22, 42), (32, 40), (42, 42.5), (27, 45), (38, 45)], 1.3, c["wool"]))
        body = (f'<path d="M27 37 C26 31 30 28 33 28 C37 28 39 32 38 37 Z" fill="{V}"/>'
                f'<circle cx="32" cy="24" r="6" fill="{c["skin"]}"/><circle cx="34" cy="18.5" r="3" fill="{c["flax"]}"/>'
                f'<path d="M26 23 C26 18 30 17.5 33 18 C30 19 28 21 27.5 25 Z" fill="{c["flax"]}"/>'
                + eye(30.5, 24.5, c, closed=True) + eye(35, 24.5, c, closed=True))
        small_w = f'<g transform="translate(16 8) scale(0.5)">{wings}</g>'
        return small_w + shroom + body + zz(44, 14)
    dress_d = "M27 31 C25 36 21 44 22 47 C25 45 27 47 29 45 C31 47 33 47 35 45 C37 47 39 45 42 47 C43 44 39 36 37 31 Z"
    dress = (f'<path d="{dress_d}" fill="{V}"/>' + clip(dress_d, dots([(25, 44), (29, 41), (33, 43), (37, 40), (40, 44), (31, 37)], 1.3, c["lupin_l"])))
    legs = tube([(29, 46), (28, 53)], [2.4, 2], c["skin"]) + tube([(35, 46), (36, 53)], [2.4, 2], c["skin"])
    arm_l = [(28, 33), (22, 26), (20, 19)] if pose == "winkt" else [(28, 33), (24, 38), (25, 42)]
    arm_r = [(36, 33), (41, 30), (45, 26)]
    arms = "".join(tube(a, [2.4, 2.2, 2], c["skin"]) for a in (arm_l, arm_r))
    wand = (f'<path d="M45 27 L49 14" fill="none" stroke="{c["moss"]}" stroke-width="1"/>'
            f'<circle cx="49.5" cy="12" r="4.2" fill="{c["wool"]}" fill-opacity="0.9"/>'
            + "".join(f'<path d="M49.5 12 l{3.4 * math.cos(a):.1f} {3.4 * math.sin(a):.1f}" fill="none" stroke="{c["wool_d"]}" stroke-width="0.5"/>' for a in [k * math.pi / 4 for k in range(8)]))
    head = (f'<circle cx="32" cy="24" r="7" fill="{c["skin"]}"/><circle cx="32" cy="15.5" r="3.6" fill="{c["flax"]}"/>'
            f'<path d="M25 24 C24 17 29 16.5 32 16.5 C35 16.5 40 17 39 24 C37 20 34 19.5 32 19.5 C30 19.5 27 20 25 24 Z" fill="{c["flax"]}"/>'
            + eye(29.5, 24.5, c) + eye(34.5, 24.5, c) + cheeks(27.5, 36.5, 27, c))
    fx = ""
    if pose == "schwebt":
        fx = '<ellipse cx="32" cy="61" rx="7" ry="1.4" fill="#22304a" fill-opacity="0.18" stroke="none"/>' + star4(12, 44, 2.4, c["mustard"]) + star4(52, 40, 2, c["mustard"])
    return fx + wings + legs + dress + arms + wand + head

def jolakoettur(c, pose):
    """Jólakötturinn (Weihnachtskatze der Sage): riesige schwarze Katze mit gelben Augen."""
    K, Y = c["bird"], c["mustard"]
    def eyes2(closed=False):
        if closed:
            return f'<path d="M23 22 q3.5 2.6 7 0 M34 22 q3.5 2.6 7 0" fill="none" stroke="{Y}" stroke-width="1.4"/>'
        return "".join(f'<ellipse cx="{x}" cy="21" rx="3.8" ry="4.2" fill="{Y}"{N}/><ellipse cx="{x}" cy="21" rx="1" ry="3.4" fill="{c["ink"]}"{N}/>' for x in (26, 38))
    whisk = f'<path d="M22 27 L12 25 M22 29 L13 30.5 M42 27 L52 25 M42 29 L51 30.5" fill="none" stroke="{c["wool"]}" stroke-width="0.7"/>'
    if pose == "schlaeft":
        body = f'<path d="M8 50 C8 38 22 34 34 34 C48 34 58 40 57 50 C56 58 46 59 32 59 C18 59 8 58 8 50 Z" fill="{K}"/>'
        tail = tube([(52, 52), (40, 57), (24, 56), (16, 51)], [7, 6, 5, 3.6], K)
        head = (f'<path d="M14 34 L15 25 L21 31 Z M30 31 L35 24 L36 33 Z" fill="{K}"/><ellipse cx="25" cy="38" rx="12" ry="9" fill="{K}"/>'
                f'<path d="M17 37 q3 2 6 0 M27 37 q3 2 6 0" fill="none" stroke="{Y}" stroke-width="1.4"/>')
        return body + head + tail + zz(46, 18)
    body = f'<path d="M17 58 C13 46 17 34 26 30 L38 30 C47 34 51 46 47 58 Z" fill="{K}"/>'
    tail = tube([(46, 56), (54, 50), (55, 40), (51, 34)], [5, 5, 4.5, 3.6], K)
    paws = f'<ellipse cx="27" cy="57.5" rx="4" ry="2.2" fill="{K}"/><ellipse cx="37" cy="57.5" rx="4" ry="2.2" fill="{K}"/>'
    ears = f'<path d="M19 17 L17 4 L28 11 Z M45 17 L47 4 L36 11 Z" fill="{K}"/><path d="M20 13 L19 7 L24 10.5 Z M44 13 L45 7 L40 10.5 Z" fill="{c["ox_l"]}"{N}/>'
    head = f'<ellipse cx="32" cy="21" rx="15" ry="12" fill="{K}"/>' + eyes2() + f'<path d="M30.5 26.5 L33.5 26.5 L32 28 Z" fill="{c["ox_l"]}"{N}/>'
    if pose == "faucht":   # Buckel, gesträubtes Fell, Maul offen
        spikes = f'<path d="M18 36 L14 31 L19 32 L17 26 L22 29 L23 23 L42 23 L43 29 L48 26 L46 32 L51 31 L46 36 Z" fill="{K}"/>'
        mouth = f'<path d="M27 28.5 C29 33.5 35 33.5 37 28.5 Z" fill="{c["ox"]}" stroke="{c["wool"]}" stroke-width="0.6"/><path d="M28.5 29 l0.8 2 l0.8 -2 M33.9 29 l0.8 2 l0.8 -2" fill="{c["wool"]}"{N}/>'
        tail = tube([(46, 56), (55, 46), (56, 30), (52, 22)], [5, 6, 6, 4], K)
        return tail + spikes + body + paws + ears + head + mouth + whisk
    return tail + body + paws + ears + head + '<path d="M29 29 q3 2 6 0" fill="none" stroke="#f3ead8" stroke-width="0.9"/>' + whisk

def jolasveinn(c, pose):
    """Weihnachtskerl (Jólasveinn): alter Kerl in brauner Wolle mit grauer Kapuze und struppigem Bart, Skyr-Schale und Holzlöffel
    (kein Weihnachtsmann: keine rote Mütze, kein weißer Bommel)."""
    Br = c["deer_d"]
    legs = tube([(26, 48), (26, 56)], [5.5, 5], c["lava"]) + tube([(38, 48), (38, 56)], [5.5, 5], c["lava"]) + \
        f'<ellipse cx="25" cy="58" rx="4.5" ry="2.2" fill="{c["lava_l"]}"/><ellipse cx="39" cy="58" rx="4.5" ry="2.2" fill="{c["lava_l"]}"/>'
    coat = f'<path d="M20 34 C20 29 25 27 32 27 C39 27 44 29 44 34 L46 50 C40 52 24 52 18 50 Z" fill="{Br}"/>' + \
        f'<rect x="18.5" y="43" width="27" height="3" fill="{c["mustard"]}"/>'
    hand = lambda a: f'<circle cx="{a[-1][0]}" cy="{a[-1][1]}" r="2.8" fill="{c["skin"]}"/>'
    arm_r = [(42, 31), (46, 37), (44, 42)]
    arm_l = [(22, 31), (15, 24), (13, 16)] if pose == "winkt" else [(22, 31), (18, 37), (20, 42)]
    arms = tube(arm_l, [5, 4.6, 4.2], Br) + hand(arm_l) + tube(arm_r, [5, 4.6, 4.2], Br) + hand(arm_r)
    extra_back, extra = "", ""
    if pose == "traegt":   # Sack über der Schulter
        extra_back = f'<path d="M40 18 C50 14 58 20 57 30 C56 38 48 40 43 36 C40 30 38 24 40 18 Z" fill="{c["wool_d"]}"/><path d="M42 21 l-3 4" fill="none" stroke-width="1"/>'
        arm_r = [(42, 31), (46, 26), (43, 21)]
        arms = tube(arm_l, [5, 4.6, 4.2], Br) + hand(arm_l) + tube(arm_r, [5, 4.6, 4.2], Br) + hand(arm_r)
    elif pose == "steht":   # Skyr-Schale und Holzlöffel
        extra = (f'<path d="M15 41 L25 41 C25 46 15 46 15 41 Z" fill="{c["petrol"]}"/><ellipse cx="20" cy="41" rx="5" ry="1.3" fill="{c["wool"]}"/>'
                 + bone("M45 42 L49 31", c["flax_d"], 1.4) + f'<ellipse cx="49.5" cy="29.5" rx="1.8" ry="2.4" fill="{c["flax_d"]}" transform="rotate(20 49.5 29.5)"/>')
    head = (f'<ellipse cx="32" cy="19" rx="9.5" ry="9" fill="{c["skin"]}"/>'
            f'<path d="M22 20 C22 30 25 34 27 38 L29 35 L32 39 L35 35 L37 38 C39 34 42 30 42 20 C38 24 26 24 22 20 Z" fill="{c["beard"]}"/>'
            f'<path d="M21 21 C19 9 26 4 33 5 C40 5 46 10 47 18 C49 22 50 27 47 31 C46 26 44 22 42.5 19 C40 15 24 15 22 21 Z" fill="{c["lava_l"]}"/>'
            f'<path d="M47 31 l-1.5 4 l3.4 -0.6 Z" fill="{c["lava_l"]}"/><path d="M22.5 18.5 C25 14.5 39 14.5 42 18.5" fill="none" stroke="{c["lava"]}" stroke-width="1"/>'
            + eye(28.5, 19.5, c, closed=pose == "schlaeft") + eye(35.5, 19.5, c, closed=pose == "schlaeft")
            + f'<ellipse cx="32" cy="23.5" rx="3.2" ry="2.6" fill="{c["cheek"]}"/><path d="M28.5 28 q3.5 2 7 0" fill="none" stroke-width="0.9"/>')
    if pose == "schlaeft":
        return isl_lying(legs + coat + arms, head, (32, 19), c)
    return extra_back + legs + coat + arms + extra + head

def hotpot(c, pose):
    """Heißer Topf (Freibad-Kultur): Badende mit Strickmütze im runden Steinbecken, Dampf."""
    pool = (f'<ellipse cx="32" cy="50" rx="27" ry="10" fill="{c["lava_l"]}"/>'
            + "".join(f'<ellipse cx="{32 + 26 * math.cos(a):.1f}" cy="{50 + 9.4 * math.sin(a):.1f}" rx="3.6" ry="2.6" fill="{c["lava_l"]}"/>' for a in [k * math.pi / 7 for k in range(14)])
            + f'<ellipse cx="32" cy="49" rx="21" ry="6.5" fill="{c["water"]}"/>')
    hat_d = "M22 20 C22 11 27 8 32 8 C37 8 42 11 42 20 Z"
    hat = (f'<path d="{hat_d}" fill="{c["petrol"]}"/>' + clip(hat_d, zigzag(20, 44, 18.5, 2.4, c["wool"], 3) + dots([(x, 13.5) for x in range(25, 40, 4)], 0.8, c["mustard"]))
           + f'<circle cx="32" cy="6.5" r="3.2" fill="{c["ox_l"]}"/><rect x="21" y="18.5" width="22" height="3.6" rx="1.6" fill="{c["wool"]}"/>')
    body = (f'<path d="M20 50 C20 38 25 33 32 33 C39 33 44 38 44 50 Z" fill="{c["skin"]}"/>'
            f'<ellipse cx="32" cy="26" rx="9" ry="8" fill="{c["skin"]}"/>' + hat
            + eye(28.5, 26.5, c, closed=pose == "schlaeft") + eye(35.5, 26.5, c, closed=pose == "schlaeft") + cheeks(26, 38, 29.5, c)
            + '<path d="M30 31 q2 1.3 4 0" fill="none" stroke-width="0.9"/>')
    arm = ""
    if pose == "winkt":
        arm = tube([(41, 41), (48, 33), (50, 25)], [3.6, 3.2, 3], c["skin"]) + f'<circle cx="50" cy="24" r="2.4" fill="{c["skin"]}"/>'
    water_front = f'<path d="M11 49 C16 54 48 54 53 49 C52 55 12 55 11 49 Z" fill="{c["water"]}"{N}/>'
    steam = f'<path d="M10 30 c-2 -3 2 -5 0 -8 c-2 -3 2 -5 0 -8 M54 34 c-2 -3 2 -5 0 -8 c-2 -3 2 -5 0 -8" fill="none" stroke="{c["wool"]}" stroke-width="1.6"/>'
    z = zz(46, 12) if pose == "schlaeft" else ""
    return pool + arm + body + water_front + f'<path d="M14 48 q3 -1.5 6 0 M44 48 q3 -1.5 6 0" fill="none" stroke="#fff" stroke-width="1"/>' + steam + z

def nykur(c, pose):
    """Nykur: graues Wasserpferd der Sage (Hufe verkehrt herum), steht im See; taucht = nur Kopf und Hals."""
    g = dict(c, horse=c["nyk"], horse_d=c["nyk_d"], flax=c["nyk_m"], flax_d=c["nyk_d"], blanket=False)
    if pose == "taucht":
        return f'<g transform="translate(-10 24)">{islandpferd(g, "steht")}</g>' + isl_water(c, 47)
    return islandpferd(g, "schlaeft" if pose == "schlaeft" else "steht") + isl_water(c, 46)

def marbendill(c, pose):
    """Marbendill: kleiner Meermann der Sage (lacht dreimal), Seetang-Bart, Fischschwanz, sitzt im Wasser."""
    S, T = c["merskin"], c["petrol"]
    if pose == "taucht":   # nur die Schwanzflosse
        return (tube([(30, 52), (32, 40), (36, 30)], [8, 6.5, 4], T)
                + f'<path d="M36 30 C34 22 38 16 44 14 C42 20 44 24 48 26 C44 28 40 30 36 30 Z" fill="{c["petrol_l"]}"/>' + isl_water(c, 48)
                + f'<path d="M18 46 q-3 -3 -6 -2 M46 46 q3 -3 6 -1" fill="none" stroke-width="0.8"/>')
    tail = tube([(26, 50), (40, 52), (50, 46), (54, 38)], [11, 8, 6, 4], T) + \
        f'<path d="M54 38 C52 32 54 28 58 26 C58 30 60 32 63 33 C60 36 57 37 54 38 Z" fill="{c["petrol_l"]}"/>'
    body = f'<path d="M22 48 C21 40 24 34 31 33 C37 33 41 38 41 47 Z" fill="{S}"/>'
    arms = tube([(23, 37), (18, 43), (21, 47)], [3.6, 3.2, 3], S) + tube([(39, 37), (44, 43), (40, 47)], [3.6, 3.2, 3], S)
    beard = f'<path d="M24 28 C24 38 28 44 31 45 C34 44 38 38 38 28 C35 31 27 31 24 28 Z" fill="{c["moss"]}"/>' + \
        f'<path d="M27 33 q1 5 3 8 M33 33 q1 5 2 7" fill="none" stroke="{c["moss_l"]}" stroke-width="0.8"/>'
    head = (f'<ellipse cx="31" cy="24" rx="8" ry="8" fill="{S}"/>'
            f'<path d="M23 23 C22 15 27 13 31 13 C35 13 40 15 39 23 C37 18 34 17 31 17 C28 17 25 18 23 23 Z" fill="{c["moss"]}"/>'
            + eye(28, 23.5, c, closed=pose in ("lacht", "schlaeft")) + eye(34, 23.5, c, closed=pose in ("lacht", "schlaeft"))
            + f'<ellipse cx="31" cy="27" rx="1.8" ry="1.4" fill="{c["cheek"]}"/>')
    mouth = (f'<path d="M27.5 30 C28.5 34 33.5 34 34.5 30 Z" fill="{c["ox"]}"/>' + '<path d="M44 16 l3 -2 M45 21 l4 0 M43 11 l2 -3" fill="none" stroke-width="1"/>'
             if pose == "lacht" else '<path d="M28.5 30.5 q2.5 1 5 0" fill="none" stroke-width="0.9"/>')
    if pose == "schlaeft":   # schläft im Wasser, Kopf zur Seite geneigt
        return tail + body + arms + f'<g transform="rotate(-14 31 34)">{head + beard + mouth}</g>' + isl_water(c, 49) + zz(44, 12)
    return tail + body + arms + head + beard + mouth + isl_water(c, 49)

def seewurm(c, pose):
    """Seewurm (Lagarfljótsormur, isländische Sage): grüne Buckel im See, kleiner Kopf mit Bartfäden."""
    G = c["moss"]
    hump = lambda x0, x1, h: tube([(x0, 52), ((x0 + x1) / 2, 52 - h), (x1, 52)], [6, 7, 6], G) + \
        f'<path d="M{x0 + 2} {52 - h * 0.45} Q{(x0 + x1) / 2} {52 - h * 1.05} {x1 - 2} {52 - h * 0.45}" fill="none" stroke="{c["moss_l"]}" stroke-width="1.4"/>'
    head = (f'<path d="M40 24 C42 17 50 15 55 18 C59 20 60 25 56 27 C51 29 44 29 40 28 Z" fill="{G}"/>'
            f'<path d="M45 17 L43 11 L48 15.5 Z M50 16 L50 10 L53 15.5 Z" fill="{c["mustard"]}"/>'
            f'<path d="M56 26 C58 30 56 33 58 36 M52 28 C53 32 51 35 52 38" fill="none" stroke-width="0.9"/>'
            + eye(51, 21, c, closed=pose == "schlaeft"))
    if pose == "taucht":
        return hump(6, 22, 12) + hump(24, 40, 14) + tube([(42, 52), (48, 44), (54, 40)], [6, 4.5, 2.5], G) + isl_water(c, 50)
    if pose == "schlaeft":
        return hump(8, 26, 9) + tube([(30, 52), (38, 46), (46, 46)], [6, 7, 7], G) + f'<g transform="translate(-6 22) rotate(6 48 22)">{head}</g>' + isl_water(c, 50) + zz(14, 18)
    return hump(4, 18, 10) + hump(19, 33, 12) + tube([(35, 52), (39, 40), (42, 28)], [6.5, 7, 6.5], G) + head + isl_water(c, 50)

def wal(c, pose):
    """Wal (Buckelwal) vor der Küste: dunkler Rücken, blaest = Fontäne, taucht = Fluke."""
    D, Dl = c["whale"], c["whale_l"]
    if pose == "taucht":
        fluke = (tube([(30, 52), (31, 42), (32, 34)], [10, 6, 4], D)
                 + f'<path d="M32 34 C26 30 16 30 10 24 C18 23 26 25 32 29 C38 25 46 23 54 24 C48 30 38 30 32 34 Z" fill="{D}"/>'
                 + f'<path d="M14 25.5 C20 26 26 28 31 31 M50 25.5 C44 26 38 28 33 31" fill="none" stroke="{Dl}" stroke-width="1.2"/>')
        drops = dots([(12, 30), (18, 34), (48, 33), (54, 29)], 1.1, c["wool"])
        return fluke + drops + isl_water(c, 48)
    back = (f'<path d="M4 52 C8 40 20 34 34 34 C46 34 56 40 60 50 L60 54 L4 54 Z" fill="{D}"/>'
            f'<path d="M30 34.5 L34 28 L37 35 Z" fill="{D}"/>' + dots([(46, 40), (50, 43), (53, 46.5)], 1, Dl)
            + f'<path d="M12 47 C22 41 36 40 48 44" fill="none" stroke="{Dl}" stroke-width="1.2"/>' + eye(52, 47, c, closed=pose == "schlaeft", light=True))
    spout = ""
    if pose == "blaest":
        spout = (f'<path d="M50 36 C49 28 46 22 42 18 M51 36 C52 28 56 22 60 19 M50.5 36 L50.5 16" fill="none" stroke="{c["water"]}" stroke-width="2.2"/>'
                 + dots([(41, 16), (61, 17), (50.5, 13), (45, 11), (56, 11)], 1.4, c["water"]))
    z = zz(10, 24) if pose == "schlaeft" else ""
    return spout + back + isl_water(c, 50) + z

def eiderente(c, pose):
    """Eiderente (Erpel) schwimmend: weißer Rücken, schwarzer Bauch und Scheitel, blassgrüner Nacken."""
    W, K = c["wool"], c["bird"]
    if pose == "taucht":   # Kopf unter Wasser, Bürzel hoch
        return (f'<path d="M20 50 C20 40 28 32 36 30 L42 27 L40 34 C44 40 44 48 40 50 Z" fill="{K}"/>'
                f'<path d="M22 50 C22 42 28 37 34 36 C38 40 38 46 36 50 Z" fill="{W}"/>'
                + tube([(26, 50), (24, 55)], [2.4, 2], c["foot"]) + isl_water(c, 49)
                + '<path d="M12 46 q-2 -3 -4 -3 M52 46 q2 -3 4 -3" fill="none" stroke-width="0.8"/>')
    body = (f'<path d="M10 44 C12 36 22 34 34 35 C42 35.5 48 38 48 44 C48 50 40 52 30 52 C20 52 12 50 10 44 Z" fill="{W}"/>'
            f'<path d="M12 46 C18 51 40 53 47 47 C46 51 38 53 30 53 C20 53 14 51 12 46 Z" fill="{K}"/>'
            f'<path d="M10 44 L4 40 L10 47 Z" fill="{K}"/><path d="M18 40 C24 37 32 37 38 40" fill="none" stroke="{c["wool_d"]}" stroke-width="1.2"/>')
    head = (f'<path d="M38 38 C37 30 40 24 46 23 C51 22 54 26 53 31 C52 35 48 38 44 40 Z" fill="{W}"/>'
            f'<path d="M40 27 C41 23 45 21.5 49 22.5 C51 23.5 52 25 52 27 C48 25.5 44 25.5 40 27 Z" fill="{K}"/>'
            f'<path d="M41 33 C44 31 48 32 51 34 C49 37 45 38 41 37 Z" fill="{c["eider"]}"{N}/>'
            f'<path d="M52 28 C56 28 59 30 60 32 C57 33 54 32.5 52 31.5 Z" fill="{c["eider_b"]}"/>'
            + eye(48.5, 28.5, c, closed=pose == "schlaeft"))
    if pose == "schlaeft":
        head = f'<g transform="translate(-14 10) rotate(-30 46 30)">{head}</g>' + zz(44, 18)
    return body + head + isl_water(c, 49)

ISLAND = {"islandpferd": (islandpferd, ("steht", "toelt", "schlaeft"), "Islandpferd (Island, Bilderbuch-Volkskunst)"),
          "troll": (troll, ("steht", "winkt", "schlaeft"), "Troll mit Lopapeysa (isländische Sage)"),
          "papageitaucher": (papageitaucher, ("steht", "fisch", "schlaeft"), "Papageitaucher (Island)"),
          "schaf": (schaf, ("steht", "grast", "schlaeft"), "Isländisches Schaf"),
          "polarfuchs": (polarfuchs, ("sitzt", "springt", "schlaeft"), "Polarfuchs"),
          "kolkrabe": (kolkrabe, ("steht", "ruft", "schlaeft"), "Kolkrabe"),
          "rentier": (rentier, ("steht", "grast", "schlaeft"), "Rentier"),
          "huldufolk": (huldufolk, ("steht", "winkt", "verschwindet", "schlaeft"), "Huldufólk, verborgenes Volk in Tracht (isländische Sage)"),
          "elfenhaus": (elfenhaus, ("zu", "offen", "schlaeft"), "Álfhóll, Elfenstein mit Haus (isländische Sage)"),
          "fee": (fee, ("schwebt", "winkt", "schlaeft"), "Fee mit Pusteblume"),
          "jolakoettur": (jolakoettur, ("sitzt", "faucht", "schlaeft"), "Jólakötturinn, Weihnachtskatze (isländische Sage)"),
          "jolasveinn": (jolasveinn, ("steht", "winkt", "traegt", "schlaeft"), "Jólasveinn, Weihnachtskerl in alter Wollkleidung (isländische Sage)"),
          "hotpot": (hotpot, ("badet", "winkt", "schlaeft"), "Badende im heißen Becken (isländische Badekultur)"),
          "nykur": (nykur, ("steht", "taucht", "schlaeft"), "Nykur, Wasserpferd (isländische Sage)"),
          "marbendill": (marbendill, ("sitzt", "lacht", "taucht", "schlaeft"), "Marbendill, Meermann (isländische Sage)"),
          "seewurm": (seewurm, ("schwimmt", "taucht", "schlaeft"), "Seewurm nach dem Lagarfljótsormur (isländische Sage)"),
          "wal": (wal, ("blaest", "taucht", "schlaeft"), "Buckelwal"),
          "eiderente": (eiderente, ("schwimmt", "taucht", "schlaeft"), "Eiderente (Erpel)")}
for n, (fn, poses, desc) in ISLAND.items():
    for p in poses:
        ID.update(p=f"{n}-{p}-", n=0)
        write(n, p, desc, fn(ISL, p))
