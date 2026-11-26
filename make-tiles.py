#!/usr/bin/env python3
"""Statische Leaflet-Kacheln für einen kleinen Bereich rendern.

Beispiel:
  ./make-tiles.py                               # styles/clear.toml, Bielefeld -> out/clear
  ./make-tiles.py --lat 52.115 --lon 8.67 --style styles/north.toml --out out/kunde-xy
  ./make-tiles.py --all --zoom 16-16 --radius 1.5 --retina   # jeder Stil × jede Schrift zum Vergleichen
"""
import argparse, fnmatch, functools, gzip, hashlib, os, re, io, sqlite3, struct, tempfile, json, math, shutil, subprocess, sys, time, tomllib, urllib.parse, urllib.request, zipfile
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


def build_style(toml_path, font=None, center=None, pixel=False, streets=False, figs_at=None):
    """styles/<name>.toml + style/base.json (OSM Bright) -> fertiger Stil, Titel, Namensnennung.
    center (lat, lon): Mittelpunkt für das Koordinatengitter (graticule = true im Stil).
    figs_at (mbtiles, (süd, west, nord, ost)): Daten und Ausschnitt für die Figuren (figures im Stil).
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
        for glob, classes in t.get("hide_class", {}).items():  # einzelne Klassen (z. B. POIs) statt ganzer Ebenen
            if fnmatch.fnmatch(l["id"], glob) and "filter" in l:
                l["filter"] = ["all", l["filter"], ["!", ["in", ["get", "class"], ["literal", classes]]]]
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
    fspec = t.get("figures")
    figs = fspec and {"names": fspec["names"], "ink": fspec.get("ink", accent),
                      "sticker": fspec.get("sticker", t.get("marker", {}).get("bg", "#ffffff")),
                      "size": fspec.get("size", FIG), "line": fspec.get("line", 2), "rim": fspec.get("rim", 7),
                      "poses": fspec.get("poses")}
    weight = {"mono": "bold", "pixel": "bold", "serif": "light"}.get(fcfg.get("group"), "regular")
    s["sprite"] = poi_sprite(weight, p["background"]["background-color"], accent, p["poi_*"]["text-color"],
                             t.get("mode") == "dark", t.get("patterns"), figs)
    if "water_lines" in t:
        water_lines(s, **t["water_lines"])
    for lid, spec in t.get("outlines", {}).items():
        outline(s, lid, **spec)
    for spec in t.get("layers", []):
        add_layer(s, dict(spec))
    if fspec and figs_at:
        figures(s, figs_at[1], figs_at[0], fspec["names"], fspec.get("places"), fspec.get("density", 0.45),
                fspec.get("density_rich", 0.85), fspec.get("areas", ()), fspec.get("poses"))
    if t.get("old_railways") and center:
        old_railways(s, center)
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


OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter"]


def overpass(q, timeout=120):
    """Elemente einer Overpass-Abfrage, None wenn kein Server antwortet."""
    for url in OVERPASS:  # ponytail: Hauptserver antwortet öfter mit 502, dann der Spiegel
        try:
            req = urllib.request.Request(url, urllib.parse.urlencode({"data": q}).encode(),
                                         headers={"User-Agent": "make-tiles/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)["elements"]
        except OSError as e:
            print(f"Overpass {url}: {e}", flush=True)
    return None


def old_railways(s, center):
    """Stillgelegte und abgebaute Bahnstrecken (old_railways = true im Stil), die OpenMapTiles nicht enthält: einmal per
    Overpass um den Mittelpunkt (±0,15° Breite, ±0,25° Länge) geholt, in data/ zwischengespeichert, als GeoJSON-Quelle
    mit denselben Farben und Breiten wie die Ebenen railway und railway-hatching gezeichnet (also wie in Betrieb)."""
    f = DATA / f"old-railways-{center[0]:.3f}-{center[1]:.3f}.geojson"
    if not f.exists():
        b = f"{center[0] - .15},{center[1] - .25},{center[0] + .15},{center[1] + .25}"
        ways = overpass(f'[out:json][timeout:90];(way["railway"~"^(abandoned|disused|razed)$"]({b});'
                        f'way["abandoned:railway"]({b});way["disused:railway"]({b});way["razed:railway"]({b}););out tags geom;')
        if ways is None:
            print("old_railways: Overpass nicht erreichbar, ohne alte Bahnstrecken", flush=True)
            return
        DATA.mkdir(exist_ok=True)
        f.write_text(json.dumps({"type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": {},
             "geometry": {"type": "LineString", "coordinates": [[p["lon"], p["lat"]] for p in w["geometry"]]}}
            for w in ways if w.get("geometry")]}))
    s["sources"]["oldrail"] = {"type": "geojson", "data": json.loads(f.read_text())}
    ids = [l["id"] for l in s["layers"]]
    new = []
    for k in ("railway", "railway-hatching"):
        l = {key: v for key, v in s["layers"][ids.index(k)].items() if key not in ("source-layer", "filter")}
        new.append(dict(l, id=f"old-{k}", source="oldrail", minzoom=13))
    i = ids.index("railway-hatching") + 1
    s["layers"][i:i] = new


def outline(s, lid, color, width=1, minzoom=0):
    """Kontur als eigene Linienebene über der Flächenebene lid (outlines im Stil, z. B. Tuschelinien um Gebäude):
    fill-outline-color ist immer nur 1 px breit. Übernimmt Quelle, Filter und fill-translate der Fläche."""
    i = next(k for k, l in enumerate(s["layers"]) if l["id"] == lid)
    f = s["layers"][i]
    l = {"id": f"{lid}-outline", "type": "line", "source": f["source"], "source-layer": f["source-layer"],
         "minzoom": max(minzoom, f.get("minzoom", 0)), "layout": {"line-join": "round"},
         "paint": {"line-color": color, "line-width": width}}
    if "filter" in f:
        l["filter"] = f["filter"]
    if "fill-translate" in f.get("paint", {}):
        l["paint"]["line-translate"] = f["paint"]["fill-translate"]
    s["layers"].insert(i + 1, l)


def add_layer(s, spec):
    """[[layers]] im Stil: zusätzliche Ebene. like = Vorlage (kopiert samt Filter, Paint, Layout; ein eigener filter wird
    mit dem der Vorlage verknüpft); mit source-layer statt dessen nur die Quelle, filter dann allein. Eingefügt hinter
    after (Standard: like). Die Globs aus [paint]/[layout] gelten hier nicht, die Ebene bringt ihre Werte selbst mit."""
    ids = [l["id"] for l in s["layers"]]
    base = s["layers"][ids.index(spec.pop("like", spec.get("after")))]
    after = spec.pop("after", base["id"])
    if "source-layer" in spec:
        l = {"type": base["type"], "source": base["source"]}
    else:
        l = json.loads(json.dumps(base))
        if "filter" in spec and "filter" in l:
            spec["filter"] = ["all", l["filter"], spec["filter"]]
    for kind in ("paint", "layout"):
        l[kind] = {**l.get(kind, {}), **spec.pop(kind, {})}
    l.update(spec)
    s["layers"].insert(ids.index(after) + 1, l)


def water_lines(s, color, count=3, gap=2, width=0.6, minzoom=13):
    """Wasserlinien wie auf gestochenen Karten (water_lines im Stil): count feine Linien innen am Ufer entlang, je gap px
    weiter und schwächer. Positiver line-offset liegt bei Vektorkacheln innen (Außenringe im Uhrzeigersinn).
    count × gap unter dem Kachelpuffer (8 px) halten, sonst zeigen sich Linien an den Schnittkanten der Kacheln."""
    i = next(k for k, l in enumerate(s["layers"]) if l["id"] == "water")
    w = s["layers"][i]
    s["layers"][i + 1:i + 1] = [
        {"id": f"water-line-{n}", "type": "line", "source": w["source"], "source-layer": w["source-layer"],
         "filter": w["filter"], "minzoom": minzoom,
         "paint": {"line-color": color, "line-width": width, "line-offset": n * gap,
                   "line-opacity": round(0.8 * (1 - (n - 1) / count), 2)}}
        for n in range(1, count + 1)]


STROKE = {"light": 12, "regular": 16, "bold": 24}  # Phosphor-Strichstärken im 256er-Raster


FIG = 48     # Figuren im Sprite: FIG × FIG px (je pixelRatio; figures.size im Stil), Zeichnungen vendor/figures/<figur>/<pose>.svg, viewBox 64×64
FIG_CELL = (0.004, 0.006)  # Raster für Figuren in Grad (Breite, Länge), ~450 × 410 m bei 52° N


def fig_poses(name, only=None):
    """Posen einer Figur, mit only (figures.poses im Stil) nur diese, z. B. ["schlaeft"]; als Tabelle je Figur, "*" für
    alle übrigen (Nordlicht: Tiere schlafen, Trolle sind wach)."""
    if isinstance(only, dict):
        only = only.get(name, only.get("*"))
    return sorted(f for f in (ROOT / "vendor" / "figures" / name).glob("*.svg") if not only or f.stem in only)


# --- Figuren: Ortswahl aus den eigenen mbtiles (z14, OpenMapTiles) ---------------------------------------------------
# Früher per Overpass; das ist für größere Gebiete zu langsam (Rate-Limit). Die mbtiles haben alles und sind genau die
# Daten der Karte. Minimaler Vector-Tile-Leser (Protobuf von Hand), keine Abhängigkeit.

def _varint(b, i):
    r = s = 0
    while True:
        x = b[i]
        i += 1
        r |= (x & 0x7f) << s
        s += 7
        if x < 128:
            return r, i


def _fields(b):
    """Protobuf-Felder (Nummer, Wert): Varint als int, Längenfeld als bytes, fest 32/64 Bit als bytes."""
    i = 0
    while i < len(b):
        k, i = _varint(b, i)
        t = k & 7
        if t == 0:
            v, i = _varint(b, i)
        elif t == 2:
            n, i = _varint(b, i)
            v, i = b[i:i + n], i + n
        else:
            n = 8 if t == 1 else 4
            v, i = b[i:i + n], i + n
        yield k >> 3, v


def _packed(b):
    out, i = [], 0
    while i < len(b):
        v, i = _varint(b, i)
        out.append(v)
    return out


def _mvt_value(b):
    for f, v in _fields(b):
        if f == 1:
            return v.decode()
        if f in (2, 3):
            return struct.unpack("<f" if f == 2 else "<d", v)[0]
        if f == 6:
            return (v >> 1) ^ -(v & 1)
        return v


def _mvt_geom(cmds):
    """Geometriebefehle -> Liste von Punktfolgen (Kacheleinheiten); Ringe geschlossen."""
    x = y = i = 0
    parts = []
    while i < len(cmds):
        c, n = cmds[i] & 7, cmds[i] >> 3
        i += 1
        if c == 7:
            parts[-1].append(parts[-1][0])
            continue
        for _ in range(n):
            dx, dy = cmds[i], cmds[i + 1]
            i += 2
            x, y = x + ((dx >> 1) ^ -(dx & 1)), y + ((dy >> 1) ^ -(dy & 1))
            if c == 1:
                parts.append([(x, y)])
            else:
                parts[-1].append((x, y))
    return parts


def mvt(data, want):
    """Vector Tile -> {Ebene: [(Eigenschaften, Geometrie)]}, nur Ebenen aus want."""
    out = {}
    for f, lay in _fields(data):
        if f != 3:
            continue
        fs = list(_fields(lay))
        name = next(v.decode() for k, v in fs if k == 1)
        if name not in want:
            continue
        keys = [v.decode() for k, v in fs if k == 3]
        vals = [_mvt_value(v) for k, v in fs if k == 4]
        feats = []
        for k, v in fs:
            if k == 2:
                tags, geom = [], []
                for fk, fv in _fields(v):
                    if fk == 2:
                        tags = _packed(fv)
                    elif fk == 4:
                        geom = _mvt_geom(_packed(fv))
                feats.append(({keys[tags[n]]: vals[tags[n + 1]] for n in range(0, len(tags), 2)}, geom))
        out[name] = feats
    return out


FIG_Z, FIG_EXT = 14, 4096   # Zoomstufe und Kachelraster der Daten
FIG_GREEN = {"wood", "forest", "park", "garden", "meadow", "grassland", "village_green", "recreation_ground", "heath",
             "scrub", "playground", "cemetery"}   # ohne grass: in OSM meist Straßenbegleitgrün
FIG_LANDMARK = {"attraction", "viewpoint", "museum", "art_gallery", "artwork", "town_hall", "castle", "ruins",
                "place_of_worship", "theatre", "zoo", "stadium"}   # POIs ohne passende Figur, neben denen eine stehen darf
# Mindestabstand des Fußpunkts zur Straßenmitte in m (die Figur ist bei z16 etwa 50 m hoch, ganz frei geht in der Stadt nicht)
FIG_ROAD = {"motorway": 25, "trunk": 25, "primary": 22, "secondary": 18, "tertiary": 18, "minor": 12, "service": 9,
            "busway": 12, "raceway": 12, "rail": 12}
FIG_BESIDE = 35   # m neben einem POI, das Symbol bleibt frei


def fig_xy(lon, lat):
    """Weltkoordinaten in z14-Kacheln (Bruchzahlen)."""
    n = 2 ** FIG_Z
    return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n


def fig_lonlat(x, y):
    n = 2 ** FIG_Z
    return x / n * 360 - 180, math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))


@functools.lru_cache(maxsize=None)
def fig_tile(mb, x, y):
    """z14-Kachel -> (Flächen nach Streifen, Kontexte je Fläche, Straßen nach Gitter, POIs). Kacheleinheiten."""
    with sqlite3.connect(f"file:{mb}?mode=ro", uri=True) as con:
        r = con.execute("select tile_data from tiles where zoom_level=? and tile_column=? and tile_row=?",
                        (FIG_Z, x, 2 ** FIG_Z - 1 - y)).fetchone()
    m = mvt(gzip.decompress(r[0]), {"landcover", "landuse", "water", "transportation", "poi"}) if r else {}
    bands, ctxs, roads, pois = {}, [], {}, []
    areas = [({p.get("class"), p.get("subclass")} - {None}, g) for p, g in m.get("landcover", []) + m.get("landuse", [])]
    for ctx, g in areas + [({"water"}, g) for _, g in m.get("water", [])]:
        ctxs.append(ctx)
        for ring in g:   # Kanten nach 64er-Streifen, Punkt-in-Fläche zählt Kreuzungen gerade/ungerade
            for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
                for b in range(min(y1, y2) // 64, max(y1, y2) // 64 + 1):
                    bands.setdefault(b, []).append((len(ctxs) - 1, x1, y1, x2, y2))
    for p, g in m.get("transportation", []):
        d = FIG_ROAD.get(p.get("class"))
        if d and p.get("brunnel") != "tunnel":
            for line in g:   # Segmente nach 256er-Gitter (> größter Abstand in Einheiten)
                for (x1, y1), (x2, y2) in zip(line, line[1:]):
                    for gx in range(min(x1, x2) // 256, max(x1, x2) // 256 + 1):
                        for gy in range(min(y1, y2) // 256, max(y1, y2) // 256 + 1):
                            roads.setdefault((gx, gy), []).append((d, x1, y1, x2, y2))
    for p, g in m.get("poi", []):
        if g and 0 <= g[0][0][0] < FIG_EXT and 0 <= g[0][0][1] < FIG_EXT:   # Puffer gehört der Nachbarkachel
            pois.append(({p.get("class"), p.get("subclass")} - {None}, (x + g[0][0][0] / FIG_EXT, y + g[0][0][1] / FIG_EXT)))
    return bands, ctxs, roads, pois


def fig_at(mb, lon, lat):
    """(Flächen-Kontexte, frei von Straßen?) am Ort: Klassen/Unterklassen aus landcover/landuse, "water"."""
    X, Y = fig_xy(lon, lat)
    bands, ctxs, roads, _ = fig_tile(mb, int(X), int(Y))
    px, py = (X - int(X)) * FIG_EXT, (Y - int(Y)) * FIG_EXT
    odd = set()
    for pid, x1, y1, x2, y2 in bands.get(int(py // 64), ()):
        if (y1 > py) != (y2 > py) and px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
            odd ^= {pid}
    unit = 40075016.7 * math.cos(math.radians(lat)) / 2 ** FIG_Z / FIG_EXT   # m je Kacheleinheit
    gx, gy = int(px // 256), int(py // 256)
    for d, x1, y1, x2, y2 in (s for a in (-1, 0, 1) for b in (-1, 0, 1) for s in roads.get((gx + a, gy + b), ())):
        vx, vy = x2 - x1, y2 - y1
        t = max(0, min(1, ((px - x1) * vx + (py - y1) * vy) / (vx * vx + vy * vy or 1)))
        if math.hypot(px - x1 - t * vx, py - y1 - t * vy) * unit < d:
            return set().union(*(ctxs[p] for p in odd)), False
    return set().union(*(ctxs[p] for p in odd)), True


def fig_pois(mb, box):
    """POIs in box (süd, west, nord, ost): [(Kontexte, lon, lat)], sortiert."""
    south, west, north, east = box
    (x0, y1), (x1, y0) = fig_xy(west, south), fig_xy(east, north)
    out = []
    for x in range(int(x0), int(x1) + 1):
        for y in range(int(y0), int(y1) + 1):
            for ctx, (X, Y) in fig_tile(mb, x, y)[3]:
                lon, lat = fig_lonlat(X, Y)
                if south <= lat < north and west <= lon < east:
                    out.append((sorted(ctx), round(lon, 6), round(lat, 6)))
    return sorted(out)


def fig_beside(mb, lon, lat, b):
    """Platz FIG_BESIDE m neben einem POI: erste von 8 Richtungen (ab Hash-Richtung b), frei von Straßen und Wasser."""
    spots = []
    for k in range(8):
        a = (b + k) % 8 * math.pi / 4
        spots.append((lon + FIG_BESIDE * math.cos(a) / (111320 * math.cos(math.radians(lat))),
                      lat + FIG_BESIDE * math.sin(a) / 111320))
    for s in spots:
        ctx, free = fig_at(mb, *s)
        if free and "water" not in ctx:
            return s
    return spots[0]


FIG_SPLIT = 6   # ab so vielen passenden POIs/Wahrzeichen wird die Zelle in 2×2 geteilt (Innenstadt)


def fig_cell(mb, key, box, names, fit, density, density_rich, areas=frozenset(), only=None):
    """Figur für eine Zelle oder None, siehe figures(). key: Hash-Schlüssel, box: (süd, west, nord, ost)."""
    south, west, north, east = box
    h = hashlib.sha256(key.encode()).digest()
    pick = lambda xs, k: xs[h[k] % len(xs)]
    cand = [(west + (0.1 + 0.8 * h[6 + 2 * k] / 256) * (east - west), south + (0.1 + 0.8 * h[7 + 2 * k] / 256) * (north - south))
            for k in range(12)]
    info = [(c, *fig_at(mb, *c)) for c in cand]
    pois = fig_pois(mb, box)
    theme = [p for p in pois if fit(p[0])]
    marks = [p for p in pois if FIG_LANDMARK & set(p[0])]
    wet = set(fit({"water"}))   # Wasserwesen (places mit "water"): nur im Wasser, sonst nirgends
    land = [n for n in names if n not in wet]
    green = [x for x in info if (FIG_GREEN | areas) & x[1] and ("water" not in x[1] or "water" in areas)]
    if h[0] / 256 >= (density_rich if theme or marks or green else density):
        return None
    pool = []
    if theme and (not green or h[1] < 154) or marks and not green:   # Thema gewinnt zu 60 % vor Grün
        ctx, plon, plat = pick(theme or marks, 30)
        spot, pool = fig_beside(mb, plon, plat, h[31]), [n for n in fit(ctx) if n not in wet]
    elif green:
        spot, ctx, _ = next((x for x in green if x[2]), green[0])
        pool = [n for n in fit(ctx) if n in wet] if "water" in ctx else fit(ctx) if h[2] < 171 else []
    else:
        dry = [x for x in info if "water" not in x[1]] or info
        spot = next((x for x in dry if x[2]), dry[0])[0]
    n = pick(pool or land, 3)
    poses = fig_poses(n, only)
    img = f"fig-{n}-{poses[h[4] % len(poses)].stem}{'-m' if h[5] & 1 else ''}"
    return {"type": "Feature", "properties": {"f": img},
            "geometry": {"type": "Point", "coordinates": [round(spot[0], 6), round(spot[1], 6)]}}


def figures(s, bounds, mb, names, places=None, density=0.45, density_rich=0.85, areas=(), poses=None):
    """Kleine Figuren an festen Orten (figures im Stil). Stabil: ein weltweit verankertes Raster aus FIG_CELL-Zellen
    (~450 m); alles hängt nur vom SHA-256 der Zellnummer und den mbtiles ab, nicht von Mittelpunkt, Radius oder Stil.
    Zellen mit mindestens FIG_SPLIT passenden POIs/Wahrzeichen (Innenstadt) werden in 2×2 Unterzellen geteilt.
    Je (Unter-)Zelle, in dieser Reihenfolge:
      1. POI mit passender Figur (places: Figur = [OMT-Klassen/Unterklassen]) -> diese Figur daneben (Samurai an der
         Burg); liegt auch Grün in der Zelle, nur zu 60 %, sonst gewinnen häufige POIs (Spielplatz, Sportplatz) überall
      2. Grünfläche/Wald (FIG_GREEN, dazu areas aus dem Stil, z. B. water, farmland) unter 12 Kandidatenorten -> dort,
         Figur zu 2/3 passend zur Fläche (Kitsune im Wald); im Wasser immer ein Wasserwesen (places mit "water"),
         die sonst nirgends stehen
      3. sonstiges Wahrzeichen (FIG_LANDMARK) -> daneben, beliebige Figur
      4. sonst ein Kandidat nicht im Wasser
    Kandidaten mit FIG_ROAD-Abstand zur Straße werden vorgezogen. Zellen mit POI oder Grün bekommen mit density_rich
    eine Figur, die übrigen mit density.
    Unter allen Beschriftungen und ohne Kollision (allow-overlap), sonst würden Kacheln an ihren Rändern je nach
    eigener Beschriftung unterschiedlich entscheiden und Figuren halbieren."""
    by_ctx = {}
    for n in names:
        for c in (places or {}).get(n, []):
            by_ctx.setdefault(c, []).append(n)
    fit = lambda ctx: sorted({n for c in ctx for n in by_ctx.get(c, [])})
    dy, dx = FIG_CELL
    south, west, north, east = bounds
    feats = []
    for i in range(math.floor(south / dy), math.floor(north / dy) + 1):
        for j in range(math.floor(west / dx), math.floor(east / dx) + 1):
            box = (i * dy, j * dx, (i + 1) * dy, (j + 1) * dx)
            busy = sum(1 for p in fig_pois(mb, box) if fit(p[0]) or FIG_LANDMARK & set(p[0])) >= FIG_SPLIT
            subs = [(f"fig {i} {j} {k}", (box[0] + k // 2 * dy / 2, box[1] + k % 2 * dx / 2,
                                           box[0] + (k // 2 + 1) * dy / 2, box[1] + (k % 2 + 1) * dx / 2))
                    for k in range(4)] if busy else [(f"fig {i} {j}", box)]
            for key, b in subs:
                f = fig_cell(mb, key, b, names, fit, density, density_rich, frozenset(areas), poses)
                if f:
                    feats.append(f)
    s["sources"]["figures"] = {"type": "geojson", "data": {"type": "FeatureCollection", "features": feats}}
    first_symbol = next(k for k, l in enumerate(s["layers"]) if l["type"] == "symbol")
    s["layers"].insert(first_symbol, {   # Stilzoom = Leaflet-Zoom - 1 (512er-Kacheln): ab Leaflet z15
        "id": "figures", "type": "symbol", "source": "figures", "minzoom": 14,
        "layout": {"icon-image": ["get", "f"], "icon-anchor": "bottom", "icon-allow-overlap": True,
                   "icon-ignore-placement": True,
                   "icon-size": ["interpolate", ["linear"], ["zoom"], 14, 0.55, 16, 0.85, 17, 1]}})


def poi_sprite(weight, bg, accent, glyph, dark, patterns=None, figs=None):
    """Sprite wie style/ofm(@2x), aber die POI-Bilder aus style/icons.toml neu: Phosphor-Symbol in der POI-Farbe
    auf einem Kreis in dezentem Akzent (dunkel 22 %, hell 16 % Akzent über dem Grund), Ring 45 %.
    Liegt in style/sprites/ (gitignored, im Container unter /data); je Kombination nur einmal erzeugt.
    patterns ([patterns] im Stil): name = { symbol, color, bg[, fill] } -> 32×32-Musterbild für fill-pattern, Symbol aus
    vendor/patterns/<symbol>.svg in color auf bg (fill-pattern ersetzt die Füllfarbe), unten an das Sprite angehängt.
    figs (figures im Stil): {names, ink, sticker} -> Bilder fig-<figur>-<pose>[-m] aus vendor/figures/<figur>/<pose>.svg
    (-m gespiegelt), mit Tuschekontur ink und breitem Sticker-Rand sticker (Lesbarkeit auf jedem Grund), in Zeilen
    unter den Mustern. size/line/rim: Bildgröße, Kontur- und Randbreite (im 64er-Raster). currentColor in den Zeichnungen = ink (Schraffur, Konturen mit eigener Breite)."""
    hexrgb = lambda h: [int(h[i:i + 2], 16) for i in (1, 3, 5)]
    mix = lambda t: "#%02x%02x%02x" % tuple(round(b + (a - b) * t) for b, a in zip(hexrgb(bg), hexrgb(accent)))
    disc, ring = mix(0.22 if dark else 0.16), mix(0.45)
    name = f"sprites/{weight}-{bg[1:]}-{accent[1:]}-{glyph[1:]}"
    if patterns or figs:  # Figuren und Muster mit Dateiinhalt im Hash, sonst bliebe nach dem Nachzeichnen das alte Sprite
        drawn = [f.read_text() for n in (figs or {}).get("names", []) for f in fig_poses(n, (figs or {}).get("poses"))]
        drawn += [(ROOT / "vendor" / "patterns" / f"{s['symbol']}.svg").read_text() for s in (patterns or {}).values()]
        name += "-" + hashlib.sha1(json.dumps([patterns, figs, drawn], sort_keys=True).encode()).hexdigest()[:8]
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
        svg, pr = [], 2 if sfx else 1
        ph = 32 * pr if patterns else 0  # Musterzeile unter dem Sprite
        px += bytes(w * ph * 4)
        for k, (pn, spec) in enumerate(sorted((patterns or {}).items())):
            x, d = k * 32 * pr, 32 * pr
            body = re.sub(r"<!--.*?-->|^\s*<svg[^>]*>|</svg>\s*$", "",
                          (ROOT / "vendor" / "patterns" / f"{spec['symbol']}.svg").read_text().strip(), flags=re.S | re.M)
            svg.append(f'<rect x="{x}" y="{h}" width="{d}" height="{d}" fill="{spec["bg"]}"/>'
                       f'<g transform="translate({x},{h}) scale({pr})" color="{spec["color"]}">'
                       f'{body.replace("FILL", spec.get("fill", "none"))}</g>')
            idx[pn] = {"x": x, "y": h, "width": d, "height": d, "pixelRatio": pr}
        h += ph
        if figs:  # Figurenzeilen, jede Pose normal und gespiegelt; Zeichnung zweimal: breiter Sticker-Rand, darüber Tusche
            fh = figs["size"] * pr
            per = w // fh
            imgs = [(f"fig-{n}-{f.stem}{m}", f, m) for n in figs["names"] for f in fig_poses(n, figs.get("poses")) for m in ("", "-m")]
            rows = -(-len(imgs) // per)
            px += bytes(w * fh * rows * 4)
            for k, (key, f, m) in enumerate(imgs):
                x, y = k % per * fh, h + k // per * fh
                body = re.sub(r"<!--.*?-->|^\s*<svg[^>]*>|</svg>\s*$", "", f.read_text().strip(), flags=re.S | re.M)
                flip = " translate(64,0) scale(-1,1)" if m else ""
                svg.append(f'<g transform="translate({x},{y}) scale({fh / 68}) translate(2,2){flip}" stroke-linejoin="round" '
                           f'stroke-linecap="round"><g stroke="{figs["sticker"]}" color="{figs["sticker"]}" stroke-width="{figs["rim"]}">{body}</g>'
                           f'<g stroke="{figs["ink"]}" color="{figs["ink"]}" stroke-width="{figs["line"]}">{body}</g></g>')
                idx[key] = {"x": x, "y": y, "width": fh, "height": fh, "pixelRatio": pr}
            h += fh * rows
        for key, r in idx.items():
            icon = icons.get(key.removesuffix("_11"))
            if not icon or key in (patterns or {}):
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
        out.with_suffix(".json").write_text(json.dumps(idx))
    return name


def write_page(out, cfg):
    """index.html einer Variante aus template.html und ihrer Konfiguration."""
    page = (ROOT / "template.html").read_text().replace("<title>Karte</title>", f"<title>{cfg['title']}</title>")
    (out / "index.html").write_text(page.replace("/*CONFIG*/{}", json.dumps(cfg, ensure_ascii=False)))


def tile_lab(d, n=25):
    """Mittlere OKLab-Farbe der Kacheln einer Variante (n Kacheln aus der Mitte der höchsten Zoomstufe)."""
    import numpy as np
    from PIL import Image
    z = max((p for p in (d / "tiles").iterdir() if p.name.isdigit()), key=lambda p: int(p.name))
    files = sorted(f for f in z.rglob("*.*") if "@" not in f.name and ".labels." not in f.name)
    k = max(0, len(files) // 2 - n // 2)
    px = np.concatenate([np.asarray(Image.open(f).convert("RGB").reduce(4)).reshape(-1, 3) for f in files[k:k + n]]) / 255
    c = np.where(px <= 0.04045, px / 12.92, ((px + 0.055) / 1.055) ** 2.4)
    lms = np.cbrt(c @ np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
                                [0.0883024619, 0.2817188376, 0.6299787005]]).T)
    return (lms @ np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
                            [0.0259040371, 0.7827717662, -0.8086757660]]).T).mean(0)


def colour_order(outdir, configs):
    """Streifen-Reihenfolge mit sanftem Farbübergang (Nutzerwunsch 2026-11-25): je Gruppe eine Kette der Familien, in der
    Nachbarn farblich möglichst nah sind, gemessen an Hell- und Dunkel-Variante zusammen, damit der Moduswechsel die
    Reihenfolge nicht ändert. Nur Familien mit order 50 (Standard) werden sortiert; ein eigenes order (Cyberpunk 99 …)
    bleibt fest rechts. Schreibt order = 50 + Rang/100 in die Konfiguration, streifen.html sortiert wie bisher danach."""
    try:
        import numpy as np
    except ImportError:
        return
    lab = {}
    for n, c in configs.items():   # je (Gruppe, Familie, Modus) die erste normale Variante
        key = (c.get("category"), c.get("family"), c.get("mode"))
        if key not in lab and not c.get("pixel") and not c.get("streets") and (outdir / n / "tiles").exists():
            lab[key] = tile_lab(outdir / n)
    for cat in {k[0] for k in lab}:
        fams = {f for c, f, _ in lab if c == cat}
        vec = {f: np.concatenate([lab.get((cat, f, m), lab.get((cat, f, "dark" if m == "light" else "light")))
                                  for m in ("light", "dark")]) for f in fams}
        order = {f: min(c.get("order", 50) for c in configs.values() if c.get("family") == f) for f in fams}
        free = [f for f in sorted(fams) if order[f] == 50]
        pinned = sorted((f for f in fams if order[f] != 50), key=lambda f: (order[f], f))
        d = lambda a, b: float(np.linalg.norm(vec[a] - vec[b]))
        best, cost = free, math.inf
        for start in free:   # gierige Kette von jedem Start aus, die kürzeste gewinnt (bis zum ersten festen Streifen)
            path, rest = [start], set(free) - {start}
            while rest:
                path.append(min(sorted(rest), key=lambda r: d(path[-1], r)))
                rest.remove(path[-1])
            c = sum(d(a, b) for a, b in zip(path, path[1:] + pinned[:1]))
            if c < cost:
                best, cost = path, c
        for c in configs.values():
            if c.get("category") == cat and c.get("family") in best:
                c["order"] = 50 + best.index(c["family"]) / 100


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
    for c in configs.values():  # Marker in der Schrift des Stils (oder [marker] font)
        c["font_url"] = marker_font(c.get("marker", {}).get("font") or c.get("font", ""), outdir)
    colour_order(outdir, configs)
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
            write_page(d, dict(cfg, font_url=marker_font(cfg["marker"].get("font") or cfg.get("font", ""), d)))
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


def regenerate(root):
    """--regenerate (Nutzerwunsch 2026-11-26): gerenderte Stile in root (site/ oder out/) nummeriert auflisten, Nummern
    einlesen und deren Ordner (alle Schriften/8-Bit-Varianten des Stils) löschen; der folgende Lauf baut sie neu."""
    by = {}
    for c in sorted(root.glob("*/config.json")):
        by.setdefault(json.loads(c.read_text()).get("style", c.parent.name), []).append(c.parent)
    names = sorted(by)
    if not names:
        sys.exit(f"keine gerenderten Stile in {root}")
    for i, n in enumerate(names, 1):
        print(f"{i:3}  {n:24} {', '.join(d.name for d in by[n])}")
    try:
        nums = [int(x) for x in input("Neu erstellen (Nummern, mit Komma oder Leerzeichen getrennt): ").replace(",", " ").split()]
    except (ValueError, EOFError):
        sys.exit("ungültige Eingabe, nur ganze Zahlen")
    if bad := [n for n in nums if not 1 <= n <= len(names)]:
        sys.exit(f"keine solche Nummer: {', '.join(map(str, bad))}")
    for n in dict.fromkeys(nums):
        for d in by[names[n - 1]]:
            shutil.rmtree(d)
        print(f"gelöscht: {names[n - 1]}")


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
    wanted, jobs = set(), []
    for st in sorted((ROOT / "styles").glob("*.toml")):
        meta = tomllib.loads(st.read_text())
        cat = meta.get("category", "standard")
        if meta.get("family") in cfg.get("exclude", []):  # nur README, nicht auf der öffentlichen Vorschau
            continue
        # Schriften der Gruppe, dazu für Gruppen/Familien in pixel = [...] eine 8-Bit-Variante (Schalter "8 Bit") und für
        # Gruppen in streets = [...] eine Nur-Straßen-Variante (Schalter "Straßen") in der ersten Schrift
        site_fonts = [meta["site_font"]] if "site_font" in meta else cfg["fonts"][cat]  # z. B. Phosphor: VT323
        variants = [(f, False, False) for f in site_fonts]
        variants += [("Silkscreen", 4, False)] if {cat, meta.get("family")} & set(cfg.get("pixel", [])) else []
        variants += [(site_fonts[0], False, True)] if cat in cfg.get("streets", []) else []
        for font, s.pixel, s.streets_only in variants:
            suffix = "-8bit" if s.pixel else "-streets" if s.streets_only else ""
            out = site / f"{st.stem}-{font.lower().replace(' ', '-')}{suffix}"
            wanted.add(out)
            done = out / "config.json"
            keep = a.missing and done.exists()
            old = json.loads(done.read_text()) if keep else {}
            z0, z1 = map(int, s.zoom.split("-"))  # neue Zoomstufe/@2x: fehlende Kacheln ergänzen
            if keep and (old.get("retina"), old.get("zmin"), old.get("zmax")) == (s.retina, z0, z1):
                continue
            jobs.append((st, out, font, s.pixel, s.streets_only, keep))
    t0 = time.time()
    for i, (st, out, font, s.pixel, s.streets_only, keep) in enumerate(jobs):
        render(s, st, out, mb, font, standalone=False, keep=keep)  # keep: nur fehlende Kacheln (z. B. @2x)
        eta = t0 + (time.time() - t0) / (i + 1) * len(jobs)  # ponytail: Mittel über alle Stile, Aquarell/Siebdruck dauern länger
        print(f"== {i + 1} von {len(jobs)} Stilen fertig, ETA {time.strftime('%H:%M', time.localtime(eta))}", flush=True)
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
    """PNGs verlustfrei nachkomprimieren (oxipng, falls installiert), nach dem Stoppen des Containers.
    Gemessen (8 Kerne, 652 Kacheln): -o 1 spart 5,6 % in 5 s, -o 2 7,2 % in 11–13 s; oxipng belegt ~6,5 Kerne,
    parallel zum nächsten Stil gewinnt man daher nichts. 32 Farben + oxipng so groß wie 24 Farben ohne, aber genauer."""
    files = [str(f) for f in files]
    if OXIPNG and files:
        subprocess.run([OXIPNG, "-q", "-o", "1", "--strip", "safe", *files], check=True)


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


def vnoise(u, v, seed):
    """Wertrauschen 0..1 an Weltkoordinaten (u, v in Zellen): Gitterwerte per Integer-Hash, weich interpoliert;
    gleiche Koordinate = gleicher Wert, daher nahtlos über Kachelgrenzen (stain_png, watercolor)."""
    import numpy as np
    i, j = np.floor(u).astype(np.int64), np.floor(v).astype(np.int64)
    fu, fv = u - i, v - j
    fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
    def h(a, b):
        n = (a * 73856093 ^ b * 19349663 ^ seed * 83492791) & 0xFFFFFFFF
        n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
        return (n ^ (n >> 16)) / 0xFFFFFFFF
    top = h(i, j) * (1 - fu) + h(i + 1, j) * fu
    bot = h(i, j + 1) * (1 - fu) + h(i + 1, j + 1) * fu
    return top * (1 - fv) + bot * fv


def stain_png(data, x, y, cfg):
    """Altersflecken in die Kachel einbacken (stains im Stil, Versuch): Wertrauschen in globalen Pixelkoordinaten der
    Zoomstufe, daher nahtlos über Kachelgrenzen; je Zoomstufe gleich groß auf dem Bildschirm (andere Stufe = anderes
    Blatt). Fleckenfarbe multipliziert (blend = "patina": Grünspan-Kruste), Stärke cfg["strength"]; danach wie immer pngquant."""
    import numpy as np
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    size = im.size[0]
    yy, xx = np.mgrid[0:size, 0:size] * (256 / size)
    gx, gy = x * 256 + xx, y * 256 + yy

    noise = vnoise
    def fbm(u, v):  # Fleckenfeld 0..1; Fleckengröße in px (× scale), feinere Oktaven fransen die Ränder aus
        n, tot, amp = 0, 0, 1
        for cell in (640, 320, 160, 80, 40):
            cell *= cfg.get("scale", 1)
            n, tot, amp = n + amp * noise(u / cell, v / cell, round(cell)), tot + amp, amp * .5
        return n / tot
    n, tot = fbm(gx, gy), 1
    a = np.clip((n / tot - cfg.get("threshold", .55)) * cfg.get("edge", 4), 0, 1)[..., None] * cfg.get("strength", .35)  # edge: Randschärfe
    col = np.array([int(cfg.get("color", "#8c642d")[i:i + 2], 16) for i in (1, 3, 5)]) / 255
    if cfg.get("blend") == "patina":  # Grünspan (Kupferplatte, nach Fotos oxidierter Kupferplatten): körnige Kruste in hellem
        # Türkis bis Grün, die in den Zonen dicht ist und zum Rand in Krümel zerfällt (Lücken lassen die Linien durch),
        # ringsum ein rostiger Saum; Farben mit eigener Helligkeit, damit es auf dunklem Grund leuchtet
        px = np.asarray(im, float)
        z = n / tot - cfg.get("threshold", .55)          # > 0: Zone
        grain = sum(noise(gx / c, gy / c, round(7 + 10 * c)) * w for c, w in ((1.5, .5), (4, .3), (12, .2)))   # Korn, 0..1
        zone = np.clip(z * cfg.get("edge", 4), 0, 1)
        if cfg.get("drips"):  # Grünspan läuft in Rinnsalen nach unten (Nutzerfoto 2026-11-25): Zone von weiter oben,
            # nur in schmalen Spalten (Rauschen über x), je länger, desto dünner; drips = größte Länge in px.
            # Fleckenfeld einmal mit Rand nach oben berechnet und zeilenweise verschoben (12× fbm kostete 4 min)
            d = int(cfg["drips"] * size / 256)
            ey, ex = np.mgrid[-d:size, 0:size] * (256 / size)
            far = np.clip((fbm(x * 256 + ex, y * 256 + ey) - cfg.get("threshold", .55)) * cfg.get("edge", 4), 0, 1)
            col = noise(gx / 6, np.full_like(gx, 5.5), 41) * .65 + noise(gx / 2, np.full_like(gx, 3.5), 43) * .35
            for k in range(1, d + 1, max(1, d // 24)):
                zone = np.maximum(zone, far[d - k:d - k + size] * (col > .45 + .25 * k / d) * (1.15 - .3 * k / d))
        crust = np.clip((zone * .75 + grain - 1.05) * 6, 0, 1)[..., None] * cfg.get("strength", .35)
        hue = noise(gx / 30, gy / 30, 99)[..., None]       # Türkis ↔ Grün, fleckig
        hexc = lambda h: np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)
        green = hexc(cfg.get("color", "#40bfae")) * (1 - hue) + hexc(cfg.get("color2", "#6a9a52")) * hue
        rust = (np.clip(1 - np.abs(z + .02) * 45, 0, 1) * np.clip(grain * 2 - .6, 0, 1))[..., None] * .5   # Saum um die Zone
        px = px * (1 - rust) + hexc(cfg.get("rust", "#b0582a")) * rust
        out = np.clip(px * (1 - crust) + green * crust, 0, 255)
    elif cfg.get("blend") == "aurora":  # Nordlicht (Island-Partner, Nutzerwunsch 2026-11-25): Lichtvorhänge in Bändern alle
        # ~900 px, die sich schlängeln; unten scharfe helle Kante in color (grün), nach oben ausblassend zu color2
        # (violett), feine senkrechte Strahlen, nicht überall gleich stark; aufhellend (screen), sonst verschwindet es
        s = cfg.get("scale", 1)
        wob = ((noise(gx / (520 * s), np.full_like(gx, 3.5), 11) - .5) * 420 + (noise(gx / (150 * s), np.full_like(gx, 1.5), 13) - .5) * 120) * s
        v = (gy + wob) / (900 * s)
        band = np.floor(v)
        r = v - band                                     # 0 oben … 1 Unterkante
        ray = noise(gx / (7 * s), band * 7.3, 21) * .6 + noise(gx / (23 * s), band * 5.1, 23) * .4   # Strahlen, 0..1
        reach = 1.2 + 5 * (1 - ray)                      # helle Strahlen reichen weit nach oben, dunkle kaum
        glow = (r ** reach + .8 * r ** 14) * np.clip((1 - r) * 18, 0, 1) * (.25 + .75 * ray)   # + heller Saum unten
        env = np.clip(noise((gx + band * 977) / (650 * s), band * 3.1, 31) * 1.8 - .45, 0, 1)
        a = (glow * env)[..., None] * cfg.get("strength", .35)
        hexc = lambda h: np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)
        t = (r ** 3)[..., None]
        light = hexc(cfg.get("color", "#4af0a0")) * t + hexc(cfg.get("color2", "#a070f0")) * (1 - t)
        px = np.asarray(im, float)
        out = np.clip(255 - (255 - px) * (1 - a * light / 255), 0, 255)
    else:
        out = np.asarray(im, float) * (1 - a * (1 - col))
    buf = io.BytesIO()
    Image.fromarray(out.round().astype(np.uint8)).save(buf, "PNG")
    return buf.getvalue()


def watercolor(img, ox, oy, k, cfg, z=None):
    """Wasserfarben (watercolor im Stil, Aquarell; nach dem Vorbild von Stamen Watercolor): img = RGB 0..1 der Karte
    ohne Beschriftung, ox/oy = Weltkoordinate (256er-Pixel der Zoomstufe) der linken oberen Ecke, k = Bildpixel je
    Weltpixel (@2x: 2). Alles Rauschen hängt an Weltkoordinaten, daher nahtlos, solange img rundum Rand hat (Nachbarn).
    1. Ränder ausfransen: Bild um Rauschen verschoben (warp, Weltpixel)
    2. leicht verwaschen, dann als Pigmentdichte A = -ln(Helligkeit) gerechnet (Papier ~ 0, mehr Farbe = mehr A)
    3. Pigment sammelt sich an den Rändern jeder Fläche (edge): A dort höher, beidseits, nach innen auslaufend
    4. ungleichmäßiger Auftrag (wash) in großen Wolken, Körnung (grain) im Pigment, Papierstruktur (paper)
    5. Wassertropfen (drops > 0, water_drops())"""
    import numpy as np
    from scipy import ndimage
    h, w, _ = img.shape
    yy, xx = np.mgrid[0:h, 0:w]
    gx, gy = ox + xx / k, oy + yy / k
    def fbm(s, seed):  # grobes Rauschen (Ränder, Wolken) auf jedem 4. Pixel, dann hochgerechnet: 16× weniger Arbeit
        q = lambda v: v[::4, ::4]
        n = sum(vnoise(q(gx) / (s * f), q(gy) / (s * f), seed + i) * a
                for i, (f, a) in enumerate(((1, .6), (.4, .28), (.15, .12))))
        return ndimage.zoom(n, 4, order=1)[:h, :w] if n.shape[0] * 4 >= h and n.shape[1] * 4 >= w else \
            np.pad(ndimage.zoom(n, 4, order=1), ((0, h), (0, w)), mode="edge")[:h, :w]
    amp, ws = cfg.get("warp", 3) * k, cfg.get("warp_scale", 30)
    dx, dy = (fbm(ws, 51) - .5) * 2 * amp, (fbm(ws, 61) - .5) * 2 * amp
    img = np.stack([ndimage.map_coordinates(img[..., c], [yy + dy, xx + dx], order=1, mode="nearest")
                    for c in range(3)], -1)
    img = ndimage.gaussian_filter(img, (cfg.get("soft", .7) * k, cfg.get("soft", .7) * k, 0))
    A = -np.log(np.clip(img, 1 / 255, 1))
    # Rand: Farbabstand zur weichgezeichneten Umgebung, groß an Flächenrändern, klingt über ~edge_width aus
    ew = cfg.get("edge_width", 3) * k
    e = np.clip(np.abs(img - ndimage.gaussian_filter(img, (ew, ew, 0))).sum(-1) * 6, 0, 1)
    e = ndimage.gaussian_filter(e, ew / 3)[..., None]
    wash = 1 + (fbm(cfg.get("wash_scale", 160), 71) - .5) * 2 * cfg.get("wash", .35)
    grain = (vnoise(gx / 1.3, gy / 1.3, 81) * .6 + vnoise(gx / 4, gy / 4, 82) * .4 - .5)
    A = A * (1 + cfg.get("edge", 1.2) * e) * wash[..., None] * (1 + grain[..., None] * cfg.get("grain", .5))
    A += np.clip(grain, 0, None)[..., None] * cfg.get("paper", .05)
    if cfg.get("drops"):
        A = A * water_drops(gx, gy, cfg)[..., None]
    return np.exp(-A)


def water_drops(gx, gy, cfg):
    """Wassertropfen vom Pinsel (drops im watercolor-Stil, Nutzerwunsch 2026-11-26): Faktor auf die Pigmentdichte.
    Weltfestes Zellraster (drop_cell Weltpixel), je Zelle mit Wahrscheinlichkeit drops ein Tropfen an zufälliger Stelle,
    Radius drop_size × Zelle (höchstens 1 Zelle, daher reichen die 3×3 Nachbarzellen). Rand mit Rauschen ausgefranst;
    innen Farbe ausgewaschen (drop_out, fleckig), verdrängtes Pigment als dunkler Saum am Rand (drop_ring)."""
    import numpy as np
    cell = cfg.get("drop_cell", 140)
    lo, hi = cfg.get("drop_size", [.25, .6])
    rag = (vnoise(gx / 9, gy / 9, 91) - .5) * .35 + (vnoise(gx / 3, gy / 3, 92) - .5) * .12
    ci, cj = np.floor(gx / cell), np.floor(gy / cell)
    f = np.full(gx.shape, 9.0)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            i, j = ci + di, cj + dj   # vnoise an ganzzahligen Stellen = Hash der Zelle
            on = vnoise(i, j, 93) < cfg["drops"]
            cx, cy = (i + .15 + .7 * vnoise(i, j, 94)) * cell, (j + .15 + .7 * vnoise(i, j, 95)) * cell
            r = (lo + (hi - lo) * vnoise(i, j, 96)) * cell
            f = np.where(on, np.minimum(f, np.hypot(gx - cx, gy - cy) / r), f)
    f = f + rag   # ausgefranster Rand
    inside = np.clip((1 - f) / .15, 0, 1)   # weicher Übergang nach innen
    mottle = .7 + .6 * vnoise(gx / 14, gy / 14, 97)   # nicht gleichmäßig ausgewaschen
    ring = np.exp(-((f - 1) / cfg.get("drop_rim", .05)) ** 2)
    return (1 - cfg.get("drop_out", .6) * inside * np.clip(mottle, 0, 1)) * (1 + cfg.get("drop_ring", .8) * ring)


def halftone(img, ox, oy, k, cfg, z=17):
    """Druckraster (halftone im Stil, Siebdruck; Nutzerwunsch 2026-11-26 mit CMYK-Rasterbildern): jede Farbe der Karte
    in Druckfarben zerlegt, jede Farbe als eigenes Punktraster unter ihrem Winkel (Gelb 0°, Cyan 15°, Schwarz 45°,
    Magenta 75° wie im Offsetdruck, daher Rosetten), Punktgröße nach Farbmenge, volle Fläche ab ~100 % (Straßen in
    kräftigen Farben bleiben durchgehend), Platten je um offset Weltpixel versetzt (Passer), übereinander gedruckt.
    mode = "cmyk": Tinte auf Papier (paper), multipliziert. mode = "light": drei Leuchtfarben auf schwarzem Karton,
    hellen auf (screen). inks = { c, m, y[, k] } ersetzt die Druckfarben. Raster weltfest (ox/oy wie watercolor()), nahtlos;
    Rasterweite pitch (Weltpixel bei z17), je Zoomstufe darunter pitch_step feiner. Volltöne (eine Platte > fine_from)
    im feinen Raster (fine × pitch, Farbmenge höchstens fine_amount), damit auch Straßen aus Punkten bestehen.
    soft: Punktkante als radialer Verlauf, Breite in Rasterzellen (0 = harte Kante, 1 px)."""
    import numpy as np
    from scipy import ndimage
    h, w, _ = img.shape
    yy, xx = np.mgrid[0:h, 0:w]
    gx, gy = ox + xx / k, oy + yy / k
    hexc = lambda c: np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)]) / 255
    pitch = max(2, cfg.get("pitch", 6) + cfg.get("pitch_step", 1) * ((z or 17) - 17))
    light = cfg.get("mode", "cmyk") == "light"
    paper = hexc(cfg.get("paper", "#000000" if light else "#ffffff"))
    names = ("c", "m", "y")
    inks = {**({"c": "#2ec8ff", "m": "#ff48b0", "y": "#ffe14d"} if light else
               {"c": "#00a3e0", "m": "#ff3fa4", "y": "#ffe500", "k": "#231f20"}), **cfg.get("inks", {})}
    ink = {c: hexc(v) for c, v in inks.items()}
    # Farbmengen je Platte aus den echten Druckfarben (3×3-Gleichung je Pixel): Tinte in Dichten (−ln, Papier = 0),
    # Leuchtfarbe linear über Schwarz; so wird eine Fläche in Druckfarbe nur von ihrer eigenen Platte gedruckt
    if light:
        M, rhs = np.stack([ink[c] - paper for c in names], 1), img - paper
    else:
        dens = lambda v: -np.log(np.clip(v / paper, 1e-3, 1))
        M, rhs = np.stack([dens(ink[c]) for c in names], 1), dens(img)
    amt = np.clip(rhs @ np.linalg.inv(M).T, 0, 1.2)
    plates = {c: amt[..., n] for n, c in enumerate(names)}
    if not light:  # Schwarz übernimmt den gemeinsamen Anteil (Unterfarbenentfernung)
        kk = amt.min(-1) * cfg.get("black", 1)
        plates = {c: v - kk for c, v in plates.items()} | {"k": kk}
    angle = {"y": 0, "c": 15, "k": 45, "m": 75, **cfg.get("angles", {})}
    o = cfg.get("offset", 1)
    off = {"c": (o, 0), "m": (0, o), "y": (-o, 0), "k": (0, 0)}
    # Volltöne (Straßen, Wege, Bahn: eine Platte fast voll) im feinen Raster aus kleinen, getrennten Punkten (Nutzerwunsch
    # 2026-11-26), sonst wären sie durchgehende Flächen; hellere Flächen im groben Raster
    fine = (amt.max(-1) > cfg.get("fine_from", .8)).astype(float)
    fine = ndimage.gaussian_filter(fine, .5 * k) > .5   # Kanten der Linien glätten
    out = np.broadcast_to(paper, img.shape).copy()
    for c, val in plates.items():
        val = ndimage.shift(val, (off[c][1] * k, off[c][0] * k), order=1, mode="nearest")   # Passer-Versatz
        fn = ndimage.shift(fine.astype(float), (off[c][1] * k, off[c][0] * k), order=0, mode="nearest")
        near = ndimage.maximum_filter(fn, size=int(2 * k) * 2 + 1)   # grobe Punkte halten Abstand von Volltönen
        a, gain, soft = np.radians(angle[c]), cfg.get("gain", 1.1), cfg.get("soft", 0)

        def screen(pt, fine_cell, cap):
            """Punkte der Rasterweite pt: Farbmenge am Punktmittelpunkt abgelesen, damit jeder Punkt ganz oder gar nicht
            gedruckt wird (Kanten schneiden keine Punkte an, Punkte ragen wie im Druck etwas über die Kante)."""
            u, v = (gx * np.cos(a) + gy * np.sin(a)) / pt, (-gx * np.sin(a) + gy * np.cos(a)) / pt
            ru, rv = np.round(u), np.round(v)
            cx, cy = ((ru * np.cos(a) - rv * np.sin(a)) * pt - ox) * k, ((ru * np.sin(a) + rv * np.cos(a)) * pt - oy) * k
            at = lambda arr, o: ndimage.map_coordinates(arr, [cy, cx], order=o, mode="nearest")
            mine = at(fn, 0) > .5 if fine_cell else at(near, 0) <= .5   # Punkt gehört zum feinen bzw. groben Raster
            r = np.sqrt(np.clip(np.minimum(at(val, 1), cap) * gain, 0, 1.6) / np.pi)   # flächentreu; ab ~1,6 voll
            px, d = pt * k, np.hypot(u - ru, v - rv)
            # weiche Kante (soft = Breite in Rasterzellen, Nutzerwunsch 2026-11-26): radialer Verlauf um den Rand r,
            # symmetrisch, daher bleibt die Farbmenge etwa gleich; kleine Punkte erreichen nie volle Deckung (blasser Hof)
            e = max(1, soft * px)
            t = np.clip((r - d) * px / e + .5, 0, 1)
            return t * t * (3 - 2 * t) * np.clip(r * px * 2 - .5, 0, 1) * mine   # kein Staub

        # Volltöne fein (kleine, getrennte Punkte), sonst grob
        dot = np.maximum(screen(pitch, False, 9), screen(pitch * cfg.get("fine", .35), True, cfg.get("fine_amount", .85)))[..., None]
        out = 1 - (1 - out) * (1 - dot * ink[c]) if light else out * (1 - dot * (1 - ink[c] / paper))
    return out


def wc_tile(base, z, x, y, sfx, post):
    """Kachel mit Pixel-Nachbearbeitung post = (watercolor|halftone, cfg): 3×3 Nachbarn (parent() merkt sie sich, jede wird von bis zu neun Kacheln gebraucht)
    zusammensetzen, mit einem Viertel Kachel Rand bearbeiten, Mitte ausschneiden."""
    import numpy as np
    from PIL import Image
    n = 2 ** z
    def get(i, j):
        try:
            return np.asarray(Image.open(io.BytesIO(parent(f"{base}/{z}/{(x + i) % n}/{y + j}{sfx}.png"))).convert("RGB"))
        except OSError:  # außerhalb der Welt (Pol): Mitte wiederholen
            return get(0, 0)
    big = np.concatenate([np.concatenate([get(i, j) for i in (-1, 0, 1)], 1) for j in (-1, 0, 1)], 0)
    s = big.shape[0] // 3
    m = s // 4
    img = big[s - m:2 * s + m, s - m:2 * s + m] / 255
    k = s / 256
    out = post[0](img, x * 256 - m / k, y * 256 - m / k, k, post[1], z)[m:m + s, m:m + s]
    buf = io.BytesIO()
    Image.fromarray((out * 255).round().astype(np.uint8)).save(buf, "PNG")
    return buf.getvalue()


def wc_static(data, post, k=1, z=17):
    """Wasserfarben auf einem einzelnen Bild (README-Vorschau, Static-API; k = Bildpixel je Weltpixel), ohne Nachbarn."""
    import numpy as np
    from PIL import Image
    img = np.asarray(Image.open(io.BytesIO(data)).convert("RGB")) / 255
    buf = io.BytesIO()
    Image.fromarray((post[0](img, 0, 0, k, post[1], z) * 255).round().astype(np.uint8)).save(buf, "PNG")
    return buf.getvalue()


def post_of(meta):
    """Pixel-Nachbearbeitung eines Stils: (Funktion, Einstellungen) aus watercolor = {…} oder halftone = {…}, sonst None."""
    for key, fn in (("watercolor", watercolor), ("halftone", halftone)):
        if key in meta:
            return fn, meta[key]
    return None


def over(data, labels):
    """Beschriftung (RGBA, transparenter Grund) über die Kachel legen."""
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    im.alpha_composite(Image.open(io.BytesIO(labels)).convert("RGBA"))
    buf = io.BytesIO()
    im.convert("RGB").save(buf, "PNG")
    return buf.getvalue()


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


def split_labels(style, shift=True):
    """--pixel: Stil in Karte ohne Beschriftung und Beschriftung allein (transparenter Grund) teilen. MapLibre richtet
    Beschriftungen nur nach anderen Beschriftungen aus. Die Beschriftung wird eine Stufe feiner gerendert als die Karte
    (OpenMapTiles hat POIs erst ab z14, zwei Stufen gröber fehlten sie ganz): Zoomverschiebung eine Stufe zurück,
    Schrift und Rand doppelt so groß, dither_tiles() fasst doppelt so große Blöcke zusammen.
    shift=False (watercolor): nur teilen, die Beschriftung bleibt, wie sie ist."""
    m, lab = json.loads(json.dumps(style)), json.loads(json.dumps(style))
    for l in m["layers"]:
        if l["type"] == "symbol":
            l.setdefault("layout", {})["visibility"] = "none"
    for l in lab["layers"]:
        lay, paint = l.setdefault("layout", {}), l.setdefault("paint", {})
        if l["type"] != "symbol":
            lay["visibility"] = "none"
            continue
        if not shift:
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
        url = f"/static/{a.lon},{a.lat},12/512x512.png"
        post = post_of(meta)
        if post:  # Karte und Beschriftung getrennt, wie in render()
            style, labels = split_labels(style, shift=False)
        with tileserver(style, f"readme-{st.stem}", mb) as base:
            data = fetch(base + url)
        if post:
            data = wc_static(data, post, 1, 13)
            with tileserver(labels, f"readme-{st.stem}-labels", mb) as base:
                data = over(data, fetch(base + url))
        if meta.get("stains"):   # Flecken/Nordlicht wie in den Kacheln (Bild wie eine @2x-Kachel bei 0/0)
            data = stain_png(data, 0, 0, meta["stains"])
        data = quantize(data, a.colors or meta.get("colors", 32))
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
    fb = bbox(a.lat, a.lon, a.radius + 1)   # Figuren bis 1 km über den Rand (Leaflet zeigt bei z15 etwas mehr)
    style, title, attribution, font = build_style(style_file, font, (a.lat, a.lon), a.pixel, a.streets_only, (mb, fb))
    # Fingerabdruck aller Eingaben: Style-JSON (Figuren, Bahnen, Sprite-Name mit Inhalts-Hash stecken darin), Stil-TOML,
    # Ausschnitt/Format und die mbtiles. ponytail: Python-Code (stain_png, dither_tiles …) fehlt, dann --force
    params = [a.lat, a.lon, a.zoom, a.radius, a.viewport, a.retina, a.detail_from, a.detail_radius, a.format,
              a.colors, a.pixel, a.streets_only, mb.stat().st_mtime, Path(style_file).read_text()]
    fp = hashlib.sha256(json.dumps([style, params], sort_keys=True, default=str).encode()).hexdigest()[:16]
    done = out / "config.json"
    if not a.force and done.exists() and json.loads(done.read_text()).get("hash") == fp:
        print(f"unverändert, übersprungen: {out}")
        return
    meta = tomllib.loads(Path(style_file).read_text())
    wc = post_of(meta)  # Wasserfarben/Druckraster: nur die Karte bearbeiten, Beschriftung danach scharf obenauf
    if a.pixel or wc:  # Beschriftung getrennt rendern, dither_tiles()/over() backt sie ein
        style, labels = split_labels(style, shift=not wc)
    stains = meta.get("stains")  # Versuch: Flecken eingebacken
    colors = a.colors or meta.get("colors", 32)  # colors im Stil: weiche Verläufe (Lichthöfe) brauchen mehr als 32
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
            elif wc:  # Beschriftung und pngquant erst im zweiten Durchgang
                if ext != "png":
                    sys.exit("watercolor/halftone nur mit PNG")
                f.write_bytes(wc_tile(base, z, x, y, sfx, wc))
                return f
            else:
                data = fetch(f"{base}/{z}/{x}/{y}{sfx}.{ext}")
                if stains and ext == "png":
                    data = stain_png(data, x, y, stains)
            if ext == "png":  # Palette mit wenigen Farben, ohne Dithering (gemessen: kleiner als WebP, gleiche Qualität)
                data = quantize(data, colors)
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
    if wc:
        parent.cache_clear()
        with tileserver(labels, out.name + "-labels", mb) as base:
            def lab(f):
                z, x = f.parts[-3:-1]
                y, sfx = f.stem.split("@") if "@" in f.stem else (f.stem, "")
                f.write_bytes(quantize(over(f.read_bytes(), fetch(f"{base}/{z}/{x}/{y}{'@' + sfx if sfx else ''}.png")), colors))
            with ThreadPoolExecutor(WORKERS) as pool:
                list(pool.map(lab, written))
    optimize(written)  # nach dem Stoppen des Containers

    cfg = dict(lat=a.lat, lon=a.lon, zmin=zmin, zmax=zmax, retina=a.retina,
               detail_from=a.detail_from, bounds=[[b[0], b[1]], [b[2], b[3]]],
               detail=[[d[0], d[1]], [d[2], d[3]]], attribution=attribution,
               style=Path(style_file).stem, font=font, ext=ext, pixel=a.pixel, streets=a.streets_only, hash=fp)
    meta = tomllib.loads(Path(style_file).read_text())  # Gliederung der Vorschau
    cfg.update(category=meta.get("category", "standard"), mode=meta.get("mode", "light"),
               family=meta.get("family", meta.get("title", Path(style_file).stem)), order=meta.get("order", 50),
               overlay=meta.get("overlay"),
               marker=dict(meta.get("marker", {"type": "leaflet"}), label=a.label or "hier"), title=title)
    (out / "config.json").write_text(json.dumps(cfg, ensure_ascii=False))  # liest write_previews()
    if standalone:  # eigenständige Kartenseite; für die Vorschau-Seite (--site) nicht nötig
        shutil.copytree(ROOT / "vendor" / "leaflet", out / "leaflet", dirs_exist_ok=True)
        write_page(out, dict(cfg, font_url=marker_font(cfg["marker"].get("font") or font, out)))
    write_previews(out.parent)
    size = sum(f.stat().st_size for f in (out / "tiles").rglob(f"*.{ext}"))
    print(f"{count} Kacheln, {size / 1e6:.1f} MB -> {out}")


def main():
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Rendert Kartenkacheln für eine Website: ein kleiner Kartenausschnitt um einen Ort, als fertige\n"
                    "Bilddateien plus index.html mit Leaflet. Die Website lädt die Karte dann ohne fremde Server.\n"
                    "Ohne Angaben: Stil Clear, Bielefeld-Innenstadt, 5 km Umkreis -> out/clear/",
        epilog="Beispiele:\n"
               '  ./make-tiles.py --place "Sparrenburg, Bielefeld" --retina\n'
               "  ./make-tiles.py --lat 52.115 --lon 8.67 --style styles/north.toml --out out/kunde-xy\n"
               "  ./make-tiles.py --all --zoom 16-16 --radius 1.5    # alle Stile zum Vergleichen, Vorschau: out/index.html\n"
               "\nDas Ergebnis (Ordner mit tiles/, leaflet/, index.html) einfach auf den Webserver kopieren.")
    p._optionals.title = "Allgemein"
    p._actions[0].help = "diese Hilfe anzeigen"
    g = p.add_argument_group("Ort")
    g.add_argument("--place", metavar="ORT", help='Ort oder Adresse, z. B. "Sparrenburg, Bielefeld"; wird über '
                   "OpenStreetMap (Nominatim) in Koordinaten umgerechnet. Ersetzt --lat/--lon")
    g.add_argument("--lat", type=float, default=52.0211, help="Breitengrad des Markers (Standard: Bielefeld)")
    g.add_argument("--lon", type=float, default=8.5347, help="Längengrad des Markers")
    g.add_argument("--area", default="detmold-regbez", metavar="GEBIET",
                   help="OSM-Daten, die heruntergeladen werden: Gebietsname bei download.geofabrik.de, "
                        "muss den Ort enthalten (Standard: detmold-regbez)")
    g = p.add_argument_group("Ausschnitt")
    g.add_argument("--radius", type=float, default=5, metavar="KM",
                   help="wie weit man die Karte verschieben kann, in km um den Marker (Standard: 5)")
    g.add_argument("--zoom", default="10-18", metavar="VON-BIS",
                   help="Zoomstufen, 10 = Region, 14 = Stadtteil, 18 = Hausnummern (Standard: 10-18)")
    g.add_argument("--detail-from", type=int, default=17, metavar="STUFE",
                   help="ab dieser Zoomstufe nur noch die nähere Umgebung rendern, spart Dateien (Standard: 17)")
    g.add_argument("--detail-radius", type=float, default=1, metavar="KM",
                   help="Größe dieser näheren Umgebung in km (Standard: 1)")
    g.add_argument("--viewport", default="2560x1440", metavar="BxH",
                   help="größte erwartete Kartengröße auf dem Bildschirm in Pixeln (Standard: 2560x1440)")
    g = p.add_argument_group("Aussehen")
    g.add_argument("--style", metavar="DATEI", help="Kartenstil, eine Datei aus styles/ (Standard: styles/clear.toml)")
    g.add_argument("--font", metavar="SCHRIFT", help='Schrift der Beschriftung, z. B. "Fira Sans" (Liste: '
                   "style/fonts.toml; Standard: die Schrift des Stils)")
    g.add_argument("--label", metavar="TEXT", help='Text am Marker (Standard: "hier")')
    g.add_argument("--retina", action="store_true", help="zusätzlich Kacheln in doppelter Auflösung für scharfe "
                   "Darstellung auf Handys und hochauflösenden Bildschirmen (etwa 4× so viel Speicher)")
    g.add_argument("--pixel", type=int, nargs="?", const=4, default=0, choices=[2, 4],
                   help="Pixel-Look wie in alten Computerspielen; --pixel allein = grobe Pixel, --pixel 2 = feinere")
    g.add_argument("--streets-only", action="store_true",
                   help="nur Straßen, Wasser und Ortsnamen, ohne Gebäude und Symbole (Poster-Look)")
    g = p.add_argument_group("Dateien")
    g.add_argument("--out", metavar="ORDNER", help="Zielordner (Standard: out/<stilname>)")
    g.add_argument("--format", choices=["png", "webp"], default="png",
                   help="Bildformat der Kacheln; png ist meist am kleinsten (Standard: png)")
    g.add_argument("--colors", type=int, metavar="ANZAHL",
                   help="Farben je PNG-Kachel; weniger = kleinere Dateien (Standard: colors im Stil, sonst 32)")
    g = p.add_argument_group("Stile vergleichen")
    g.add_argument("--all", action="store_true",
                   help="alle Stile rendern, je in einen eigenen Ordner out/<stil>-<schrift>; Vergleich: out/index.html")
    g.add_argument("--all-fonts", action="store_true", help="mit --all: jeden Stil in allen passenden Schriften (dauert lange)")
    g.add_argument("--missing", action="store_true", help="mit --all oder --site: schon gerenderte überspringen")
    g.add_argument("--regenerate", action="store_true", help="mit --all oder --site: gerenderte Stile auflisten, "
                   "ausgewählte (Nummern) löschen und neu bauen; mit --missing nur diese und fehlende")
    g.add_argument("--force", action="store_true", help="auch unveränderte Stile neu rendern (sonst übersprungen; "
                   "nötig nach Änderungen am Python-Code, z. B. an Flecken oder 8-Bit)")
    g = p.add_argument_group("Wartung")
    g.add_argument("--reindex", action="store_true",
                   help="nur die HTML-Seiten in out/ und site/ neu schreiben, ohne neu zu rendern (nach Stil-Änderungen)")
    g.add_argument("--site", action="store_true", help="öffentliche Vorschau-Website nach site/ bauen (Einstellungen: site.toml)")
    g.add_argument("--readme-previews", action="store_true", help="Vorschaubilder der Stile für die README erzeugen")
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

    if a.regenerate:
        if not (a.site or a.all):
            sys.exit("--regenerate nur mit --all oder --site")
        regenerate(ROOT / ("site" if a.site else "out"))
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
