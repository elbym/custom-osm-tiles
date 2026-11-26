#!/usr/bin/env python3
"""Erzeugt den Scheiben-Block in styles/hologramm.toml (zwischen den Markern '# >>> Hologramm-Scheiben' und '# <<<').
Gebäude per OSM-ID und Höhe in 3 Gruppen (fill-translate kennt keine Daten-Ausdrücke, daher je Gruppe eigene Ebenen):
eigene Neigung, eigenem Startpunkt im irisierenden Farbkreis IRIS und Linienart (nicht alle in derselben
Farbe enden lassen, die oberste Scheibe prägt das Bild). Dazu flackernde Scheiben (Deckkraft je Gebäude und Scheibe per ID),
Neon-Deckel mit Schein erst ab 12 m und ein Glitch-Band (eine Scheibe seitlich verrutscht) bei jedem 7. Hochhaus."""
import re, sys
from pathlib import Path

T = [0, 6, 12, 20, 32, 50]  # Schwellen render_height (m) je Scheibe
# Irisierend wie Hologrammfolie (Nutzerwunsch 2026-11-26): ein Farbkreis, jede Gruppe läuft ab einem anderen Startpunkt
# 6 Schritte weiter, so schillern Nachbarn verschieden, bleiben aber im selben Spektrum
IRIS = ["#00f0ff", "#48b4ff", "#8a8cff", "#b86cff", "#f05ce8", "#ff7ab4", "#ffb894", "#9affd8"]
GROUPS = [  # Versatz je Scheibe bei Stil-Zoom 15 / 17, Startpunkt im Farbkreis, Strichmuster (None = durchgezogen)
    {"step": {15: (0.6, -1.6), 17: (1.0, -2.0)}, "dash": None, "start": 0},     # Cyan -> Rosa, nach rechts
    {"step": {15: (0, -1.9), 17: (0, -2.5)}, "dash": [3, 1.5], "start": 3},     # Violett -> Cyan, senkrecht, gestrichelt
    {"step": {15: (-0.5, -1.4), 17: (-0.8, -1.8)}, "dash": [1, 1], "start": 5},  # Rosa -> Periwinkel, nach links, gepunktet
]
for g in GROUPS:
    g["c"] = [IRIS[(g["start"] + k) % len(IRIS)] for k in range(6)]
ID = '["to-number", ["id"], 0]'
H = '["coalesce", ["get", "render_height"], 0]'


def tr(g, k, dx0=0):
    return ('["interpolate", ["linear"], ["zoom"], 14, ["literal", [0, 0]], '
            + ", ".join(f'{z}, ["literal", [{round(dx * k + dx0, 2)}, {round(dy * k, 2)}]]'
                        for z, (dx, dy) in g["step"].items()) + "]")


def flicker(k, full):
    # je Gebäude und Scheibe: jede 5. fast aus, jede 5. halb (Ziffern der ID ab der 2., die letzte ist der OSM-Typ)
    return f'["match", ["%", ["floor", ["/", ["+", {ID}, ["*", {H}, 7]], {10 * 3 ** (k + 1)}]], 5], 0, {round(full * 0.12, 2)}, 1, {round(full * 0.5, 2)}, {full}]'


def block():
    out, prev = [], "holo-glitch"

    def layer(kind, lid, filt, paint):
        nonlocal prev
        out.append(f'[[layers]]\nsource-layer = "building"\nlike = "building"\ntype = "{kind}"\nafter = "{prev}"\n'
                   f'id = "{lid}"\nfilter = {filt}\nminzoom = 13\npaint = {{ {paint} }}')
        prev = lid

    W = '["interpolate", ["linear"], ["zoom"], 14, 0.4, 16, 0.9]'
    for gi, g in enumerate(GROUPS):
        # Gruppe aus ID und Höhe: Planetiler fasst bei z14 benachbarte Häuser mit gleichen Werten zu einem Objekt mit einer
        # ID zusammen (die Altstadt sind wenige große Blöcke), die ID allein färbte daher fast alles gleich
        gf = f'["==", ["%", ["+", ["floor", ["/", {ID}, 10]], ["floor", {H}]], 3], {gi}]'
        for k, (t, c) in enumerate(zip(T, g["c"])):
            f = f'["all", {gf}, [">=", {H}, {t}]]'
            top = f'["all", {gf}, [">=", {H}, {t}], ["<", {H}, {T[k + 1]}]]' if k < 5 else f
            dash = f', line-dasharray = {g["dash"]}' if g["dash"] and k else ""
            layer("fill", f"holo-{gi}-{k}", f,
                  f'fill-color = "{c}", fill-opacity = {flicker(k, 0.10 if k == 0 else 0.06) if k else 0.10}, fill-translate = {tr(g, k)}')
            layer("line", f"holo-{gi}-{k}-kante", f,
                  f'line-color = "{c}", line-width = {W}, line-opacity = {flicker(k, 0.8) if k else 0.9}{dash}, line-translate = {tr(g, k)}')
            if k >= 2:  # Neon-Deckel mit Schein erst ab 12 m, flache Häuser bleiben ruhig
                layer("line", f"holo-{gi}-{k}-schein", top,
                      f'line-color = "{c}", line-width = 4, line-blur = 3, line-opacity = 0.45, line-translate = {tr(g, k)}')
                layer("line", f"holo-{gi}-{k}-deckel", top,
                      f'line-color = "{g['c'][5]}", line-width = {W}, line-opacity = 0.9, line-translate = {tr(g, k)}')
        # Glitch-Band: bei jedem 7. Gebäude ab 20 m ist Scheibe 3 seitlich verrutscht, in der Gegenfarbe
        layer("line", f"holo-{gi}-glitch", f'["all", {gf}, [">=", {H}, 20], ["==", ["%", ["floor", ["/", {ID}, 30]], 7], 0]]',
              f'line-color = "{GROUPS[(gi + 1) % 3]["c"][3]}", line-width = 1.4, line-opacity = 0.85, line-translate = {tr(g, 3, 4)}')
    return "\n".join(out)


if __name__ == "__main__":
    p = Path(__file__).resolve().parent.parent / "styles/hologramm.toml"
    s = p.read_text()
    a = s.index("[[layers]]\nsource-layer", s.index("# >>> Hologramm-Scheiben"))
    a = s.index('\n[[layers]]', s.index('id = "holo-glitch"')) + 1
    b = s.index("# <<<", a)
    p.write_text(s[:a] + block() + "\n" + s[b:])
    print(f"{block().count('[[layers]]')} Ebenen -> {p}")
