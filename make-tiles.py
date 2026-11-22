#!/usr/bin/env python3
"""Statische Leaflet-Kacheln für einen kleinen Bereich rendern.

Beispiel:
  ./make-tiles.py --lat 52.115 --lon 8.67 --radius 5 --out out/kunde-xy
"""
import argparse, io, json, math, shutil, subprocess, sys, time, urllib.request, zipfile
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


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--radius", type=float, default=5, help="km um den Marker")
    p.add_argument("--zoom", default="10-18", help="z. B. 10-14")
    p.add_argument("--detail-from", type=int, default=17, help="ab dieser Stufe nur --detail-radius")
    p.add_argument("--detail-radius", type=float, default=1, help="km, für die Detailstufen")
    p.add_argument("--viewport", default="2560x1440", help="größte Kartengröße in px")
    p.add_argument("--area", default="detmold-regbez", help="Geofabrik-Name")
    p.add_argument("--retina", action="store_true", help="zusätzlich @2x rendern")
    p.add_argument("--out", required=True)
    a = p.parse_args()
    zmin, zmax = map(int, a.zoom.split("-"))
    vw, vh = map(int, a.viewport.split("x"))
    if not (0 <= zmin <= zmax <= 20):
        sys.exit("--zoom ungültig")

    mb = ensure_mbtiles(a.area)
    ensure_noto()
    out = Path(a.out)
    b = bbox(a.lat, a.lon, a.radius)
    # ponytail: high zooms only near the marker; Leaflet upscales z(detail_from-1) outside
    d = bbox(a.lat, a.lon, min(a.radius, a.detail_radius))

    name = f"tiles-{PORT}"
    run("podman", "run", "-d", "--rm", "--name", name, "-p", f"127.0.0.1:{PORT}:8080",
        "-v", f"{ROOT / 'style'}:/data:Z", "-v", f"{mb}:/data/tiles.mbtiles:ro,Z",
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

        count = 0
        for z in range(zmin, zmax + 1):
            for x, y in (tiles_for(d, z, 0, 0) if z >= a.detail_from else tiles_for(b, z, vw, vh)):
                for sfx in ["", "@2x"] if a.retina else [""]:
                    f = out / "tiles" / str(z) / str(x) / f"{y}{sfx}.png"
                    f.parent.mkdir(parents=True, exist_ok=True)
                    f.write_bytes(fetch(f"{base}/{z}/{x}/{y}{sfx}.png"))
                    count += 1
            print(f"z{z} fertig", flush=True)
    finally:
        subprocess.run(["podman", "stop", name], capture_output=True)

    shutil.copytree(ROOT / "vendor" / "leaflet", out / "leaflet", dirs_exist_ok=True)
    page = (ROOT / "template.html").read_text()
    cfg = dict(lat=a.lat, lon=a.lon, zmin=zmin, zmax=zmax, retina=a.retina,
               detail_from=a.detail_from, bounds=[[b[0], b[1]], [b[2], b[3]]],
               detail=[[d[0], d[1]], [d[2], d[3]]])
    (out / "index.html").write_text(page.replace("/*CONFIG*/{}", json.dumps(cfg)))
    size = sum(f.stat().st_size for f in (out / "tiles").rglob("*.png"))
    print(f"{count} Kacheln, {size / 1e6:.1f} MB -> {out}")


if __name__ == "__main__":
    main()
