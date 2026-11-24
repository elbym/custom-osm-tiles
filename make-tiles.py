#!/usr/bin/env python3
"""Statische Leaflet-Kacheln für einen kleinen Bereich rendern.

Beispiel:
  ./make-tiles.py                               # styles/clear.toml, Bielefeld -> out/clear
  ./make-tiles.py --lat 52.115 --lon 8.67 --style styles/north.toml --out out/kunde-xy
  ./make-tiles.py --all --zoom 16-16 --radius 1.5 --retina   # jeder Stil × jede Schrift zum Vergleichen
"""
import argparse, fnmatch, functools, os, re, io, tempfile, json, math, shutil, subprocess, sys, time, tomllib, urllib.parse, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
PORT = 8089
PLANETILER = "ghcr.io/onthegomap/planetiler:latest"
TILESERVER = "docker.io/maptiler/tileserver-gl:latest"
NOTO = "https://github.com/openmaptiles/fonts/releases/download/v2.0/noto-sans.zip"
WORKERS = 4   # gleichzeitige Kachel-Anfragen; gemessen: mehr bremst (Rendern + WebP nutzen schon mehrere Kerne)


def tile(lat, lon, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def bbox(lat, lon, km):
    dlat = km / 111.32
    dlon = km / (111.32 * math.cos(math.radians(lat)))
    return lat - dlat, lon - dlon, lat + dlat, lon + dlon


def tiles_for(b, z, vw, vh):
    # maxBounds keeps the view inside b; if the view is bigger than b, Leaflet centres it on b.
    # So cover b, grown to at least one viewport (vw x vh px) around its centre.
    x0, y0 = tile(b[2], b[1], z)  # north-west
    x1, y1 = tile(b[0], b[3], z)  # south-east
    n = 2 ** z
    w, h = max(x1 - x0, vw / 256), max(y1 - y0, vh / 256)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for x in range(max(0, int(cx - w / 2)), min(n - 1, int(cx + w / 2)) + 1):
        for y in range(max(0, int(cy - h / 2)), min(n - 1, int(cy + h / 2)) + 1):
            yield x, y


def run(*cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def ensure_mbtiles(area):
    f = DATA / f"{area}.mbtiles"
    if not f.exists():
        DATA.mkdir(exist_ok=True)
        # ponytail: cached per area; delete data/<area>.mbtiles to refresh OSM data
        run("podman", "run", "--rm", "-v", f"{DATA}:/data:Z", PLANETILER,
            "--download", f"--area={area}", f"--output=/data/{area}.mbtiles")
    return f


def ensure_noto():
    # ponytail: Noto Sans fallback is 100 MB, so it is not in git; fetched once on first run
    fonts = ROOT / "style" / "fonts"
    if not (fonts / "Noto Sans Regular").exists():
        print("Lade Noto Sans (Ersatzschrift) ...", flush=True)
        zipfile.ZipFile(io.BytesIO(fetch(NOTO))).extractall(fonts)


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def geocode(query):
    """Ortsname -> (lat, lon) über Nominatim (OSM); erster Treffer. Eine Anfrage je Lauf, Nutzungsregeln: max. 1/s."""
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({"q": query, "format": "jsonv2", "limit": 1})
    req = urllib.request.Request(url, headers={"User-Agent": "make-tiles/1.0"})  # Nominatim verlangt einen User-Agent
    with urllib.request.urlopen(req, timeout=30) as r:
        hits = json.load(r)
    if not hits:
        sys.exit(f"--place: nichts gefunden für {query!r}")
    print(f"{query}: {hits[0]['display_name']} -> {hits[0]['lat']}, {hits[0]['lon']}", flush=True)
    return float(hits[0]["lat"]), float(hits[0]["lon"])


def font_config():
    """style/fonts.toml: Schriften, ihre Schnitte und Einstellungen."""
    return tomllib.loads((ROOT / "style" / "fonts.toml").read_text())


def fonts(groups=("sans", "serif")):
    """Schriften der Gruppen für --all (Noto Sans ist nur Ersatzschrift und steht nicht in fonts.toml)."""
    return sorted(f for f, cfg in font_config().items() if cfg.get("group", "sans") in groups)


def ensure_glyphs():
    """Fehlende Glyphen aus fonts-src/ erzeugen (style/fonts/ ist nicht im Git)."""
    dest = ROOT / "style" / "fonts"
    todo = [(font, face, spec) for font, cfg in font_config().items() for face, spec in cfg.items()
            if isinstance(spec, dict) and not (dest / f"{font} {face}").exists()]
    if not todo:
        return
    tool = shutil.which("build_pbf_glyphs") or shutil.which(str(Path.home() / ".cargo/bin/build_pbf_glyphs")) or sys.exit(
        "build_pbf_glyphs fehlt: cargo install build_pbf_glyphs (siehe requirements.txt)")
    with tempfile.TemporaryDirectory() as tmp:
        for font, face, spec in todo:
            src = ROOT / "fonts-src" / spec["file"]
            # Dateiname = Ordnername der Glyphen, z. B. "Literata Bold"
            out = Path(tmp) / f"{font} {face}{src.suffix}"
            axes = [f"{k}={v}" for k, v in spec.items() if k != "file"]
            if axes:
                run(sys.executable, "-m", "fontTools.varLib.instancer", str(src), *axes, "-o", str(out))
            else:
                shutil.copy(src, out)
        run(tool, tmp, str(dest))


# --streets-only: nur Straßennetz, Wasser und Ortsnamen (Poster-Look wie maptoposter); Straßennamen, Schilder,
# Bahn, Gebäude, Landnutzung und POIs fallen weg. DROP gewinnt vor KEEP.
STREETS_KEEP = ["background", "water", "water-intermittent", "waterway-*", "highway-*", "bridge-*", "tunnel-*", "label_*"]
STREETS_DROP = ["highway-name-*", "highway-shield-*", "highway-area", "*railway*", "waterway_*label"]


def build_style(toml_path, font=None, center=None, pixel=False, streets=False):
    """styles/<name>.toml + style/base.json (OSM Bright) -> fertiger Stil, Titel, Namensnennung.
    center (lat, lon): Mittelpunkt für das Koordinatengitter (graticule = true im Stil).
    pixel: 8-Bit-Modus (2 oder 4 = Pixelgröße), Pixelschriften dann nur in ganzen Rasterschritten; bei 4 jede Schrift
    genau ein Rasterschritt groß und Beschriftungen zwei Stufen früher, weil die Kachel zwei Stufen gröber gerendert
    wird (sonst fehlen Straßennamen und POIs). streets: siehe STREETS_KEEP."""
    t = tomllib.loads(Path(toml_path).read_text())
    s = json.loads((ROOT / "style" / "base.json").read_text())
    font = font or t.get("font", "Noto Sans")
    # Beschriftungssprache: OSM Bright bevorzugt name_en; stattdessen name:<language> (Standard de), sonst Originalname
    lang_key = f"name:{t.get('language', 'de')}"

    def localize(expr):
        if expr == ["get", "name_en"]:
            return ["get", lang_key]
        return [localize(e) for e in expr] if isinstance(expr, list) else expr
    fcfg = font_config().get(font, {})
    # Pixelschrift im 8-Bit-Modus: ohne scale, sonst sprängen zu viele Größen auf den doppelten Rasterschritt
    scale = t.get("text_scale", 1) * (1 if pixel and "grid" in fcfg else fcfg.get("scale", 1))
    r = lambda v: round(v * scale * 2) / 2
    for l in s["layers"]:
        lay = l.setdefault("layout", {})
        if "text-field" in lay:
            lay["text-field"] = localize(lay["text-field"])
        if "text-font" in lay:  # Basis nutzt "Noto Sans X"; Noto bleibt Ersatz für fehlende Zeichen
            lay["text-font"] = [f.replace("Noto Sans", font) for f in lay["text-font"]] + \
                ([] if font == "Noto Sans" else lay["text-font"])
            if l["id"].startswith("highway-name") and "streets" in fcfg:
                lay["text-font"][0] = lay["text-font"][0].replace("Regular", fcfg["streets"])
        size = lay.get("text-size")
        if size is not None and "shield" not in l["id"]:  # Schildtext muss ins Schild passen
            if isinstance(size, (int, float)):
                lay["text-size"] = r(size)
            elif size[0] == "interpolate":
                for i in range(4, len(size), 2):
                    size[i] = r(size[i])
        if pixel == 4 and "grid" not in fcfg and l["type"] == "symbol" and "text-field" in lay:
            # andere Schrift im 8-Bit-Modus: feste Größe in Rasterpixeln (sonst Kartengröße ×4); dither_tiles() rastert
            lay["text-size"] = PIXEL_TEXT
            l.setdefault("paint", {})["text-halo-blur"] = 0
        if "grid" in fcfg and l["type"] == "symbol":  # Pixelschrift: Größen aufs Raster, Halo ohne Weichzeichnung
            lay["text-size"] = fcfg["grid"] if pixel == 4 else on_grid(lay.get("text-size", 16), fcfg["grid"], 1 if pixel else 2)
            l.setdefault("paint", {})["text-halo-blur"] = 0
            if lay.get("symbol-placement", "point") != "point":  # Straßennamen waagerecht: schräg passt nie ins Raster
                lay["text-rotation-alignment"] = lay["text-pitch-alignment"] = "viewport"
        if any(fnmatch.fnmatch(l["id"], g) for g in t.get("hide", [])):
            lay["visibility"] = "none"
        # [paint."muster"] / [layout."muster"]: nur Eigenschaften, die zum Ebenentyp passen
        prefixes = ("text-", "icon-", "symbol-") if l["type"] == "symbol" else (l["type"] + "-",)
        for kind in ("paint", "layout"):
            for glob, props in t.get(kind, {}).items():
                if fnmatch.fnmatch(l["id"], glob):
                    l.setdefault(kind, {}).update(
                        {k: v for k, v in props.items() if k.startswith(prefixes) or k == "visibility"})
        if streets and (any(fnmatch.fnmatch(l["id"], g) for g in STREETS_DROP)
                        or not any(fnmatch.fnmatch(l["id"], g) for g in STREETS_KEEP)):
            lay["visibility"] = "none"
        if pixel:  # Stil wie auf der Zielzoomstufe auswerten, nur 1/pixel so groß gezeichnet (siehe zoom_shift)
            dz = pixel.bit_length() - 1
            for kind in ("paint", "layout"):
                for k, v in l.get(kind, {}).items():
                    if k != "text-size":
                        l[kind][k] = zoom_shift(v, dz)
            for k in ("line-width", "line-gap-width", "line-offset"):  # Breiten maßstäblich, Linien mindestens
                if k in l.get("paint", {}):                              # PIXEL_MIN_LINE, sonst reißen sie im Raster
                    l["paint"][k] = scale_out(l["paint"][k], 1 / pixel, PIXEL_MIN_LINE if k == "line-width" else 0)
            for k in ("minzoom", "maxzoom"):
                if k in l:
                    l[k] = max(0, l[k] - dz)
            # Straßenränder wären im groben Raster nur einen halben Pixel breit und zerfielen in Punkte; den Rand zieht
            # der Umriss in dither_tiles(). Leuchtränder (line-blur) bleiben.
            if l["id"].endswith("-casing") and l["type"] == "line" and not l.get("paint", {}).get("line-blur"):
                lay["visibility"] = "none"
        if pixel and "grid" in fcfg and "text-halo-color" in l.get("paint", {}):  # 8 Bit: Rand hält Raster von Schrift fern
            l["paint"]["text-halo-width"] = PIXEL_HALO * 2 // pixel
    # POI-Symbole: Phosphor im Kreis, Stärke nach Schriftgruppe, Farben aus dem Stil
    p, accent = t["paint"], t.get("marker", {}).get("color", "#888888")
    weight = {"mono": "bold", "pixel": "bold", "serif": "light"}.get(fcfg.get("group"), "regular")
    s["sprite"] = poi_sprite(weight, p["background"]["background-color"], accent, p["poi_*"]["text-color"],
                             t.get("mode") == "dark")
    if t.get("graticule") and center:
        graticule(s, center, accent, p["background"]["background-color"], font)
    return s, f"{t.get('title', Path(toml_path).stem)} · {font}", t.get("attribution", ""), font


def zoom_shift(expr, dz):
    """--pixel: zoomabhängige Ausdrücke dz Stufen früher. Die Vorfahrkachel wird dz Stufen gröber gerendert; so sieht
    sie aus wie die Zielzoomstufe (sonst fehlen z. B. Füllungen der Nebenstraßen, Breite 0 unter z13,5)."""
    if not isinstance(expr, list):
        return expr
    expr = [zoom_shift(e, dz) for e in expr]
    if expr[:1] in (["interpolate"], ["interpolate-hcl"], ["interpolate-lab"]) and expr[2] == ["zoom"]:
        expr[3::2] = [z - dz for z in expr[3::2]]
    elif expr[:1] == ["step"] and expr[1] == ["zoom"]:
        expr[3::2] = [z - dz for z in expr[3::2]]
    return expr


def scale_out(expr, k, least=0):
    """Zahl oder Ausgaben eines interpolate/step-Ausdrucks mal k, aber mindestens least (0 bleibt 0: unsichtbar)."""
    if isinstance(expr, (int, float)):
        return max(expr * k, least) if expr else expr
    if isinstance(expr, list) and expr[:1] in (["interpolate"], ["step"]):
        first = 4 if expr[0] == "interpolate" else 2
        return expr[:first] + [scale_out(v, k, least) if i % 2 == 0 else v for i, v in enumerate(expr[first:])]
    return expr


def on_grid(size, grid, sub=1):
    """text-size auf ganze Vielfache des Pixelrasters einer Pixelschrift (grid = Geviert in px bei 1 Schriftpixel
    = 1 Bildpixel). Zoomabhängige Größen werden je ganzer Stufe ausgewertet und als step-Ausdruck geschrieben,
    damit auch zwischen den Stützstellen kein Zwischenwert entsteht. sub = 2 (außerhalb von --pixel): auch halbe
    Schritte (VT323 18,75 px), die Kacheln sind dann ohnehin geglättet; kleiner als ein ganzer Schritt nie."""
    snap = lambda v: max(grid, round(v * sub / grid) * grid / sub)
    if isinstance(size, (int, float)):
        return snap(size)
    curve, stops = size[1], list(zip(size[3::2], size[4::2]))
    base = curve[1] if curve[0] == "exponential" else 1
    def at(z):
        if z <= stops[0][0]:
            return stops[0][1]
        for (z0, v0), (z1, v1) in zip(stops, stops[1:]):
            if z <= z1:
                f = (z - z0) / (z1 - z0) if base == 1 else (base ** (z - z0) - 1) / (base ** (z1 - z0) - 1)
                return v0 + (v1 - v0) * f
        return stops[-1][1]
    out = ["step", ["zoom"], snap(at(0))]
    for z in range(1, 23):
        if snap(at(z)) != snap(at(z - 1)):
            out += [z, snap(at(z))]
    return out if len(out) > 3 else out[2]


# Koordinatengitter: (Abstand in Grad, Nachkommastellen, Leaflet-Zoom von, bis); um den Mittelpunkt je 150 Linien.
# tileserver-gl zeichnet 256er-Kacheln eine Stufe tiefer (MapLibre rechnet in 512er-Kacheln), daher z - 1 im Stil.
GRID = [(0.1, 1, 0, 12), (0.02, 2, 12, 14), (0.01, 2, 14, 16), (0.002, 3, 16, 18), (0.001, 3, 18, 24)]


def graticule(s, center, color, bg, font):
    """Längen-/Breitengrade als GeoJSON-Linien direkt im Stil (Nerd-Stile, graticule = true): gestrichelt in der
    Akzentfarbe, unter der Beschriftung; Gradzahlen dezimal an den Linien entlang, nachrangig zu Karten-Namen."""
    feats = []
    for k, (d, nd, _, _) in enumerate(GRID):
        lat0, lon0 = round(center[0] / d) * d, round(center[1] / d) * d
        for i in range(-150, 151):
            la, lo = round(lat0 + i * d, 6), round(lon0 + i * d, 6)
            if -85 < la < 85:
                feats.append({"type": "Feature", "properties": {"k": k, "t": f"{abs(la):.{nd}f}°{'N' if la >= 0 else 'S'}"},
                              "geometry": {"type": "LineString", "coordinates": [[lon0 - 150 * d, la], [lon0 + 150 * d, la]]}})
            feats.append({"type": "Feature", "properties": {"k": k, "t": f"{abs(lo):.{nd}f}°{'E' if lo >= 0 else 'W'}"},
                          "geometry": {"type": "LineString", "coordinates": [[lo, max(-85, lat0 - 150 * d)], [lo, min(85, lat0 + 150 * d)]]}})
    s["sources"]["grid"] = {"type": "geojson", "data": {"type": "FeatureCollection", "features": feats}}
    lines, labels = [], []
    for k, (_, _, z0, z1) in enumerate(GRID):
        flt, rng = ["==", ["get", "k"], k], {"minzoom": max(0, z0 - 1), "maxzoom": z1 - 1}
        lines.append({"id": f"grid-{k}", "type": "line", "source": "grid", "filter": flt, **rng,
                      "paint": {"line-color": color, "line-opacity": 0.6, "line-width": 1, "line-dasharray": [3, 3]}})
        labels.append({"id": f"grid-label-{k}", "type": "symbol", "source": "grid", "filter": flt, **rng,
                       "layout": {"symbol-placement": "line", "symbol-spacing": 350, "text-field": ["get", "t"],
                                  "text-font": [f"{font} Regular", "Noto Sans Regular"], "text-size": 10},
                       "paint": {"text-color": color, "text-opacity": 0.75, "text-halo-color": bg, "text-halo-width": 1.5}})
    first_symbol = next(i for i, l in enumerate(s["layers"]) if l["type"] == "symbol")
    s["layers"][first_symbol:first_symbol] = lines   # Linien unter alle Beschriftungen und Symbole
    s["layers"] += labels                            # zuletzt = geringster Vorrang, Ortsnamen gewinnen


STROKE = {"light": 12, "regular": 16, "bold": 24}  # Phosphor-Strichstärken im 256er-Raster


def poi_sprite(weight, bg, accent, glyph, dark):
    """Sprite wie style/ofm(@2x), aber die POI-Bilder aus style/icons.toml neu: Phosphor-Symbol in der POI-Farbe
    auf einem Kreis in dezentem Akzent (dunkel 22 %, hell 16 % Akzent über dem Grund), Ring 45 %.
    Liegt in style/sprites/ (gitignored, im Container unter /data); je Kombination nur einmal erzeugt."""
    hexrgb = lambda h: [int(h[i:i + 2], 16) for i in (1, 3, 5)]
    mix = lambda t: "#%02x%02x%02x" % tuple(round(b + (a - b) * t) for b, a in zip(hexrgb(bg), hexrgb(accent)))
    disc, ring = mix(0.22 if dark else 0.16), mix(0.45)
    name = f"sprites/{weight}-{bg[1:]}-{accent[1:]}-{glyph[1:]}"
    icons = tomllib.loads((ROOT / "style" / "icons.toml").read_text())
    for sfx in ("", "@2x"):
        out = ROOT / "style" / f"{name}{sfx}.png"
        if out.exists():
            continue
        out.parent.mkdir(exist_ok=True)
        src = ROOT / "style" / f"ofm{sfx}"
        idx = json.loads(src.with_suffix(".json").read_text())
        w, h = map(int, subprocess.run(["magick", "identify", "-format", "%w %h", f"{src}.png"],
                                       capture_output=True, text=True, check=True).stdout.split())
        px = bytearray(subprocess.run(["magick", f"{src}.png", "RGBA:-"], capture_output=True, check=True).stdout)
        svg = []
        for key, r in idx.items():
            icon = icons.get(key.removesuffix("_11"))
            if not icon:
                continue
            for y in range(r["y"], r["y"] + r["height"]):  # altes Bild ausradieren
                px[(y * w + r["x"]) * 4:(y * w + r["x"] + r["width"]) * 4] = bytes(r["width"] * 4)
            d, pr = r["width"], r["pixelRatio"]
            f = ROOT / "vendor" / "phosphor" / weight / f"{icon}.svg"
            if not f.exists():  # eigene Ergänzung: Linien, Strichstärke je Phosphor-Stärke
                f = ROOT / "vendor" / "phosphor-extra" / f"{icon}.svg"
            body = re.sub(r"^<svg[^>]*>|</svg>\s*$", "", f.read_text()).replace(
                'stroke-width="16"', f'stroke-width="{STROKE[weight]}" color="{glyph}"')
            g = d * 0.62  # Symbolgröße relativ zum Kreis
            svg.append(f'<circle cx="{r["x"] + d / 2}" cy="{r["y"] + d / 2}" r="{d / 2 - pr / 2}" fill="{disc}" '
                       f'stroke="{ring}" stroke-width="{pr}"/>'
                       f'<g transform="translate({r["x"] + (d - g) / 2},{r["y"] + (d - g) / 2}) scale({g / 256})" '
                       f'fill="{glyph}">{body}</g>')
        base, over = out.with_suffix(".base.png"), out.with_suffix(".svg")
        subprocess.run(["magick", "-size", f"{w}x{h}", "-depth", "8", "RGBA:-", str(base)], input=bytes(px), check=True)
        over.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">{"".join(svg)}</svg>')
        over_png = out.with_suffix(".over.png")
        subprocess.run(["inkscape", "--export-type=png", f"--export-filename={over_png}", str(over)],
                       capture_output=True, check=True)
        subprocess.run(["magick", str(base), str(over_png), "-composite", str(out)], check=True)
        for f in (base, over, over_png):
            f.unlink()
        shutil.copy(src.with_suffix(".json"), out.with_suffix(".json"))
    return name


def write_page(out, cfg):
    """index.html einer Variante aus template.html und ihrer Konfiguration."""
    page = (ROOT / "template.html").read_text().replace("<title>Karte</title>", f"<title>{cfg['title']}</title>")
    (out / "index.html").write_text(page.replace("/*CONFIG*/{}", json.dumps(cfg, ensure_ascii=False)))


def write_previews(outdir):
    """Vorschauseite (index.html = streifen.html) + variants.js (Titel und Konfiguration aller Varianten) nach outdir."""
    index = outdir / "index.html"
    if not index.exists() or "variants.js" in index.read_text():  # fremde index.html (--out in eine Website) nie überschreiben
        shutil.copy(ROOT / "streifen.html", index)
    for old in ("compare.html", "streifen.html"):  # frühere Vorschauseiten
        (outdir / old).unlink(missing_ok=True)
    shutil.copy(ROOT / "vendor" / "streifen.css", outdir / "streifen.css")  # Tailwind, gebaut mit npm run css
    shutil.copytree(ROOT / "vendor" / "leaflet", outdir / "leaflet", dirs_exist_ok=True)
    names = sorted(d.name for d in outdir.iterdir() if (d / "config.json").exists())
    configs = {n: json.loads((outdir / n / "config.json").read_text()) for n in names}
    for c in configs.values():  # Marker in der Schrift des Stils
        c["font_url"] = marker_font(c.get("font", ""), outdir)
    titles = {n: c["title"] for n, c in configs.items()}
    (outdir / "variants.js").write_text(
        f"const VARIANTS = {json.dumps(names)};\n"
        f"const TITLES = {json.dumps(titles, ensure_ascii=False)};\n"
        f"const CONFIGS = {json.dumps(configs, ensure_ascii=False)};\n")


def reindex(outdir, label=None):
    """config.json (und ggf. index.html) aller Varianten aus den aktuellen Stil-Dateien neu schreiben, ohne Rendern."""
    for d in sorted(outdir.iterdir()):
        conf, page = d / "config.json", d / "index.html"
        if conf.exists():
            cfg = json.loads(conf.read_text())
        elif page.exists():  # ältere Ausgabe ohne config.json
            cfg = json.loads(re.search(r"const c = (\{.*\});", page.read_text())[1])
        else:
            continue
        st = ROOT / "styles" / f"{cfg['style']}.toml"
        if not st.exists():
            continue
        meta = tomllib.loads(st.read_text())
        cfg.update(category=meta.get("category", "standard"), mode=meta.get("mode", "light"),
                   family=meta.get("family", meta.get("title", st.stem)), attribution=meta.get("attribution", ""),
                   order=meta.get("order", 50), overlay=meta.get("overlay"),
                   marker=dict(meta.get("marker", {"type": "leaflet"}),
                               label=label or cfg.get("marker", {}).get("label", "hier")),
                   title=f"{meta.get('title', st.stem)} · {cfg['font']}")
        conf.write_text(json.dumps(cfg, ensure_ascii=False))
        if page.exists():
            write_page(d, dict(cfg, font_url=marker_font(cfg.get("font", ""), d)))
    write_previews(outdir)


@contextmanager
def tileserver(style, tag, mb):
    """tileserver-gl mit diesem Stil starten; liefert die Basis-URL, stoppt den Container danach."""
    built = DATA / f"style-{tag}.json"
    built.write_text(json.dumps(style, ensure_ascii=False))
    name = f"tiles-{PORT}"
    run("podman", "run", "-d", "--rm", "--name", name, "-p", f"127.0.0.1:{PORT}:8080",
        "-v", f"{ROOT / 'style'}:/data:Z", "-v", f"{mb}:/data/tiles.mbtiles:ro,Z",
        "-v", f"{built}:/data/style.json:ro,Z",
        TILESERVER, "--config", "/data/config.json")
    try:
        for _ in range(300):  # bis 60 s; Start dauert meist < 1 s
            try:
                fetch(f"http://127.0.0.1:{PORT}/health")
                break
            except OSError:
                time.sleep(0.2)
        else:
            sys.exit("tileserver-gl startet nicht: podman logs " + name)
        yield f"http://127.0.0.1:{PORT}/styles/map"
    finally:
        subprocess.run(["podman", "stop", name], capture_output=True)


def build_site(a):
    """Öffentliche Vorschau nach site/ (GitHub Pages): Einstellungen aus site.toml, je Stil die Schriften seiner Gruppe."""
    cfg = tomllib.loads((ROOT / "site.toml").read_text())
    mb = ensure_mbtiles(cfg["area"])
    s = argparse.Namespace(**vars(a))
    s.lat, s.lon, s.label, s.zoom = cfg["lat"], cfg["lon"], cfg["label"], cfg["zoom"]
    s.radius, s.viewport, s.retina = cfg["radius"], cfg["viewport"], cfg["retina"]
    s.detail_from, s.detail_radius = 99, cfg["radius"]  # kein Detailbereich
    site = ROOT / "site"
    site.mkdir(exist_ok=True)
    wanted = set()
    for st in sorted((ROOT / "styles").glob("*.toml")):
        meta = tomllib.loads(st.read_text())
        cat = meta.get("category", "standard")
        # Schriften der Gruppe, dazu für Gruppen in pixel = [...] eine 8-Bit-Variante (Schalter "8 Bit") und für
        # Gruppen in streets = [...] eine Nur-Straßen-Variante (Schalter "Straßen") in der ersten Schrift
        site_fonts = [meta["site_font"]] if "site_font" in meta else cfg["fonts"][cat]  # z. B. Phosphor: VT323
        variants = [(f, False, False) for f in site_fonts]
        variants += [("Silkscreen", 4, False)] if cat in cfg.get("pixel", []) else []
        variants += [(site_fonts[0], False, True)] if cat in cfg.get("streets", []) else []
        for font, s.pixel, s.streets_only in variants:
            suffix = "-8bit" if s.pixel else "-streets" if s.streets_only else ""
            out = site / f"{st.stem}-{font.lower().replace(' ', '-')}{suffix}"
            wanted.add(out)
            done = out / "config.json"
            keep = a.missing and done.exists()
            if keep and json.loads(done.read_text()).get("retina") == s.retina:
                continue
            render(s, st, out, mb, font, standalone=False, keep=keep)  # keep: nur fehlende Kacheln (z. B. @2x)
    for old in site.glob("*/config.json"):              # Varianten aus früheren site.toml-Ständen (andere Schrift/Ort)
        if old.parent not in wanted:
            shutil.rmtree(old.parent)
    write_previews(site)
    (site / ".nojekyll").touch()                          # GitHub Pages: Dateien unverändert ausliefern
    size = sum(f.stat().st_size for f in site.rglob("*") if f.is_file())
    print(f"site/: {size / 1e6:.0f} MB")


def quantize(data, colors):
    """PNG auf eine Palette reduzieren (pngquant, ohne Dithering)."""
    return subprocess.run(["pngquant", str(colors), "--nofs", "--strip", "--speed", "1", "-"],
                          input=data, capture_output=True, check=True).stdout


def optimize(files):
    """PNGs verlustfrei nachkomprimieren (oxipng, falls installiert), erst nach dem Rendern: oxipng nutzt dann
    alle Kerne allein. Gemessen: 32 Farben + oxipng so groß wie 24 Farben ohne, aber genauer."""
    files = [str(f) for f in files]
    if OXIPNG and files:  # ponytail: -o 2; -o 4 spart nur 0,3–1 % mehr bei doppelter Zeit
        subprocess.run([OXIPNG, "-q", "-o", "2", "--strip", "safe", *files], check=True)


def marker_font(font, dest):
    """Schriftdatei für den Marker nach dest/fonts/<schrift>/: die unveränderte Originaldatei (Fett, bei Pixelschriften
    Normal; variable Schriften ganz) samt Lizenzdateien. Keine Teilmenge: das wäre nach der OFL eine veränderte Fassung,
    und viele Schriften haben einen reservierten Namen. Gibt die URL relativ zu dest zurück."""
    cfg = font_config().get(font)
    if not cfg:
        return None
    src = ROOT / "fonts-src" / cfg["Regular" if cfg.get("group") == "pixel" else "Bold"]["file"]
    d = dest / "fonts" / font.lower().replace(" ", "-")
    d.mkdir(parents=True, exist_ok=True)
    for f in [src] + [f for f in src.parent.iterdir() if re.match(r"(OFL|LICEN[CS]E|GUST)", f.name, re.I)]:
        if not (d / f.name).exists():
            shutil.copy(f, d / f.name)
    return f"fonts/{d.name}/{src.name}"


OXIPNG = shutil.which("oxipng") or shutil.which(str(Path.home() / ".cargo/bin/oxipng"))


@functools.lru_cache(maxsize=None)
def parent(url):
    """Elternkachel für --pixel; jede wird von vier Kindern (und @2x) gebraucht."""
    return fetch(url)


PIXEL_TEXT = 11  # --pixel 4 mit normaler Schrift: Geviert in Rasterpixeln (9 unlesbar; Regel in CLAUDE.md)
PIXEL_SS = 3  # --pixel: Vorfahrkachel in 3-facher Auflösung, je 3×3 = ein 8-Bit-Pixel (Schrift rastet ins Pixelraster)


def lowres(data, f, qx, qy):
    """--pixel f: Stück (qx, qy) der Vorfahrkachel (f = 2: Eltern, 4: Großeltern), in PIXEL_SS-facher Auflösung
    gerendert = die 256/f echten 8-Bit-Pixel der Kachel, je PIXEL_SS² Bildpixel. Die Vorfahrkachel ist im Stil gröber
    gezeichnet, Striche und Schrift sind also 1/f so groß; dither_tiles() fasst zusammen und vergrößert um f."""
    from PIL import Image
    s = 256 * PIXEL_SS // f
    im = Image.open(io.BytesIO(data)).convert("RGBA").crop((qx * s, qy * s, qx * s + s, qy * s + s))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


PIXEL_MIN_LINE = 1.7  # --pixel: Mindestbreite von Linien in Rasterpixeln, sonst reißen sie im Raster ab
PIXEL_COLORS = 16   # --pixel: Farben der Karte je Stil (eine Palette für alle Kacheln)
ROAD_GLOBS = ("minor", "service", "link", "secondary", "primary", "trunk", "motorway", "path")  # --pixel: Umrisse
LABEL_COLORS = 8    # --pixel: Farben der Beschriftungsebene (Schrift, Rand, Symbole), kommen zur Palette dazu
OUTLINE_STEP = 24   # --pixel: Helligkeitssprung (0–255), ab dem ein Flächenpixel zum Umriss wird
PIXEL_HALO = 2      # --pixel: Randbreite um Schrift (px im 128er-Raster, also 2 Schriftpixel)
TEXT_MERGE = 24     # --pixel: Textfarben näher als das (RGB-Abstand) werden eine Palettenfarbe


def style_colors(toml_path):
    """Alle Hex-Farben der Stil-Datei und die Textfarben darunter (auch in match-Ausdrücken)."""
    src = Path(toml_path).read_text()
    texts = set(re.findall(r'#[0-9a-fA-F]{6}', " ".join(re.findall(r'text-color\s*=(.*)', src))))
    return sorted(set(re.findall(r'"(#[0-9a-fA-F]{6})"', src))), texts


def pixel_palette(px, cand, force=(), n=PIXEL_COLORS):
    """Palette aus den Farben cand (Hex) der Stil-Datei: jede gewichtet mit der Zahl der Pixel px, die ihr am nächsten
    liegen. Erst die häufigste, dann alle Farben aus force, auch ohne Gewicht (dünne Schrift hat kaum reine Pixel),
    fast gleiche zusammengefasst; dann jeweils die mit dem größten Abstand × log(Gewicht)."""
    import numpy as np
    cv = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in cand], float)
    u, c = np.unique(px, axis=0, return_counts=True)
    w = np.bincount((((u[:, None].astype(float) - cv[None]) ** 2).sum(-1)).argmin(1), weights=c, minlength=len(cv))
    order = np.argsort(-w)
    pal = [cv[order[0]]]
    for i in order:
        if cand[i] in force and min(((cv[i] - q) ** 2).sum() for q in pal) > TEXT_MERGE ** 2:
            pal.append(cv[i])
    pal = pal[:n]
    while len(pal) < n:
        score = np.min([((cv - q) ** 2).sum(1) for q in pal], axis=0) ** .5 * np.log1p(w)
        if score.max() <= 0:  # keine weitere Farbe kommt in den Pixeln vor
            break
        pal.append(cv[score.argmax()])
    return np.array(pal)


def split_labels(style):
    """--pixel: Stil in Karte ohne Beschriftung und Beschriftung allein (transparenter Grund) teilen. MapLibre richtet
    Beschriftungen nur nach anderen Beschriftungen aus. Die Beschriftung wird eine Stufe feiner gerendert als die Karte
    (OpenMapTiles hat POIs erst ab z14, zwei Stufen gröber fehlten sie ganz): Zoomverschiebung eine Stufe zurück,
    Schrift und Rand doppelt so groß, dither_tiles() fasst doppelt so große Blöcke zusammen."""
    m, lab = json.loads(json.dumps(style)), json.loads(json.dumps(style))
    for l in m["layers"]:
        if l["type"] == "symbol":
            l.setdefault("layout", {})["visibility"] = "none"
    for l in lab["layers"]:
        lay, paint = l.setdefault("layout", {}), l.setdefault("paint", {})
        if l["type"] != "symbol":
            lay["visibility"] = "none"
            continue
        for kind in (lay, paint):
            for k, v in kind.items():
                if k != "text-size":
                    kind[k] = zoom_shift(v, -1)
        for k in ("minzoom", "maxzoom"):
            if k in l:
                l[k] += 1
        if "text-size" in lay:
            lay["text-size"] = scale_out(lay["text-size"], 2)
        if "text-halo-width" in paint:
            paint["text-halo-width"] = scale_out(paint["text-halo-width"], 2)
    return m, lab


def snap_labels(li, text, n, b):
    """Beschriftung ins 8-Bit-Raster: MapLibre setzt sie auf Bruchteile von Pixeln, Striche liegen dann halb in zwei
    b×b-Blöcken und keiner bekommt genug (Querbalken verschwinden). Je Beschriftung (zusammenhängende Pixel der
    Ebene) die Verschiebung um 0 bis b-1 Bildpixel wählen, bei der die Schrift die Blöcke am eindeutigsten
    füllt oder frei lässt. li: Palettenindex je Bildpixel (-1 = leer), text: Schriftmaske."""
    import numpy as np
    from scipy import ndimage
    lab, _ = ndimage.label(ndimage.binary_dilation(li >= 0, iterations=b))
    out = np.full_like(li, -1)
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        own = lab[sl] == i
        part, tpart = np.where(own, li[sl], -1), text[sl] & own
        best = None
        for dy in range(b):
            for dx in range(b):
                tmp = np.zeros(li.shape, bool)
                tmp[sl] = np.roll(tpart, (dy, dx), (0, 1))  # Rand der Region ist leer (Dilatation), kein Umlauf
                c = tmp.reshape(n, b, n, b).sum((1, 3))
                score = np.minimum(c, b * b - c).sum()
                if best is None or score < best[0]:
                    best = (score, dy, dx)
        shifted = np.roll(part, best[1:], (0, 1))
        out[sl] = np.where(shifted >= 0, shifted, out[sl])
    return out


def dither_tiles(files, toml_path, retina):
    """--pixel, zweiter Durchgang im Stil von 8-Bit-Kunst. Karte (f) und Beschriftung (f.labels.png, transparent)
    kommen getrennt in PIXEL_SS-facher Auflösung. Karte: eine Palette für alle Kacheln, je PIXEL_SS² Bildpixel die
    häufigste Palettenfarbe (Leuchtschein und Glättung werden harte Stufen), verirrte Einzelpixel weg, dunkle Umrisse,
    Wasser mit Wellenstrichen und Grün mit Punktmuster. Beschriftung: eigene kleine Palette, ins Raster gerückt, je
    Block Schrift ab 4/9 Deckung, sonst Rand/Symbol ab 4/9; dann in die Kachel eingebacken. Ohne Glättung auf 256
    (@2x 512) px."""
    import numpy as np
    from PIL import Image
    t = tomllib.loads(Path(toml_path).read_text())
    cand, texts = style_colors(toml_path)
    maps = {f: np.asarray(Image.open(f).convert("RGB")) for f in files}
    labs = {f: np.asarray(Image.open(f.with_suffix(".labels.png")).convert("RGBA")) for f in files}
    sample = np.concatenate([m[::2, ::2].reshape(-1, 3) for m in maps.values()])
    pal = pixel_palette(sample, cand)
    ls = np.concatenate([l[l[..., 3] > 200][:, :3] for l in labs.values()] + [np.zeros((1, 3), np.uint8)])
    lpal = pixel_palette(ls, cand, texts, LABEL_COLORS)
    is_text = np.array([any(((lpal[i] - np.array([int(h[j:j + 2], 16) for j in (1, 3, 5)])) ** 2).sum()
                            <= TEXT_MERGE ** 2 for h in texts) for i in range(len(lpal))])
    hexrgb = lambda h: np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)
    nearest = lambda c, skip=-1: int(np.where(np.arange(len(pal)) == skip, np.inf, ((pal - c) ** 2).sum(1)).argmin())
    ink = hexrgb(t["paint"]["label_*"]["text-color"])
    n = next(iter(maps.values())).shape[0] // PIXEL_SS  # 128 oder 64 echte Pixel je Kachel
    y, x = np.mgrid[:n, :n]
    textures = []  # (Palettenindex der Fläche, Musterfarbe, Maske)
    for key, mask in [("water*", (y % 4 == 1) & ((x + 3 * (y // 4)) % 8 < 3)),          # Wellenstriche
                      ("park", ((x % 4 == 0) & (y % 4 == 0)) | ((x % 4 == 2) & (y % 4 == 2)))]:  # Punkte
        c = t["paint"].get(key, {}).get("fill-color")
        i = nearest(hexrgb(c)) if c else 0
        if i > 0 and i not in [j for j, _, _ in textures]:  # nur eigene Flächenfarbe, nie der Grund (0)
            textures.append((i, nearest(pal[i] * .65 + ink * .35, skip=i), mask))
    # Umrisse wie in Sierra-Spielen: Flächenpixel (Grund, Landnutzung, Gebäude …: je > 3 % der Pixel) neben einem
    # deutlich helleren Pixel werden zur dunkelsten Farbe; Leuchtstufen lösen das nicht aus
    lum = pal @ [.299, .587, .114]
    share = np.bincount(((sample[:, None].astype(float) - pal) ** 2).sum(-1).argmin(1), minlength=len(pal)) / len(sample)
    area, dark = share > .03, int(lum.argmin())
    road = np.zeros(len(pal), bool)  # Palettenfarben der Straßen und Wege (line-color der Straßen-Muster im Stil)
    for glob, props in t.get("paint", {}).items():
        if any(k in glob for k in ROAD_GLOBS) and isinstance(props.get("line-color"), str):
            road[nearest(hexrgb(props["line-color"]))] = True
    flat = [int(v) for v in np.concatenate([pal, lpal]).flatten()]
    flat += [0] * (768 - len(flat))
    blocks = lambda m: m.reshape(n, PIXEL_SS, n, PIXEL_SS).transpose(0, 2, 1, 3).reshape(n, n, -1, 1)
    near = lambda img, p: (((img[..., None, :].astype(float) - p) ** 2).sum(-1)).argmin(-1)
    out = []
    for f in files:
        idx = (blocks(near(maps[f], pal)) == np.arange(len(pal))).sum(2).argmax(-1)  # je Block die häufigste Farbe
        # verirrte Einzelpixel: alle vier Nachbarn gleich und anders als das Pixel -> Nachbarfarbe
        p = np.pad(idx, 1, mode="edge")
        n4 = np.stack([p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]])
        idx = np.where((n4 == n4[0]).all(0) & (n4[0] != idx), n4[0], idx)
        p = np.pad(idx, 1, mode="edge")
        n4 = np.stack([p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]])
        # Umriss nur an Straßen und Wegen (nicht an Gebäuden und Landnutzung, sonst bekommt jeder helle Fleck schwarze
        # Nachbarn), und nur neben Stellen aus mindestens zwei Pixeln; einzeln übrig gebliebene Umrisspixel fallen weg
        twin = np.pad((n4 == idx).any(0), 1)
        t4 = np.stack([twin[:-2, 1:-1], twin[2:, 1:-1], twin[1:-1, :-2], twin[1:-1, 2:]])
        edge = (np.where(t4 & road[n4], lum[n4], -1e9).max(0) - lum[idx] > OUTLINE_STEP) & area[idx]
        e = np.pad(edge, 1)
        friends = sum(e[1 + dy:e.shape[0] - 1 + dy, 1 + dx:e.shape[1] - 1 + dx]
                      for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
        idx = np.where(edge & (friends > 0), dark, idx)
        for i, c, mask in textures:
            idx = np.where((idx == i) & mask, c, idx)
        # Beschriftung: deckende Pixel auf die Beschriftungspalette, ins Raster rücken, je Block entscheiden
        l = labs[f]
        li = np.where(l[..., 3] > 127, near(l[..., :3], lpal), -1)
        b = 2 * PIXEL_SS  # Beschriftung eine Stufe feiner gerendert (split_labels)
        li = snap_labels(li, (li >= 0) & is_text[np.maximum(li, 0)], n, b)
        cnt = (li.reshape(n, b, n, b).transpose(0, 2, 1, 3).reshape(n, n, -1, 1) == np.arange(len(lpal))).sum(2)
        tc = np.where(is_text, cnt, 0)
        need = b * b * 4 / 9
        lab = np.where(tc.sum(-1) >= need, tc.argmax(-1), np.where(cnt.sum(-1) >= need, cnt.argmax(-1), -1))
        idx = np.where(lab >= 0, len(pal) + lab, idx)
        f.with_suffix(".labels.png").unlink()
        im = Image.fromarray(idx.astype(np.uint8), "P")
        im.putpalette(flat)
        if retina:
            out.append(f.with_name(f.stem + "@2x.png"))
            im.resize((512, 512), Image.NEAREST).save(out[-1])
        im.resize((256, 256), Image.NEAREST).save(f)
        out.append(f)
    return out


def readme_previews(a, mb):
    """Je Stil ein 512×512-Bild auf Zoom 12 ohne Marker nach docs/previews/<stil>.png (für die README)."""
    dest = ROOT / "docs" / "previews"
    dest.mkdir(parents=True, exist_ok=True)
    for st in sorted((ROOT / "styles").glob("*.toml")):
        meta = tomllib.loads(st.read_text())
        style = build_style(st, meta.get("preview_font", meta.get("font")), (a.lat, a.lon))[0]
        with tileserver(style, f"readme-{st.stem}", mb) as base:
            data = fetch(f"{base}/static/{a.lon},{a.lat},12/512x512.png")
        data = quantize(data, a.colors)
        (dest / f"{st.stem}.png").write_bytes(data)
        optimize([dest / f"{st.stem}.png"])
        data = (dest / f"{st.stem}.png").read_bytes()
        print(f"{st.stem}: {len(data) / 1e3:.0f} kB", flush=True)


def render(a, style_file, out, mb, font=None, standalone=True, keep=False):
    """Kacheln + config.json nach out/; standalone: zusätzlich eigene index.html mit Leaflet (Website-Karte)."""
    zmin, zmax = map(int, a.zoom.split("-"))
    vw, vh = map(int, a.viewport.split("x"))
    b = bbox(a.lat, a.lon, a.radius)
    # ponytail: high zooms only near the marker; Leaflet upscales z(detail_from-1) outside
    d = bbox(a.lat, a.lon, min(a.radius, a.detail_radius))
    style, title, attribution, font = build_style(style_file, font, (a.lat, a.lon), a.pixel, a.streets_only)
    if a.pixel:  # Beschriftung getrennt rendern, dither_tiles() backt sie ein
        style, labels = split_labels(style)
    crops = []   # --pixel: (Kachel, URL der Beschriftungs-Vorfahrkachel ohne Basis, f, qx, qy)
    with tileserver(style, out.name, mb) as base:
        if not keep:  # keep: vorhandene Kacheln behalten (z. B. nur @2x ergänzen)
            shutil.rmtree(out / "tiles", ignore_errors=True)
        jobs = [(z, x, y, sfx) for z in range(zmin, zmax + 1)
                for x, y in (tiles_for(d, z, 0, 0) if z >= a.detail_from else tiles_for(b, z, vw, vh))
                for sfx in (["", "@2x"] if a.retina else [""])]

        ext = "webp" if a.format == "webp" else "png"
        parent.cache_clear()  # gleiche URL (Port 8089) für jeden Stil
        if a.pixel and ext != "png":
            sys.exit("--pixel nur mit PNG")
        if ext == "png" and not shutil.which("pngquant"):
            sys.exit("pngquant fehlt (für --format png): sudo dnf install pngquant, oder --format webp")

        def get(job):
            z, x, y, sfx = job
            f = out / "tiles" / str(z) / str(x) / f"{y}{sfx}.{ext}"
            if keep and f.exists():
                return None
            f.parent.mkdir(parents=True, exist_ok=True)
            if a.pixel:  # 8-Bit: Viertel der Elternkachel; Palette, Muster und @2x erst in dither_tiles()
                if sfx:
                    return None
                n, fl = a.pixel.bit_length() - 1, a.pixel // 2  # Zoomstufen nach oben; Beschriftung eine weniger
                crops.append((f, f"/{z - n + 1}/{x >> n - 1}/{y >> n - 1}@{PIXEL_SS}x.png", fl, x % fl, y % fl))
                f.write_bytes(lowres(parent(f"{base}/{z - n}/{x >> n}/{y >> n}@{PIXEL_SS}x.png"),
                                     a.pixel, x % a.pixel, y % a.pixel))
                return f
            else:
                data = fetch(f"{base}/{z}/{x}/{y}{sfx}.{ext}")
            if ext == "png":  # Palette mit wenigen Farben, ohne Dithering (gemessen: kleiner als WebP, gleiche Qualität)
                data = quantize(data, a.colors)
            f.write_bytes(data)
            return f if ext == "png" else None

        # tileserver-gl rendert parallel (Renderer-Pools in style/config.json); so viele Anfragen gleichzeitig
        with ThreadPoolExecutor(WORKERS) as pool:
            written = [f for f in pool.map(get, jobs) if f]
        count = len(jobs)
    if a.pixel:
        parent.cache_clear()
        with tileserver(labels, out.name + "-labels", mb) as base:
            with ThreadPoolExecutor(WORKERS) as pool:
                list(pool.map(lambda c: c[0].with_suffix(".labels.png").write_bytes(
                    lowres(parent(base + c[1]), *c[2:])), crops))
        written = dither_tiles(written, style_file, a.retina)
    optimize(written)  # nach dem Stoppen des Containers

    cfg = dict(lat=a.lat, lon=a.lon, zmin=zmin, zmax=zmax, retina=a.retina,
               detail_from=a.detail_from, bounds=[[b[0], b[1]], [b[2], b[3]]],
               detail=[[d[0], d[1]], [d[2], d[3]]], attribution=attribution,
               style=Path(style_file).stem, font=font, ext=ext, pixel=a.pixel, streets=a.streets_only)
    meta = tomllib.loads(Path(style_file).read_text())  # Gliederung der Vorschau
    cfg.update(category=meta.get("category", "standard"), mode=meta.get("mode", "light"),
               family=meta.get("family", meta.get("title", Path(style_file).stem)), order=meta.get("order", 50),
               overlay=meta.get("overlay"),
               marker=dict(meta.get("marker", {"type": "leaflet"}), label=a.label or "hier"), title=title)
    (out / "config.json").write_text(json.dumps(cfg, ensure_ascii=False))  # liest write_previews()
    if standalone:  # eigenständige Kartenseite; für die Vorschau-Seite (--site) nicht nötig
        shutil.copytree(ROOT / "vendor" / "leaflet", out / "leaflet", dirs_exist_ok=True)
        write_page(out, dict(cfg, font_url=marker_font(font, out)))
    write_previews(out.parent)
    size = sum(f.stat().st_size for f in (out / "tiles").rglob(f"*.{ext}"))
    print(f"{count} Kacheln, {size / 1e6:.1f} MB -> {out}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lat", type=float, default=52.0211, help="Standard: Bielefeld")
    p.add_argument("--lon", type=float, default=8.5347)
    p.add_argument("--place", help='Ortsname oder Adresse statt --lat/--lon, z. B. "Sparrenburg, Bielefeld" (Nominatim)')
    p.add_argument("--radius", type=float, default=5, help="km um den Marker")
    p.add_argument("--zoom", default="10-18", help="z. B. 10-14")
    p.add_argument("--detail-from", type=int, default=17, help="ab dieser Stufe nur --detail-radius")
    p.add_argument("--detail-radius", type=float, default=1, help="km, für die Detailstufen")
    p.add_argument("--viewport", default="2560x1440", help="größte Kartengröße in px")
    p.add_argument("--area", default="detmold-regbez", help="Geofabrik-Name")
    p.add_argument("--retina", action="store_true", help="zusätzlich @2x rendern")
    p.add_argument("--format", choices=["png", "webp"], default="png",
                   help="png = Palette über pngquant (Standard, kleinste Dateien), webp = direkt vom tileserver")
    p.add_argument("--pixel", type=int, nargs="?", const=4, default=0, choices=[2, 4],
                   help="8-Bit-Look: jede Kachel aus der 2 (Standard 4) bzw. 1 (2) Stufen gröberen Kachel, Pixel ohne "
                        "Glättung 4- bzw. 2-fach, flache Farben mit Umrissen; Schrift Silkscreen bzw. VT323")
    p.add_argument("--streets-only", action="store_true",
                   help="nur Straßennetz, Wasser und Ortsnamen (Poster-Look); mit --all: Ausgabe out/<stil>-<schrift>-streets")
    p.add_argument("--colors", type=int, default=32, help="Farben je PNG-Kachel (pngquant), Standard 32")
    p.add_argument("--label", help="Text im Terminal-Marker der Nerd-Stile (~/<label>), Standard: hier")
    p.add_argument("--style", help="Standard: styles/clear.toml; mit --all: nur dieser Stil")
    p.add_argument("--font", help="Schrift statt der des Stils; mit --all: nur diese Schrift")
    p.add_argument("--all", action="store_true", help="jeder Stil in seiner preview_font nach out/<stil>-<schrift>")
    p.add_argument("--all-fonts", action="store_true", help="mit --all: jede Schrift der Gruppen des Stils statt nur preview_font")
    p.add_argument("--missing", action="store_true", help="mit --all: vorhandene Varianten überspringen")
    p.add_argument("--out", help="Standard: out/<stilname>")
    p.add_argument("--reindex", action="store_true", help="nur index.html aller Varianten in out/ neu schreiben")
    p.add_argument("--site", action="store_true", help="öffentliche Vorschau laut site.toml nach site/ (GitHub Pages)")
    p.add_argument("--readme-previews", action="store_true",
                   help="je Stil ein 512×512-Bild (Zoom 12, ohne Marker) nach docs/previews/ für die README")
    a = p.parse_args()
    if a.place:
        a.lat, a.lon = geocode(a.place)
    if a.pixel and not a.font:
        a.font = "VT323" if a.pixel == 2 else "Silkscreen"  # Alternativen in fonts.toml: Press Start 2P
    if a.reindex:
        for d in (ROOT / "out", ROOT / "site"):
            if d.exists():
                reindex(d, a.label)
        return
    zmin, zmax = map(int, a.zoom.split("-"))
    if not (0 <= zmin <= zmax <= 20):
        sys.exit("--zoom ungültig")

    if a.site:
        ensure_noto()
        ensure_glyphs()
        return build_site(a)
    mb = ensure_mbtiles(a.area)
    ensure_noto()
    ensure_glyphs()
    if a.readme_previews:
        return readme_previews(a, mb)
    if not a.all:
        st = Path(a.style or ROOT / "styles" / "clear.toml")
        render(a, st, Path(a.out) if a.out else ROOT / "out" / st.stem, mb, a.font)
        return
    for st in [Path(a.style)] if a.style else sorted((ROOT / "styles").glob("*.toml")):
        meta = tomllib.loads(st.read_text())
        if a.font:
            todo = [a.font]
        elif a.all_fonts:  # volle Matrix: jede Schrift der Gruppen des Stils
            todo = fonts(meta.get("fonts", ["sans", "serif"]))
        else:              # Vorschau: nur die Vorschau-Schrift des Stils
            todo = [meta.get("preview_font", meta.get("font", "Fira Sans"))]
        for font in todo:
            out = ROOT / "out" / f"{st.stem}-{font.lower().replace(' ', '-')}{'-streets' if a.streets_only else ''}"
            if a.missing and (out / "index.html").exists():
                continue
            render(a, st, out, mb, font)


if __name__ == "__main__":
    main()
