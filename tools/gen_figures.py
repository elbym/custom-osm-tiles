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
                      white="#e6d4ae", white_l="#f7ecd2", skin="#d9b48a", skin_l="#ead0ac", dark="#3b2614")}
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
    pts = [(38, 28), (35, 37), (28, 45), (18, 50)]
    ws = [11, 14, 15, 13]
    tail = tube([(13, 53), (6, 52), (3, 45), (6, 38)], [3, 2.5, 2, 1.5], k["body"]) + tuft(k, 6, 39, 20)
    wings = featherwing(f, (30, 35), [-160, -145, -130, -115, -100], [20, 24, 26, 25, 20], f["top"])
    far = featherwing(f, (33, 33), [-95, -80, -65], [20, 20, 16], f["body"])
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
    body = hat("M14 58 C12 48 16 36 26 32 C34 29 42 32 46 40 C49 46 48 54 46 58 Z", k["body"], region=right(36), ang=60, gap=1.3)
    belly = hat("M22 58 C22 50 26 44 32 44 C38 44 42 50 42 58 Z", c["white_l"], region=right(36), ang=60, gap=1.5)
    legs = (f'<path d="M12 58 C10 52 14 48 20 50 L22 58 Z M48 58 C50 52 46 48 40 50 L38 58 Z" fill="{k["body"]}"/>'
            '<path d="M12 58 l-3 2 M14 58 l-1 3 M48 58 l3 2 M46 58 l1 3" fill="none" stroke-width="0.7"/>')
    eyes = (f'<circle cx="24" cy="33" r="4" fill="{k["top"]}" stroke-width="0.7"/><circle cx="38" cy="32" r="4" fill="{k["top"]}" stroke-width="0.7"/>'
            '<ellipse cx="24.5" cy="33" rx="1.6" ry="2" fill="#1f1a14" stroke="none"/><ellipse cx="38.5" cy="32" rx="1.6" ry="2" fill="#1f1a14" stroke="none"/>')
    mouth = '<path d="M20 40 Q31 45 43 39" fill="none" stroke-width="0.8"/>'
    sac = hat("M24 42 C24 50 38 50 38 42 C34 44 28 44 24 42 Z", c["white_l"], ang=0, gap=1.3) if pose == "quakt" else ""
    well = hat("M2 60 L2 50 L12 50 L12 60 Z", c["grey_l"], region=right(7), ang=0, gap=1.4) + '<path d="M2 55 H12 M7 50 V55" fill="none" stroke-width="0.5"/>'
    return (well + body + belly + legs + spots([(16, 50), (20, 38), (30, 34)], [6, 6, 6], k["top"], every=6) + eyes + mouth + sac
            + f'<g transform="translate(31 30)">{crown}</g>')

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
            write(n + sfx, p, desc + (", Sepia" if sfx else ", koloriert"), fn(c, p))
