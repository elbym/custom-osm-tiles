# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Pre-renders static Leaflet tiles (palette PNG via pngquant by default, or WebP) for a small area around one marker, one set per website project. The site then needs no third-party map requests (privacy). User-facing docs are in German (README.md); answer the user in German. Remote: public GitHub repo `elbym/custom-osm-tiles` (renamed from `tiles`; local folder is still `tiles`).

## Commands

```sh
pip install -r requirements.txt && cargo install build_pbf_glyphs   # once; podman (not docker) and pngquant must be installed

./make-tiles.py                                        # defaults: styles/clear.toml, Bielefeld, 5 km, z10-18 -> out/clear
./make-tiles.py --lat 52.115 --lon 8.67 --style styles/north.toml --font Inter --retina --out out/kunde-xy
./make-tiles.py --all --zoom 16-16 --radius 1.5 --retina   # preview set: each style in its preview_font -> out/<style>-<font> (~2 min)
./make-tiles.py --all --all-fonts --missing ...           # full matrix: each style × every font of its groups (slow)
./make-tiles.py --all --style styles/wiki.toml ...     # one style (preview_font; add --all-fonts for all);  --font X: one font for all styles, ignoring groups
./make-tiles.py --site [--missing]                     # public preview per site.toml (Berlin, z16, retina) -> site/ for GitHub Pages
npm install && npm run css                             # rebuild vendor/streifen.css (Tailwind v4) after changing streifen.html classes
./make-tiles.py --readme-previews                      # docs/previews/<style>.png: 512×512, z12, no marker (README gallery, ~30 s)
./make-tiles.py --reindex [--label "Firma"]            # rewrite all out/*/index.html from template + styles, no rendering
```

There are no tests. To check a rendering change, re-render and look at a tile near the marker. For the Bielefeld default that is `out/<variant>/tiles/16/34321/21641.png`, or `.webp` with `--format webp` (z18: `18/137286/86565`). `magick` builds contact sheets. Check the preview pages with headless Chromium, because the Chrome extension is usually not connected:
`chromium-browser --headless=new --allow-file-access-from-files --virtual-time-budget=8000 --window-size=1800,900 --screenshot=… "file://…/out/streifen.html?cat=nerd&mode=dark"`

## How it fits together

`make-tiles.py` drives everything; its only Python dependency is fontTools, called as a subprocess.

1. `ensure_mbtiles()` runs a Planetiler container that builds `data/<area>.mbtiles` (OpenMapTiles schema) from a Geofabrik extract, default `detmold-regbez`. The result is cached; delete it to refresh the OSM data.
2. `ensure_noto()` downloads the Noto Sans fallback glyphs. `ensure_glyphs()` builds any other missing glyph folders (see Fonts).
3. `build_style()` merges `styles/<name>.toml` into `style/base.json` and writes `data/style-<out>.json`.
4. `render()` starts tileserver-gl on **127.0.0.1:8089**, because 8080 is taken by ddev on this machine.
   - Mounts: `style/` as `/data`, the mbtiles as `/data/tiles.mbtiles`, the built style over `/data/style.json`. `style/config.json` holds the font and sprite paths and the renderer pools.
   - It fetches the needed `{z}/{x}/{y}[@2x].png|webp` with `WORKERS = 4` parallel requests, then stops the container.
   - Measured for 198 z16 retina tiles: 1 worker 8.5 s, 4 workers 2.6 s, 8 or more about 3.4 s, because rendering and WebP encoding already use several cores. Container start is about 0.7 s, so one container per variant is fine.
   - Format: by default each tile is fetched as PNG and piped through `pngquant <colors> --nofs --strip` (`--colors`, default 24). Measured: 24 colours match WebP's error (about 0.9 %) at about 8 % less size, and ImageMagick quantising is 3–4× slower. `--format webp` keeps the old path. The extension is stored as `ext` in the config, and `template.html`/`streifen.html` build tile URLs from it.
   - Finally it fills `template.html` into `out/<name>/index.html` by replacing the `/*CONFIG*/{}` placeholder with JSON. The config includes `style`, `font`, `category`, `mode`, `family` and `attribution`.
`tileserver(style, tag, mb)` is the context manager both paths share. `render()` fetches tiles through it. `readme_previews()` fetches one tileserver static image per style (`/styles/map/static/lon,lat,12/512x512.png`) in its `preview_font`, runs it through pngquant and writes it to `docs/previews/`. The README gallery is a Hell/Dunkel table per family that links those files, so update it when styles are added or renamed.
5. `write_previews()` copies `compare.html`, `streifen.html` and Leaflet into `out/`, and regenerates `out/variants.js` (`VARIANTS`, `TITLES`, `CONFIGS`) from every `out/*/index.html`.

**The script and `template.html` are coupled.** The tile coverage in `tiles_for()` assumes Leaflet's `maxBounds` = the `--radius` bbox:
- At low zooms the view is bigger than the bbox, so one `--viewport` worth of tiles is rendered around it.
- From `--detail-from` (17) on, only `--detail-radius` is rendered. The template's base layer uses `maxNativeZoom` = detail_from−1 to upscale outside that area.
- Change both sides together.
- Vector data stops at z14; tileserver-gl overzooms for z15–18.

**Public site:**
- `build_site()` reads `site.toml` and renders each style × the fonts of its category into `site/`.
- It turns `streifen.html` into `site/index.html`, drops `compare.html`, and adds `.nojekyll`.
- Publish `site/` as an orphan `gh-pages` branch (force-pushed, no history). Never commit tiles to `main`. The Pages limit is 1 GB.
- `streifen.html` is styled with Tailwind v4, built locally into `vendor/streifen.css`, never from a CDN.
  - The `dark:` variant is bound to `<html data-mode>`, which follows the page's light/dark switch.
  - Classes set from JS are fine, because Tailwind scans the HTML source.
  - Portrait screens get horizontal strips: `clip()` checks `matchMedia('(orientation: portrait)')`.
- The "Über" dialog holds all attributions. Keep it complete; the user insisted on this.

**Preview pages** (opened via file://):
- Both pages filter by `category` (standard|nerd) and `mode` (light|dark), and pair styles via `family`.
- `streifen.html` is one Leaflet map with one tile layer per family, each in its own pane that is cut to a vertical strip with a `clip-path` polygon. Panes live inside the translated mapPane, so `clip()` subtracts the mapPane position on every move or zoom.
- `compare.html` is a 2×2 grid of iframes. Switching mode swaps each pick for its family counterpart in the same font.
- Map sync uses `postMessage`, because file:// iframes are cross-origin: `template.html` posts on `moveend` when framed, and `compare.html` forwards the message to the other frames.

## Styles

- `style/base.json` is OpenFreeMap's OSM Bright, kept close to upstream. The only changes: the source is `mbtiles://{osm}`, the `ne2_shaded` raster layer is removed, and glyphs and the sprite (`ofm*`) are local. Do all customisation in `styles/*.toml`.
- TOML keys:
  - `title` is the window title; the font name is appended.
  - `category`, `mode` and `family` drive the preview pages.
  - `preview_font` is the only font `--all` renders, unless `--all-fonts` is given: Fira Sans for standard styles and Maple Mono for nerd styles, at the user's request, to keep preview renders fast.
  - `font` is the default font. It replaces "Noto Sans" in every `text-font`, and Noto stays in the stack as fallback.
  - `fonts` lists the font groups that `--all --all-fonts` renders. The default is `["sans", "serif"]`; the editor themes add `"mono"`. A single run with `--font`, or `--all --font X`, ignores the groups.
  - `text_scale` scales `text-size`, except the `*shield*` layers.
  - `hide` is a list of layer-id globs to hide.
  - `[paint."glob"]` / `[layout."glob"]` set properties on matching layer ids. They apply in file order, so the last match wins. Only properties whose prefix fits the layer type are applied, which makes broad globs like `water*` safe.
- Marker: the `[marker]` table in a style is written into the config as `marker` (+ `label` from `--label`, default "hier").
  - `template.html`'s `markerIcon()` draws `type = "terminal"` as an `L.divIcon` (box `~/<label>` + static block cursor, no blinking (user request), + stem + dot, anchored on the dot). `type = "bubble"` (all standard styles) is a speech bubble modelled on Heroicons "chat-bubble-bottom-center": rounded box with the label, plus a centred SVG tail at the bottom whose tip is the anchor. Its colours `color`/`bg`/`fg` follow the style's accent and mode. Anything else falls back to `L.Icon.Default`.
  - The label is set via `textContent`, never as HTML.
  - `streifen.html` carries a copy of `markerIcon()` and its CSS, and uses the middle strip's marker. Keep both copies in sync.
- `--reindex` rewrites every `out/*/index.html` from `template.html` and the current style metadata (category, mode, family, attribution, marker) without rendering. Use it after template or marker changes.
- Nerd styles show green areas (`park`, `landcover-*`, `landuse-cemetery`, `landcover-wood`) in the theme's signature colour instead of green (Tokyo Night magenta2 pink, Dracula/Alucard purple, Catppuccin peach, Nightfox/Dayfox cyan, Solarized yellow), mixed with the background: dark 20 % (wood 28 %), light 25 % (wood 35 %). Exception: in solarized-dark the RGB mix with the teal base turned green, so it uses an OKLCH dark gold (#4b3b13 / #5b4717). This was a user request; Tokyo Night uses `magenta2`.
- Nerd styles end with a `# >>> Akzent-Beschriftung … # <<<` block. It hides the white shield sprite (`icon-image = ""`, because sprite PNGs cannot be recoloured) and colours road refs by class with a `match` expression: motorway / trunk+primary / rest, using the theme's accent colours. Major road names get the primary accent too. Keep the block at the end of the file so it wins.
- POI layers: a low `rank` means important, so `poi_r1` holds the most important places and `poi_r20` the least. Hide `poi_r20`, not `poi_r1`.
- Styles and their user-chosen names:
  - **Standard:**
    - `clear` (own design, default).
    - `cupertino`: borrows only the overall look of Apple Maps. Own colours, no Apple assets, and no "Apple" in the public attribution.
    - `north`: Hydda palette.
    - `osm-light`: a lighter, decluttered osm.org standard map.
    - `wiki`: Wikimedia Maps colours from wikimedia/osm-bright.tm2. The design is CC BY 3.0, so this attribution must stay, in `wiki-dark` too.
  - **Standard dark:** `clear-dark`, `cupertino-dark`, `north-dark`, `osm-dark`, `wiki-dark`.
  - **Nerd** (editor-theme palettes): `dayfox`/`nightfox`, `catppuccin-latte`/`-mocha`, `dracula-light` ("Alucard", the official Dracula light palette) / `dracula`, `solarized-light`/`-dark` (all MIT), and `tokyonight-day`/`-night` (Apache-2.0).
- For the recreations, only colour values were taken from the originals, never their style files. That is what the user asked for, to avoid licence problems, and each recreation names its inspiration in `attribution`.
- Dark and editor-theme styles share one role mapping: bg, landuse, buildings, water, green, three road tiers, text.
  - The `*-dark` standard styles were derived in OKLCH, not by inversion (inversion makes white roads darker than the ground). The light background's hue becomes a dark neutral ramp, and accents are relit.
  - Dark styles need the `highway-area` and `aeroway-*` overrides, otherwise OSM Bright's light grey pedestrian areas glare. They also need lighter minor roads to stand out from buildings.
  - The generator scripts were one-offs and are not in the repo. The TOMLs are now the source of truth; edit them by hand.

## Fonts

- Only the sources plus licences (`fonts-src/<font>/`) are in git. `style/fonts/` is gitignored and built by `ensure_glyphs()` from the face specs in `style/fonts.toml`.
- `style/fonts.toml`: each table is one font (one variant per style under `--all --all-fonts`).
  - Faces are `Regular`/`Bold`/`Italic` = `{ file, <axis> = value }`. Faces with axes are cut from variable fonts with `fontTools.varLib.instancer`; the rest are copied.
  - Optional keys: `group` (sans|serif|mono), `scale` (multiplies `text_scale`), and `streets` (a face suffix used for the `highway-name*` layers).
- The temp file is named `<Font> <Face>.ttf`, because `build_pbf_glyphs` names output folders after the file stem.
- Only missing folders are rebuilt, so delete a folder after changing its spec.
- Noto Sans is deliberately absent from `fonts.toml`: it is fallback only, because the user dislikes it as a label font.
- `brotli` is not installed, so take new fonts as TTF/OTF from upstream (google/fonts, CTAN), not WOFF2.
