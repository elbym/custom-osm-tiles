# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Pre-renders static Leaflet raster tiles for a small area around one marker, per website project, so the site needs no third-party map requests (privacy). User-facing docs are in German (README.md); answer the user in German.

## Commands

```sh
# podman required, not docker; defaults = styles/clear.toml, Bielefeld, 5 km, z10-18 -> out/clear
./make-tiles.py
./make-tiles.py --lat 52.115 --lon 8.67 --style styles/north.toml --out out/kunde-xy
./make-tiles.py --all --zoom 16-16 --radius 1.5 --retina   # every style × every font -> out/<style>-<font>, for comparing
# preview: open out/<name>/index.html or out/compare.html directly via file://
```

There are no tests. To check a rendering change, re-render and look at a tile near the marker, e.g. `out/clear/tiles/16/34321/21641.webp` (after `--all`: `out/clear-overpass/…`) (z18: `18/137286/86565`) for the Bielefeld default. `magick` is installed to turn WebP into PNG contact sheets.

## How it fits together

- `make-tiles.py` (stdlib only) does everything:
  1. Planetiler container builds `data/<area>.mbtiles` from a Geofabrik extract (default `detmold-regbez`). The result is cached; delete it to refresh the OSM data.
  2. `build_style()` turns `styles/<name>.toml` + `style/base.json` into `data/style-<name>.json`.
  3. Starts tileserver-gl on **127.0.0.1:8089**, because 8080 is taken by ddev on this machine. `style/` is mounted as `/data`, the mbtiles as `/data/tiles.mbtiles`, and the built style over `/data/style.json`. Fonts and sprites resolve via `style/config.json`.
  4. Fetches only the needed `{z}/{x}/{y}.webp`, stops the container, copies `vendor/leaflet/` and fills `template.html` (replacing the `/*CONFIG*/{}` placeholder with JSON) into `out/<name>/index.html`.
- **The script and `template.html` are coupled.** The tile coverage in `tiles_for()` assumes Leaflet's `maxBounds` = the `--radius` bbox:
  - At low zooms the viewport is bigger than the bbox, so the script renders one `--viewport` worth of tiles around it.
  - From `--detail-from` (17) on, tiles are rendered only within `--detail-radius`. The template's base layer uses `maxNativeZoom` = detail_from−1 to upscale outside that area.
  - Change both sides together.
- `streifen.html`: one Leaflet map with one tile layer per style (same font, `?font=`). Each layer sits in its own pane, and the pane is cut to its vertical strip with a `clip-path` polygon. Panes live inside the translated mapPane, so `clip()` subtracts the mapPane position on every move or zoom. It needs `style`/`font` in each variant's config, which `render()` writes into `index.html` and `write_previews()` collects into `variants.js` as `CONFIGS`.
- Verify preview pages with headless Chromium: `chromium-browser --headless=new --allow-file-access-from-files --virtual-time-budget=8000 --screenshot=… file://…/out/streifen.html`. The Chrome extension is usually not connected.
- Each run (via `write_previews()`) copies `compare.html` (2×2 grid), `streifen.html` and Leaflet to `out/` and regenerates `out/variants.js` (all dirs with an `index.html`, titles read from their `<title>`). Map sync uses `postMessage`, because file:// iframes are cross-origin: `template.html` posts on `moveend` when inside an iframe, and `compare.html` forwards the message to all other frames.
- Vector data only goes to z14; tileserver-gl overzooms for z15–18.

## Styles

- `style/base.json` is OpenFreeMap's OSM Bright, kept as close to upstream as possible. The only changes:
  - the source is `mbtiles://{osm}`, and the `ne2_shaded` raster layer is removed;
  - glyphs and the sprite (`ofm*`) are local.
  
  Do all customisation in `styles/*.toml`, not in `base.json`.
- TOML keys:
  - `title` is the window/tab title; the font name is appended automatically.
  - `font` replaces "Noto Sans" in every `text-font`. Noto stays in the stack as fallback. `--all` ignores it and loops over `fonts(groups)`, which are the tables in `style/fonts.toml` whose `group` is in the style's `fonts` list (default `["sans", "serif"]`; the editor themes add `"mono"`). Noto Sans is deliberately not there: it is fallback only, because the user dislikes it as a label font. `--font` overrides it, and with `--all` it limits the loop to that one font.
  - `text_scale` scales all `text-size` values except the `*shield*` layers. It is multiplied by `scale` from the font's table in `style/fonts.toml`. That table can also set `streets` = a face suffix (e.g. `"450"`) used for the `highway-name*` layers instead of Regular. `brotli` is not installed, so take new fonts as TTF/OTF from upstream (google/fonts, CTAN), not WOFF2.
  - `hide` is a list of layer-id globs to hide.
  - `[paint."glob"]` / `[layout."glob"]` set properties on matching layer ids. They apply in file order, so the last match wins. Only properties whose prefix fits the layer type are applied, which makes broad globs like `water*` safe.
- Styles, with the user-chosen names:
  - `clear` ("Clear") is our own design and the default.
  - `cupertino` ("Cupertino") only borrows the overall look of Apple Maps: own colours, no Apple assets, and no "Apple" in the public attribution.
  - `north` ("North") recreates Hydda's palette.
  - `osm-light` ("OSM light") is a lighter, decluttered take on the osm.org standard map.
  - `dayfox`/`nightfox`, `catppuccin-latte`/`catppuccin-mocha`, `dracula` and `solarized-*` (MIT), plus `tokyonight-*` (Apache-2.0), use editor-theme palettes. They all share one role mapping (bg, buildings, water, green, road tiers, text). Dark variants need the `highway-area` and `aeroway-*` overrides, otherwise OSM Bright's light grey pedestrian areas glare. They also need lighter minor roads (surface2) to stand out from buildings.
  - `wiki` ("Wiki") recreates Wikimedia Maps. Its colours come from wikimedia/osm-bright.tm2, whose design is CC BY 3.0, so its `attribution` must stay.
- POI layers: a low `rank` means important, so `poi_r1` holds the most important places and `poi_r20` the least. Hide `poi_r20`, not `poi_r1`.
- For the recreations, only colour values were taken from the originals, never their style files. That is what the user asked for, to avoid licence problems, and each recreation names its inspiration in `attribution`.
- Fonts: only the sources plus licences (`fonts-src/<font>/`) are in git. `style/fonts/` is gitignored.
  - `ensure_glyphs()` builds any missing `style/fonts/<Font> <Face>/` from the face specs in `style/fonts.toml` (`{ file, <axis> = value }`).
  - Faces with axes are cut with `fontTools.varLib.instancer`; the rest are copied. The temp file is named `<Font> <Face>.ttf`, because `build_pbf_glyphs` names output folders after the file stem.
  - It only rebuilds missing folders, so delete a folder after changing its spec.
  - Needs fontTools (`requirements.txt`) and `build_pbf_glyphs` (cargo).
  - Noto Sans glyphs (100 MB) are downloaded ready-made by `ensure_noto()`.
