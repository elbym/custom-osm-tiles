#!/usr/bin/env python3
"""Statische Leaflet-Kacheln für einen kleinen Bereich rendern.

Beispiel:
  ./make-tiles.py                               # styles/clear.toml, Bielefeld -> out/clear
  ./make-tiles.py --lat 52.115 --lon 8.67 --style styles/north.toml --out out/kunde-xy
  ./make-tiles.py --all --zoom 16-16 --radius 1.5 --retina   # jeder Stil × jede Schrift zum Vergleichen
"""
import argparse, fnmatch, functools, os, re, io, tempfile, json, math, shutil, subprocess, sys, time, tomllib, urllib.request, zipfile
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
            axes = [f"{k}={v}" for k, v in spec.items() if k not in ("file", "slant")]
            if axes:
                run(sys.executable, "-m", "fontTools.varLib.instancer", str(src), *axes, "-o", str(out))
            else:
                shutil.copy(src, out)
            if "slant" in spec:
                oblique(out, spec["slant"])
        run(tool, tmp, str(dest))


def oblique(path, deg):
    """Schrift ohne Kursive: alle Glyphen um deg Grad nach rechts neigen (unechte Kursive, slant = 10 in fonts.toml).
    Nur TrueType-Umrisse (glyf), also TTF oder daraus instanziierte variable Schriften."""
    from fontTools.pens.transformPen import TransformPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import TTFont
    f = TTFont(path)
    gs, glyf, skew = f.getGlyphSet(), f["glyf"], (1, 0, math.tan(math.radians(deg)), 1, 0, 0)
    new = {}
    for name in f.getGlyphOrder():
        pen = TTGlyphPen(gs)
        gs[name].draw(TransformPen(pen, skew))
        new[name] = pen.glyph()
    for name, g in new.items():  # erst danach ersetzen: zusammengesetzte Glyphen lesen sonst schon geneigte Teile
        glyf[name] = g
        g.recalcBounds(glyf)
        # linker Rand in hmtx = neues xMin, sonst verschiebt FreeType den Umriss (falsche Abstände)
        f["hmtx"][name] = (f["hmtx"][name][0], getattr(g, "xMin", 0))
    f.save(path)


# --streets-only: nur Straßennetz, Wasser und Ortsnamen (Poster-Look wie maptoposter); Straßennamen, Schilder,
# Bahn, Gebäude, Landnutzung und POIs fallen weg. DROP gewinnt vor KEEP.
STREETS_KEEP = ["background", "water", "water-intermittent", "waterway-*", "highway-*", "bridge-*", "tunnel-*", "label_*"]
STREETS_DROP = ["highway-name-*", "highway-shield-*", "highway-area", "*railway*", "waterway_*label"]


def build_style(toml_path, font=None, center=None, pixel=False, streets=False):
    """styles/<name>.toml + style/base.json (OSM Bright) -> fertiger Stil, Titel, Namensnennung.
    center (lat, lon): Mittelpunkt für das Koordinatengitter (graticule = true im Stil).
    pixel: 8-Bit-Modus, Pixelschriften dann nur in ganzen Rasterschritten. streets: siehe STREETS_KEEP."""
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
        if "grid" in fcfg and l["type"] == "symbol":  # Pixelschrift: Größen aufs Raster, Halo ohne Weichzeichnung
            lay["text-size"] = on_grid(lay.get("text-size", 16), fcfg["grid"], 1 if pixel else 2)
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
        if pixel and "grid" in fcfg and "text-halo-color" in l.get("paint", {}):  # 8 Bit: Rand hält Raster von Schrift fern
            l["paint"]["text-halo-width"] = PIXEL_HALO
    # POI-Symbole: Phosphor im Kreis, Stärke nach Schriftgruppe, Farben aus dem Stil
    p, accent = t["paint"], t.get("marker", {}).get("color", "#888888")
    weight = {"mono": "bold", "pixel": "bold", "serif": "light"}.get(fcfg.get("group"), "regular")
    s["sprite"] = poi_sprite(weight, p["background"]["background-color"], accent, p["poi_*"]["text-color"],
                             t.get("mode") == "dark")
    if t.get("graticule") and center:
        graticule(s, center, accent, p["background"]["background-color"], font)
    return s, f"{t.get('title', Path(toml_path).stem)} · {font}", t.get("attribution", ""), font


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
    """Vergleichsseiten + variants.js (Titel und Konfiguration aller Varianten) nach outdir."""
    for f in ("compare.html", "streifen.html"):
        shutil.copy(ROOT / f, outdir / f)
    shutil.copy(ROOT / "vendor" / "streifen.css", outdir / "streifen.css")  # Tailwind, gebaut mit npm run css
    shutil.copytree(ROOT / "vendor" / "leaflet", outdir / "leaflet", dirs_exist_ok=True)
    names = sorted(d.name for d in outdir.iterdir() if (d / "config.json").exists())
    configs = {n: json.loads((outdir / n / "config.json").read_text()) for n in names}
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
            write_page(d, cfg)
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
        variants += [("VT323", True, False)] if cat in cfg.get("pixel", []) else []
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
    (site / "compare.html").unlink(missing_ok=True)       # veröffentlicht wird nur die Streifen-Ansicht
    shutil.move(site / "streifen.html", site / "index.html")
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


OXIPNG = shutil.which("oxipng") or shutil.which(str(Path.home() / ".cargo/bin/oxipng"))


@functools.lru_cache(maxsize=None)
def parent(url):
    """Elternkachel für --pixel; jede wird von vier Kindern (und @2x) gebraucht."""
    return fetch(url)


def lowres(data, qx, qy):
    """--pixel: Viertel (qx, qy) der 256er-Elternkachel = die 128×128 echten 8-Bit-Pixel der Kachel. Die Elternkachel
    ist im Stil eine Stufe gröber gezeichnet, Striche und Schrift sind also halb so groß; dither_tiles() verdoppelt."""
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB").crop((qx * 128, qy * 128, qx * 128 + 128, qy * 128 + 128))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


PIXEL_COLORS = 16   # --pixel: Farben je Stil (eine Palette für alle Kacheln)
PIXEL_HALO = 2      # --pixel: Randbreite um Schrift (px im 128er-Raster, also 2 Schriftpixel)
TEXT_MERGE = 24     # --pixel: Textfarben näher als das (RGB-Abstand) werden eine Palettenfarbe
TEXT_SNAP = 40      # --pixel: Pixel so nah an einer Textfarbe werden ohne Raster abgebildet (Schrift bleibt glatt)
BAYER_SPREAD = 40   # Stärke des Musters (RGB-Einheiten); höher = mehr Raster, auch auf reinen Flächen


def pixel_palette(px, toml_path, n=PIXEL_COLORS):
    """Palette aus den Farben der Stil-Datei: jede Hex-Farbe gewichtet mit der Zahl der Pixel, die ihr am nächsten
    liegen. Erst die häufigste Farbe, dann alle Textfarben des Stils, auch ohne Gewicht (dünne, geglättete Schrift hat
    kaum reine Pixel), fast gleiche zusammengefasst; dann jeweils die mit dem größten Abstand × log(Gewicht).
    Gibt (Palette, Anzahl Textfarben hinter Index 0) zurück."""
    import numpy as np
    src = Path(toml_path).read_text()
    cand = sorted(set(re.findall(r'"(#[0-9a-fA-F]{6})"', src)))
    texts = set(re.findall(r'#[0-9a-fA-F]{6}', " ".join(re.findall(r'text-color\s*=(.*)', src))))  # auch in match
    cv = np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in cand], float)
    u, c = np.unique(px, axis=0, return_counts=True)
    w = np.bincount((((u[:, None].astype(float) - cv[None]) ** 2).sum(-1)).argmin(1), weights=c, minlength=len(cv))
    order = np.argsort(-w)
    pal = [cv[order[0]]]
    for i in order:
        if cand[i] in texts and min(((cv[i] - q) ** 2).sum() for q in pal) > TEXT_MERGE ** 2:
            pal.append(cv[i])
    pal = pal[:n // 2]  # ponytail: mehr als 7 Textfarben hat kein Stil; Rest bleibt für Flächen
    k = len(pal) - 1
    ok = w > 0
    while len(pal) < min(n, ok.sum() + k):
        d = np.min([((cv - q) ** 2).sum(1) for q in pal], axis=0) ** .5
        pal.append(cv[np.where(ok, d * np.log1p(w), -1).argmax()])
    return np.array(pal), k


def dither_tiles(files, toml_path, retina):
    """--pixel, zweiter Durchgang: eine Palette für alle Kacheln, dann Bayer-4×4-Dithering auf den 128er-Pixeln
    (Muster deckungsgleich über Kachelgrenzen, 128 ist durch 4 teilbar) und ohne Glättung auf 256 (@2x 512) px."""
    import numpy as np
    from PIL import Image
    sample = np.concatenate([np.asarray(Image.open(f).convert("RGB"))[::2, ::2].reshape(-1, 3) for f in files])
    pal, k = pixel_palette(sample, toml_path)
    bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]])
    shift = np.tile((bayer + .5) / 16 - .5, (32, 32))[..., None] * BAYER_SPREAD
    flat = [int(v) for v in pal.flatten()] + [0] * (768 - pal.size)
    out = []
    for f in files:
        a = np.asarray(Image.open(f).convert("RGB"), float)
        d = ((a[..., None, :] - pal) ** 2).sum(-1)
        near = d.argmin(-1)
        idx = (((a + shift)[..., None, :] - pal) ** 2).sum(-1).argmin(-1)
        text = (near >= 1) & (near <= k) & (d.min(-1) < TEXT_SNAP ** 2)  # Schrift: nächste Farbe, kein Raster
        im = Image.fromarray(np.where(text, near, idx).astype(np.uint8), "P")
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
                f.write_bytes(lowres(parent(f"{base}/{z - 1}/{x // 2}/{y // 2}.png"), x % 2, y % 2))
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
        write_page(out, cfg)
    write_previews(out.parent)
    size = sum(f.stat().st_size for f in (out / "tiles").rglob(f"*.{ext}"))
    print(f"{count} Kacheln, {size / 1e6:.1f} MB -> {out}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lat", type=float, default=52.0211, help="Standard: Bielefeld")
    p.add_argument("--lon", type=float, default=8.5347)
    p.add_argument("--radius", type=float, default=5, help="km um den Marker")
    p.add_argument("--zoom", default="10-18", help="z. B. 10-14")
    p.add_argument("--detail-from", type=int, default=17, help="ab dieser Stufe nur --detail-radius")
    p.add_argument("--detail-radius", type=float, default=1, help="km, für die Detailstufen")
    p.add_argument("--viewport", default="2560x1440", help="größte Kartengröße in px")
    p.add_argument("--area", default="detmold-regbez", help="Geofabrik-Name")
    p.add_argument("--retina", action="store_true", help="zusätzlich @2x rendern")
    p.add_argument("--format", choices=["png", "webp"], default="png",
                   help="png = Palette über pngquant (Standard, kleinste Dateien), webp = direkt vom tileserver")
    p.add_argument("--pixel", action="store_true",
                   help="8-Bit-Look: jede Kachel aus der gröberen Elternkachel, Pixel ohne Glättung verdoppelt; Schrift VT323")
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
    if a.pixel and not a.font:
        a.font = "VT323"  # 8-Bit-Schrift; Alternativen in fonts.toml: Press Start 2P, Silkscreen
    if a.reindex:
        for d in (ROOT / "out", ROOT / "site"):
            if d.exists():
                reindex(d, a.label)
        if (ROOT / "site" / "streifen.html").exists():  # site/: nur die Streifen-Ansicht, als index.html
            (ROOT / "site" / "compare.html").unlink(missing_ok=True)
            shutil.move(ROOT / "site" / "streifen.html", ROOT / "site" / "index.html")
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
