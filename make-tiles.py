#!/usr/bin/env python3
"""Statische Leaflet-Kacheln für einen kleinen Bereich rendern.

Beispiel:
  ./make-tiles.py                               # styles/clear.toml, Bielefeld -> out/clear
  ./make-tiles.py --lat 52.115 --lon 8.67 --style styles/north.toml --out out/kunde-xy
  ./make-tiles.py --all --zoom 16-16 --radius 1.5 --retina   # jeder Stil × jede Schrift zum Vergleichen
"""
import argparse, fnmatch, re, io, tempfile, json, math, shutil, subprocess, sys, time, tomllib, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
PORT = 8089
PLANETILER = "ghcr.io/onthegomap/planetiler:latest"
TILESERVER = "docker.io/maptiler/tileserver-gl:latest"
NOTO = "https://github.com/openmaptiles/fonts/releases/download/v2.0/noto-sans.zip"


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
    tool = shutil.which("build_pbf_glyphs") or sys.exit(
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


def build_style(toml_path, font=None):
    """styles/<name>.toml + style/base.json (OSM Bright) -> fertiger Stil, Titel, Namensnennung."""
    t = tomllib.loads(Path(toml_path).read_text())
    s = json.loads((ROOT / "style" / "base.json").read_text())
    font = font or t.get("font", "Noto Sans")
    fcfg = font_config().get(font, {})
    scale = t.get("text_scale", 1) * fcfg.get("scale", 1)
    r = lambda v: round(v * scale * 2) / 2
    for l in s["layers"]:
        lay = l.setdefault("layout", {})
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
        if any(fnmatch.fnmatch(l["id"], g) for g in t.get("hide", [])):
            lay["visibility"] = "none"
        # [paint."muster"] / [layout."muster"]: nur Eigenschaften, die zum Ebenentyp passen
        prefixes = ("text-", "icon-", "symbol-") if l["type"] == "symbol" else (l["type"] + "-",)
        for kind in ("paint", "layout"):
            for glob, props in t.get(kind, {}).items():
                if fnmatch.fnmatch(l["id"], glob):
                    l.setdefault(kind, {}).update(
                        {k: v for k, v in props.items() if k.startswith(prefixes) or k == "visibility"})
    return s, f"{t.get('title', Path(toml_path).stem)} · {font}", t.get("attribution", ""), font


def write_previews(outdir):
    """Vergleichsseiten + variants.js (Titel und Konfiguration aller Varianten) nach outdir."""
    for f in ("compare.html", "streifen.html"):
        shutil.copy(ROOT / f, outdir / f)
    shutil.copytree(ROOT / "vendor" / "leaflet", outdir / "leaflet", dirs_exist_ok=True)
    names = sorted(d.name for d in outdir.iterdir() if (d / "index.html").exists())
    titles, configs = {}, {}
    for n in names:
        page = (outdir / n / "index.html").read_text()
        titles[n] = re.search(r"<title>(.*?)</title>", page)[1]
        configs[n] = json.loads(re.search(r"const c = (\{.*\});", page)[1])
    (outdir / "variants.js").write_text(
        f"const VARIANTS = {json.dumps(names)};\n"
        f"const TITLES = {json.dumps(titles, ensure_ascii=False)};\n"
        f"const CONFIGS = {json.dumps(configs, ensure_ascii=False)};\n")


def render(a, style_file, out, mb, font=None):
    zmin, zmax = map(int, a.zoom.split("-"))
    vw, vh = map(int, a.viewport.split("x"))
    b = bbox(a.lat, a.lon, a.radius)
    # ponytail: high zooms only near the marker; Leaflet upscales z(detail_from-1) outside
    d = bbox(a.lat, a.lon, min(a.radius, a.detail_radius))
    style, title, attribution, font = build_style(style_file, font)
    built = DATA / f"style-{out.name}.json"
    built.write_text(json.dumps(style, ensure_ascii=False))

    name = f"tiles-{PORT}"
    run("podman", "run", "-d", "--rm", "--name", name, "-p", f"127.0.0.1:{PORT}:8080",
        "-v", f"{ROOT / 'style'}:/data:Z", "-v", f"{mb}:/data/tiles.mbtiles:ro,Z",
        "-v", f"{built}:/data/style.json:ro,Z",
        TILESERVER, "--config", "/data/config.json")
    try:
        base = f"http://127.0.0.1:{PORT}/styles/map"
        for _ in range(60):
            try:
                fetch(f"http://127.0.0.1:{PORT}/health")
                break
            except OSError:
                time.sleep(1)
        else:
            sys.exit("tileserver-gl startet nicht: podman logs " + name)

        shutil.rmtree(out / "tiles", ignore_errors=True)
        count = 0
        for z in range(zmin, zmax + 1):
            for x, y in (tiles_for(d, z, 0, 0) if z >= a.detail_from else tiles_for(b, z, vw, vh)):
                for sfx in ["", "@2x"] if a.retina else [""]:
                    f = out / "tiles" / str(z) / str(x) / f"{y}{sfx}.webp"
                    f.parent.mkdir(parents=True, exist_ok=True)
                    f.write_bytes(fetch(f"{base}/{z}/{x}/{y}{sfx}.webp"))
                    count += 1
            print(f"{out.name}: z{z} fertig", flush=True)
    finally:
        subprocess.run(["podman", "stop", name], capture_output=True)

    shutil.copytree(ROOT / "vendor" / "leaflet", out / "leaflet", dirs_exist_ok=True)
    page = (ROOT / "template.html").read_text()
    cfg = dict(lat=a.lat, lon=a.lon, zmin=zmin, zmax=zmax, retina=a.retina,
               detail_from=a.detail_from, bounds=[[b[0], b[1]], [b[2], b[3]]],
               detail=[[d[0], d[1]], [d[2], d[3]]], attribution=attribution,
               style=Path(style_file).stem, font=font)
    page = page.replace("<title>Karte</title>", f"<title>{title}</title>")
    (out / "index.html").write_text(page.replace("/*CONFIG*/{}", json.dumps(cfg, ensure_ascii=False)))
    write_previews(out.parent)
    size = sum(f.stat().st_size for f in (out / "tiles").rglob("*.webp"))
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
    p.add_argument("--style", help="Standard: styles/clear.toml; mit --all: nur dieser Stil")
    p.add_argument("--font", help="Schrift statt der des Stils; mit --all: nur diese Schrift")
    p.add_argument("--all", action="store_true", help="jeder Stil × seine Schriftgruppen nach out/<stil>-<schrift>")
    p.add_argument("--out", help="Standard: out/<stilname>")
    a = p.parse_args()
    zmin, zmax = map(int, a.zoom.split("-"))
    if not (0 <= zmin <= zmax <= 20):
        sys.exit("--zoom ungültig")

    mb = ensure_mbtiles(a.area)
    ensure_noto()
    ensure_glyphs()
    if not a.all:
        st = Path(a.style or ROOT / "styles" / "clear.toml")
        render(a, st, Path(a.out) if a.out else ROOT / "out" / st.stem, mb, a.font)
        return
    for st in [Path(a.style)] if a.style else sorted((ROOT / "styles").glob("*.toml")):
        groups = tomllib.loads(st.read_text()).get("fonts", ["sans", "serif"])
        for font in [a.font] if a.font else fonts(groups):
            slug = font.lower().replace(" ", "-")
            render(a, st, ROOT / "out" / f"{st.stem}-{slug}", mb, font)


if __name__ == "__main__":
    main()
