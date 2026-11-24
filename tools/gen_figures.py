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
         "entschlossen": '<path d="M30 33 L34 33" fill="none" stroke-width="1.4"/>'}
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
}
SHADOW = '<ellipse cx="32" cy="61" rx="11" ry="2" fill="#2b2a3a" fill-opacity="0.22" stroke="none"/>'
SPARK = star4(8, 16, 4) + star4(56, 26, 3.5) + star4(11, 40, 2.5)
TEMPO = '<path d="M2 30 L11 30 M0 38 L10 38 M3 46 L10 46" fill="none" stroke-width="1.6"/>'
ZZ = '<path d="M48 9 L53 9 L48 15 L53 15 M55 2 L58.5 2 L55 6 L58.5 6" fill="none" stroke-width="1.5"/>'

def human(f, p):
    legl = 8 if p.get("fx") == "sprung" else 9
    parts = [f.get("back", "")]
    for (hx, a) in ((28, p["legs"][0]), (36, p["legs"][1])):
        parts.append(limb(hx, 48, a, f["legw"], legl, f["leg"])[0])
    parts.append(f["torso"] + f.get("front", ""))
    la, _ = limb(25, 38, p["arms"][0], f.get("sleevew", 5), 11, f["sleeve"], f["hand"])
    ra, hand = limb(39, 38, p["arms"][1], f.get("sleevew", 5), 11, f["sleeve"], f["hand"])
    parts += [la, ra + (f["item"](*hand) if "item" in f else "")]
    ey = f.get("eyes_y", 26)
    parts.append(f["head"])
    parts.append(f["eyes_fn"](p["face"]) if "eyes_fn" in f else eyes(p["face"], [(26, ey), (38, ey)], f.get("iris", "#2b2a3a")))
    if f.get("brows") and p["face"] != "entschlossen":
        parts.append(f'<path d="M22 {ey-6} L28 {ey-4.5} M42 {ey-6} L36 {ey-4.5}" fill="none" stroke-width="1.6"/>')
    if f.get("blush", True):
        parts.append(f'<ellipse cx="20.5" cy="30" rx="3" ry="1.6" fill="{BLUSH}" stroke="none"/><ellipse cx="43.5" cy="30" rx="3" ry="1.6" fill="{BLUSH}" stroke="none"/>')
    if f.get("mouth", True):
        parts.append(f["mouth_fn"](p["face"]) if "mouth_fn" in f else MOUTH[p["face"]])
    parts.append(f.get("top", ""))
    if p.get("fx") == "winken":
        x, y = hand
        parts.append(f'<path d="M{x+4:.1f} {y-5:.1f} q3 3 0 6 M{x+7:.1f} {y-8:.1f} q5 5.5 0 11" fill="none" stroke-width="1.4"/>')
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
