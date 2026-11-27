#!/usr/bin/env python3
"""Sticker im Chibi-Sticker-Look (großer Kopf, kleine Punktaugen, große rosa Wangen, dünne Kontur, breiter gestanzter
Rand) aus den Figuren von Anime und Island. Nur der allgemeine Look, keine Figuren aus Manga oder Anime.
Probe an einer Figur (Nutzerwunsch 2026-11-26), danach Ausrollen auf alle Figuren und Posen.
Aufruf: tools/gen_stickers.py  ->  stickers/<figur>/<pose>.svg/.png/.webp (512 px) und stickers/packs/ (WhatsApp)."""
import os, pathlib, re, shutil, subprocess, sys, zipfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gen_figures as G
OUT = pathlib.Path(__file__).resolve().parent.parent / "stickers"
INK, BLUSH = "#3b2a2a", "#f7a1aa"

def eyes(kind, pts, iris):
    """Sticker-Augen: kleine Punkte tiefer im Gesicht; froh/schläft als dünne Bögen."""
    s = ""
    for i, (x, y) in enumerate(pts):
        x, y = x + (-0.5 if i == 0 else 0.5), y + 1.5
        if kind in ("normal", "entschlossen"):
            s += (f'<ellipse cx="{x}" cy="{y}" rx="1.9" ry="2.4" fill="{iris}" stroke="none"/>'
                  f'<circle cx="{x + 0.6}" cy="{y - 0.9}" r="0.7" fill="#fff" stroke="none"/>')
            if kind == "entschlossen":
                d = 1 if i == 0 else -1
                s += f'<path d="M{x - 2.6 * d} {y - 4.6} L{x + 1.6 * d} {y - 3.6}" fill="none" stroke-width="1"/>'
        elif kind == "froh":
            s += f'<path d="M{x - 2} {y + 0.6} Q{x} {y - 2} {x + 2} {y + 0.6}" fill="none" stroke-width="1.1"/>'
        else:
            s += f'<path d="M{x - 2} {y} Q{x} {y + 1.6} {x + 2} {y}" fill="none" stroke-width="1.1"/>'
    return s

HEAD_T = "translate(32 37) scale(1.3) translate(-32 -37)"   # Kopf um den Hals vergrößern
LOOK = dict(eyes=eyes, head_t=HEAD_T,
            blush=f'<ellipse cx="21.5" cy="31" rx="3.4" ry="2" fill="{BLUSH}" stroke="none"/>'
                  f'<ellipse cx="42.5" cy="31" rx="3.4" ry="2" fill="{BLUSH}" stroke="none"/>',
            mouth={"normal": '<path d="M31 31.5 Q32 32.6 33 31.5" fill="none" stroke-width="0.8"/>',
                   "entschlossen": '<path d="M31 32 L33 32" fill="none" stroke-width="0.8"/>',
                   "froh": '<path d="M30.6 31.2 Q32 34 33.4 31.2 Z" fill="#d0485a" stroke-width="0.7"/>',
                   "schlaeft": '<path d="M31.2 31.8 Q32 32.6 32.8 31.8" fill="none" stroke-width="0.7"/>'})

GROUND = re.compile(r'<ellipse[^>]*cy="(?:5[89]|6\d)[^"]*"[^>]*fill-opacity="0\.[12]\d*"[^>]*/>')   # Bodenschatten der Kartenfiguren

def wrap(art, rim="#ffffff", rw=7, line=0.6):
    """Gestanzter Rand: Zeichnung breit in Randfarbe nachgezogen (mit leichtem Schatten), darüber dünne Tusche.
    Bodenschatten fallen weg, sie passen nicht auf einen Sticker."""
    art = GROUND.sub("", art)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-20 -24 104 104">'
            '<filter id="s" x="-20%" y="-20%" width="140%" height="145%"><feGaussianBlur in="SourceAlpha" stdDeviation="0.8"/>'
            '<feOffset dy="0.9"/><feComponentTransfer><feFuncA type="linear" slope="0.3"/></feComponentTransfer>'
            '<feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
            f'<style>.rim * {{ stroke: {rim}; stroke-width: {rw}px; stroke-opacity: 1 }}</style>'   # CSS schlägt die Attribute der Teile
            f'<g stroke-linejoin="round" stroke-linecap="round"><g class="rim" filter="url(#s)" color="{rim}">{art}</g>'
            f'<g stroke="{INK}" color="{INK}" stroke-width="{line}">{art}</g></g></svg>')

# Mochi-Gesicht statt der Ellipse der Kartenfiguren: unten am breitesten
MOCHI = lambda skin: (f'<path d="M17.5 27 C17.5 15 25 11 32 11 C39 11 46.5 15 46.5 27 C46.5 34 40 37.5 32 37.5 '
                      f'C24 37.5 17.5 34 17.5 27 Z" fill="{skin}"/>')
FACE_RE = re.compile(r'<ellipse cx="32" cy="24" rx="14" ry="13" fill="([^"]+)"/>')
# Haar im Sticker-Look: Pony aus spitzen Strähnen (ersetzt den Pony der Kartenfigur, Farbe von dort), gerade
# Haarenden hinten werden zu Strähnenspitzen, Glanzlinien oben
def bangs(c, tip=22.3, lock=None):
    """Pony mit sechs Strähnen; lock = Unterkante der Seitensträhnen (lange Haare), sonst endet er an den Schläfen."""
    xs, s = (44.5, 40, 35, 29.5, 24.5, 19.5), ""
    for i, x in enumerate(xs):
        s += f" Q{x + 2.5 if i else 45.5} {tip - 4.3 if i else tip - 1.5} {x} {tip + (0.7 if i in (0, 5) else 0)}"
    s += f" Q18.5 {tip - 1.3} 18 27"
    if lock:
        d = f"M14 {lock} L13.5 22 C14 14 22 8.5 32 8.5 C42 8.5 50 14 50.5 22 L50 {lock} L46.5 {lock - 1.5} L46 27{s} L17.5 {lock - 1.5} Z"
    else:
        d = f"M17 28 L16 21 C16.5 13 23 9 32 9 C41 9 47.5 13 48 21 L47 28 L46 27{s} Z"
    return f'<path d="{d}" fill="{c}"/>' + SHINE(shade(c, 1.45))

SHINE = lambda c: f'<path d="M22 14 C25 11.5 28 11 30 11 M34 11 C37 11 40 12 42 14" fill="none" stroke="{c}" stroke-width="0.9"/>'
shade = lambda c, k: "#" + "".join(f"{min(255, int(int(c[i:i + 2], 16) * k + (12 if k > 1 else 0))):02x}" for i in (1, 3, 5))
BANGS = {"miko": dict(lock=40), "schulmaedchen": dict(lock=38), "schulsprecherin": dict(lock=38), "maid": {}, "nekomimi": {},
         "engel": {}, "idol": {}, "zauberin": {}, "ritterin": {}, "lehrer": dict(tip=21), "butler": dict(tip=20.5), "onmyoji": dict(tip=21)}
FIRST_PATH = re.compile(r'<path d="[^"]*" fill="(#[0-9a-f]{6})"/>')
FLAT_END = re.compile(r'L(\d+(?:\.\d+)?) (\d+) L(\d+(?:\.\d+)?) \2 Z')   # gerade Haarkante unten (rechts nach links)

def tips(m):
    x1, y, x2 = float(m[1]), float(m[2]), float(m[3])
    if not 30 <= y <= 50:   # Umhänge (y 57) bleiben gerade
        return m[0]
    n = max(2, round((x1 - x2) / 4 / 2) * 2)
    return "".join(f"L{x1 - i * (x1 - x2) / n:.1f} {y - 3 if i % 2 else y}" for i in range(n + 1)) + " Z"

BELOW_NECK = re.compile(r'<path d="M\d+(?:\.\d+)? (?:3[7-9]|[4-9]\d)[^"]*"[^>]*/>')
STICKER_FIX = {   # Teile, die zum tieferen Sticker-Auge verschoben werden
    "schulmaedchen": ("top", "translate(1.5 2.5)"), "schulsprecherin": ("top", "translate(0 1.5)"),
    "lehrer": ("top", "translate(0 1.5)"), "butler": ("top", "translate(0 1.5)")}

def rim_color(f):
    """Randfarbe des Kopf-Stickers: kräftigste Farbe der Kleidung, abgedunkelt."""
    cols = re.findall(r'fill="#([0-9a-f]{6})"', f["torso"] + f.get("back", ""))
    sat = lambda h: (lambda c: max(c) - min(c))([int(h[i:i + 2], 16) for i in (0, 2, 4)])
    c = max(cols, key=sat)
    return "#" + "".join(f"{int(int(c[i:i + 2], 16) * 0.8):02x}" for i in (0, 2, 4))

def human(name, pose, head_only=False):
    f = dict(G.H[name])
    if name in BANGS:   # erster Pfad nach dem Gesicht ist der Pony der Kartenfigur
        face, rest = f["head"].split("/>", 1)
        f["head"] = face + "/>" + FIRST_PATH.sub(lambda m: bangs(m[1], **BANGS[name]), rest, count=1)
    f["head"] = FACE_RE.sub(lambda m: MOCHI(m[1]), f["head"])
    f["back"] = FLAT_END.sub(tips, f.get("back", ""))
    if name == "miko":   # roter Knoten in der Schleife (so freigegeben)
        f["back"] += '<circle cx="46" cy="9" r="1.4" fill="#d8342c"/>'
    if name in STICKER_FIX:
        k, t = STICKER_FIX[name]
        f[k] = f'<g transform="{t}">{f[k]}</g>'
    f["back"] = f'<g transform="{HEAD_T}">{f.get("back", "")}</g>'   # Haar hinten gehört zum Kopf
    if head_only:   # Umhänge, Flügel, Schwänze (Pfade, die unter dem Hals beginnen) gehören nicht zum Kopf-Sticker
        f["back"] = BELOW_NECK.sub("", f["back"])
    if head_only:   # Kopf-Sticker: Pose nur als Gesichtsausdruck, farbiger Rand
        return wrap(G.human(f, dict(arms=(0, 0), legs=(0, 0), face=pose), dict(LOOK, head_only=True)), rim_color(G.H[name]), 6)
    return wrap(G.human(f, G.POSES[pose], LOOK))

def animal(name, pose):
    """Anime-Tiere und -Wesen: Zeichnung wie auf der Karte, dazu Wangen unter zwei Augen, dünne Tusche, weißer Rand."""
    a = G.A[name]
    blush = "".join(f'<ellipse cx="{x + (-3 if i == 0 else 3)}" cy="{y + 4}" rx="3.2" ry="1.9" fill="{BLUSH}" stroke="none"/>'
                    for i, (x, y) in enumerate(a["eyes"])) if len(a["eyes"]) == 2 else ""
    return wrap(G.animal(dict(a, body=a["body"] + blush), pose))

def island(name, pose):
    """Island-Figuren bleiben im Bilderbuch-Volkskunst-Look, nur als Sticker gerahmt."""
    G.ID.update(p=f"{name}-{pose}-", n=0)
    return wrap(G.ISLAND[name][0](G.ISL, pose))

def inkscape(svgs):
    """Ein Inkscape-Prozess je Stapel, ohne DBus: parallele Instanzen stürzen sonst ab (Gio::DBus::Error)."""
    subprocess.run(["inkscape", "-w", "1024", "--export-type=png", *map(str, svgs)], check=True, capture_output=True,
                   env=dict(os.environ, DBUS_SESSION_BUS_ADDRESS="disabled:"))

def finish(png):
    """WhatsApp-Sticker: 512×512, transparent, 16 px Luft; PNG und WebP (WhatsApp verlangt WebP unter 100 KB)."""
    subprocess.run(["magick", str(png), "-trim", "+repage", "-resize", "480x480", "-background", "none", "-gravity", "center",
                    "-extent", "512x512", str(png)], check=True)
    subprocess.run(["magick", str(png), "-quality", "85", str(png.with_suffix(".webp"))], check=True)

def packs(groups):
    """WhatsApp-Packs: höchstens 30 Sticker je Pack, gleichmäßig verteilt, dazu tray.png (96×96, erster Sticker);
    je Pack ein ZIP mit den PNGs (iPhone: in Dateien entpacken, Bilder in Fotos sichern, in der Sticker-App wählen)."""
    root = OUT / "packs"
    shutil.rmtree(root, ignore_errors=True)
    k = 0
    for title, files in groups:
        n = -(-len(files) // 30)
        for j in range(n):
            k += 1
            d = root / (f"{k:02d}-{title}" + ("" if n == 1 else f"-{j + 1}"))
            d.mkdir(parents=True)
            part = files[j::n]
            for f in part:
                shutil.copy(f.with_suffix(".webp"), d / f"{f.parent.name}-{f.stem}.webp")
            subprocess.run(["magick", str(part[0].with_suffix(".png")), "-resize", "96x96", str(d / "tray.png")], check=True)
            with zipfile.ZipFile(root / f"{d.name}.zip", "w") as z:   # fürs iPhone: PNG, die Sticker-Apps lesen aus Fotos
                z.write(d / "tray.png", f"{d.name}/tray.png")
                for f in part:
                    z.write(f.with_suffix(".png"), f"{d.name}/{f.parent.name}-{f.stem}.png")

if __name__ == "__main__":
    groups = {"anime": [], "anime-koepfe": [], "anime-tiere": [], "island": []}
    def add(group, name, pose, svg):
        d = OUT / name
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{pose}.svg").write_text(svg)
        groups[group].append(d / f"{pose}.svg")
    for name in G.H:
        for pose in ("steht", "winkt", "laeuft", "springt"):
            add("anime", name, pose, human(name, pose))
        for face in ("normal", "froh", "entschlossen", "schlaeft"):
            add("anime-koepfe", name, f"kopf-{face}", human(name, face, True))
    for name in G.A:
        for pose in ("sitzt", "springt", "schlaeft"):
            add("anime-tiere", name, pose, animal(name, pose))
    for name, (_, poses, _) in G.ISLAND.items():
        for pose in poses:
            add("island", name, pose, island(name, pose))
    svgs = [f for fs in groups.values() for f in fs]
    n = os.cpu_count()
    with ThreadPoolExecutor(n) as ex:
        list(ex.map(inkscape, [svgs[i::n] for i in range(n)]))
        list(ex.map(finish, [f.with_suffix(".png") for f in svgs]))
    packs(groups.items())
