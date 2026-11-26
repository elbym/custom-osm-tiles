#!/usr/bin/env python3
"""Markenstil: aus einer Kundenfarbe einen hellen und einen dunklen Kartenstil erzeugen (Nutzerwunsch 2026-11-26).

    tools/gen_marke.py "#c0392b" kunde [--title "Kunde"]   ->  styles/kunde.toml, styles/kunde-dark.toml
    tools/gen_marke.py --check                             ->  Selbsttest mit Gelb, Marineblau und Grau

Alles in OKLCH aus der Akzentfarbe abgeleitet: Grund, Flächen und Gebäude leicht in ihrem Farbton, Haupt- und Fernstraßen
in der Akzentfarbe, Wasser und Grün bleiben blau und grün (sonst liest man die Karte nicht). POI-Schrift in der
Akzentfarbe, abgedunkelt/aufgehellt bis Kontrast 4,5:1; der Marker zeigt die Kundenfarbe unverändert. Die erzeugten
Dateien sind normale Stile und dürfen danach von Hand bearbeitet werden (erneutes Erzeugen überschreibt sie)."""
import argparse
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def to_oklch(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    r, g, b = (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b))
    l, m, s = (math.copysign(abs(v) ** (1 / 3), v) for v in (
        0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b,
        0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b,
        0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b))
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    bb = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(a, bb), math.degrees(math.atan2(bb, a)) % 360


def _rgb(L, C, h):
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l, m, s = ((L + x * a + y * b) ** 3 for x, y in ((0.3963377774, 0.2158037573), (-0.1055613458, -0.0638541728),
                                                    (-0.0894841775, -1.2914855480)))
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def hexc(L, C, h):
    """OKLCH -> #rrggbb; Chroma so weit gesenkt, bis die Farbe in sRGB liegt."""
    while C > 0 and not all(-1e-4 <= c <= 1 + 1e-4 for c in _rgb(L, C, h)):
        C -= 0.002
    enc = lambda c: 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return "#%02x%02x%02x" % tuple(round(min(1, max(0, enc(c))) * 255) for c in _rgb(L, max(C, 0), h))


def lum(hx):
    c = [int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    x, y = sorted((lum(a), lum(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def readable(L, C, h, bg, dark, need=4.5):
    """Akzent in Helligkeit verschieben, bis er auf bg mindestens need:1 Kontrast hat."""
    while contrast(hexc(L, C, h), bg) < need and 0.05 < L < 0.98:
        L += 0.01 if dark else -0.01
    return hexc(L, C, h)


def colours(accent, dark):
    L, C, h = to_oklch(accent)
    t = min(C, 0.02) / 2           # Tönung der neutralen Flächen; graue Marke -> neutrales Grau
    k = min(C, 0.13)                # Straßen nicht greller als die Vorlage Clear
    if not dark:
        bg = hexc(0.96, t, h)
        c = dict(bg=bg, land=hexc(0.945, t, h), bld=hexc(0.885, t * 1.4, h), bld_line=hexc(0.83, t * 1.4, h),
                 water=hexc(0.82, 0.06, 235), water_label=hexc(0.45, 0.09, 240), green=hexc(0.87, 0.07, 145),
                 wood=hexc(0.83, 0.08, 145), minor="#ffffff", casing=hexc(0.81, t, h), path=hexc(0.70, t, h),
                 major=hexc(0.88, k * 0.7, h), major_casing=hexc(0.68, k, h), motor=hexc(0.80, k, h),
                 motor_casing=hexc(0.58, k, h), rail=hexc(0.62, t, h), label=hexc(0.24, t * 2, h),
                 street=hexc(0.36, t, h), halo="#ffffff", poi=readable(L, C, h, bg, False),
                 hl_area=hexc(0.94, t, h), mbg="#ffffff")
    else:
        bg = hexc(0.21, t * 1.2, h)
        c = dict(bg=bg, land=hexc(0.23, t * 1.2, h), bld=hexc(0.29, t * 1.4, h), bld_line=hexc(0.34, t * 1.4, h),
                 water=hexc(0.33, 0.05, 240), water_label=hexc(0.75, 0.07, 235), green=hexc(0.30, 0.04, 150),
                 wood=hexc(0.28, 0.05, 150), minor=hexc(0.42, t, h), casing=hexc(0.26, t, h), path=hexc(0.50, t, h),
                 major=hexc(0.55, k * 0.8, h), major_casing=hexc(0.35, k * 0.6, h), motor=hexc(0.65, k, h),
                 motor_casing=hexc(0.40, k * 0.7, h), rail=hexc(0.48, t, h), label=hexc(0.93, t, h),
                 street=hexc(0.82, t, h), halo=bg, poi=readable(L, C, h, bg, True),
                 hl_area=hexc(0.27, t, h), mbg=bg)
    c["marker"] = accent
    c["fg"] = c["label"]
    return c


TEMPLATE = '''# "{title}" ({mode_de}): Markenstil, erzeugt von tools/gen_marke.py aus der Akzentfarbe {accent}.
#   Grund und Gebäude leicht im Farbton der Marke, Haupt- und Fernstraßen in der Akzentfarbe, Wasser blau, Grün grün;
#   POI-Schrift in der Akzentfarbe mit Kontrast >= 4,5:1, Marker in der unveränderten Kundenfarbe.
title = "{title}"
category = "standard"
mode = "{mode}"
family = "{family}"
font = "Figtree"
preview_font = "Fira Sans"   # Schrift für die Vorschau (--all)
site_font = "Figtree"   # öffentliche Vorschau (--site)
attribution = "Kartenstil: eigener Entwurf (Markenstil aus {accent})"
text_scale = 1.15
hide = ["poi_r20", "road_oneway*"]

[paint."background"]
background-color = "{bg}"
[paint."landuse-*"]
fill-color = "{land}"
fill-opacity = 1
[paint."landuse-cemetery"]
fill-color = "{green}"
[paint."park"]
fill-color = "{green}"
[paint."landcover-*"]
fill-color = "{green}"
fill-opacity = 1
[paint."landcover-wood"]
fill-color = "{wood}"
[paint."landcover-sand"]
fill-color = "{land}"
[paint."water*"]
fill-color = "{water}"
line-color = "{water}"
[paint."building*"]
fill-color = "{bld}"
fill-outline-color = "{bld_line}"

[paint."*-minor*"]
line-color = "{minor}"
[paint."*-service-track"]
line-color = "{minor}"
[paint."*-secondary-tertiary*"]
line-color = "{minor}"
[paint."*-link"]
line-color = "{minor}"
[paint."*-primary*"]
line-color = "{major}"
[paint."*-trunk*"]
line-color = "{major}"
[paint."*-motorway*"]
line-color = "{motor}"
[paint."*-casing"]
line-color = "{casing}"
[paint."*-primary*-casing"]
line-color = "{major_casing}"
[paint."*-trunk*-casing"]
line-color = "{major_casing}"
[paint."*-motorway*-casing"]
line-color = "{motor_casing}"
[paint."*-path"]
line-color = "{path}"
[paint."*railway*"]
line-color = "{rail}"
[paint."highway-area"]
fill-color = "{hl_area}"
fill-outline-color = "{casing}"
[paint."aeroway-*"]
fill-color = "{land}"
line-color = "{minor}"

[paint."label_*"]
text-color = "{label}"
text-halo-color = "{halo}"
[paint."highway-name-*"]
text-color = "{street}"
text-halo-color = "{halo}"
[paint."poi_*"]
text-color = "{poi}"
text-halo-color = "{halo}"
[paint."water*label"]
text-color = "{water_label}"
text-halo-color = "{halo}"

[marker]
type = "bubble"
color = "{marker}"
bg = "{mbg}"
fg = "{fg}"
'''


def write(accent, name, title):
    for dark in (False, True):
        c = colours(accent, dark)
        f = ROOT / "styles" / f"{name}{'-dark' if dark else ''}.toml"
        f.write_text(TEMPLATE.format(**c, accent=accent, mode="dark" if dark else "light",
                                     mode_de="dunkel" if dark else "hell", family=title,
                                     title=f"{title} Dunkel" if dark else title))
        print(f)


def check():
    for accent in ("#ffd400", "#1b2a4a", "#808080", "#c0392b"):
        for dark in (False, True):
            c = colours(accent, dark)
            assert contrast(c["poi"], c["bg"]) >= 4.5, (accent, dark, c["poi"])
            assert contrast(c["label"], c["bg"]) >= 7, (accent, dark)
            assert contrast(c["minor"], c["bld"]) >= 1.1, (accent, dark)   # Straßen heben sich von Gebäuden ab
            assert all(v.startswith("#") and len(v) == 7 for v in c.values()), c
    assert hexc(*to_oklch("#c0392b")) == "#c0392b"
    print("ok")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("accent", nargs="?", help="Kundenfarbe als #rrggbb")
    p.add_argument("name", nargs="?", default="marke", help="Dateiname in styles/ (Standard: marke)")
    p.add_argument("--title", help="Stilname in der Vorschau (Standard: Name mit großem Anfangsbuchstaben)")
    p.add_argument("--check", action="store_true", help="Selbsttest")
    a = p.parse_args()
    if a.check:
        sys.exit(check())
    if not a.accent or len(a.accent) != 7 or not a.accent.startswith("#"):
        p.error("Akzentfarbe als #rrggbb angeben")
    write(a.accent.lower(), a.name, a.title or a.name.capitalize())
