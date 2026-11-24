# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Pre-renders static Leaflet tiles (palette PNG via pngquant by default, or WebP) for a small area around one marker, one set per website project. The site then needs no third-party map requests (privacy). User-facing docs are in German (README.md); answer the user in German. Remote: public GitHub repo `elbym/custom-osm-tiles` (renamed from `tiles`; local folder is still `tiles`).

## Commands

```sh
pip install -r requirements.txt && cargo install build_pbf_glyphs oxipng   # once; podman (not docker) pngquant and inkscape must be installed

./make-tiles.py                                        # defaults: styles/clear.toml, Bielefeld, 5 km, z10-18 -> out/clear
./make-tiles.py --lat 52.115 --lon 8.67 --style styles/north.toml --font Inter --retina --out out/kunde-xy
./make-tiles.py --all --zoom 16-16 --radius 1.5 --retina   # preview set: each style in its preview_font -> out/<style>-<font> (~4 min for 34 styles)
./make-tiles.py --all --all-fonts --missing ...           # full matrix: each style × every font of its groups (slow)
./make-tiles.py --all --style styles/wiki.toml ...     # one style (preview_font; add --all-fonts for all);  --font X: one font for all styles, ignoring groups
./make-tiles.py --site [--missing]                     # public preview per site.toml (Bielefeld/Sparrenburg, z16, retina, 8-bit for nerd; ~520 MB) -> site/ for GitHub Pages
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
   - Format: by default each tile is fetched as PNG and piped through `quantize()`: `pngquant <colors> --nofs --strip` (`--colors`, default 32), and `optimize()` runs `oxipng -o 2` over the new files after the container has stopped (optional; looked up in PATH and `~/.cargo/bin`). Measured on 80 retina tiles around the Sparrenburg: oxipng saves 7–10 % losslessly (about 0.2 s per tile on this 2-core VM); 32 colours + oxipng is the size of 24 without it, but more accurate (RMSE 0.70 % vs 0.88 %). 16 colours + oxipng would be 19 % smaller with no visible difference in samples, 12 loses icon colours. ImageMagick quantising is 3–4× slower. `--format webp` keeps the old path. The extension is stored as `ext` in the config, and `template.html`/`streifen.html` build tile URLs from it.
   - Finally it fills `template.html` into `out/<name>/index.html` by replacing the `/*CONFIG*/{}` placeholder with JSON. The config includes `style`, `font`, `category`, `mode`, `family` and `attribution`.
`tileserver(style, tag, mb)` is the context manager both paths share. `render()` fetches tiles through it. `readme_previews()` fetches one tileserver static image per style (`/styles/map/static/lon,lat,12/512x512.png`) in its `preview_font`, runs it through pngquant and writes it to `docs/previews/`. The README gallery is a Hell/Dunkel table per family that links those files, so update it when styles are added or renamed.
5. `write_previews()` copies `compare.html`, `streifen.html` and Leaflet into `out/`, and regenerates `out/variants.js` (`VARIANTS`, `TITLES`, `CONFIGS`) from every `out/*/index.html`.

**The script and `template.html` are coupled.** The tile coverage in `tiles_for()` assumes Leaflet's `maxBounds` = the `--radius` bbox:
- At low zooms the view is bigger than the bbox, so one `--viewport` worth of tiles is rendered around it.
- From `--detail-from` (17) on, only `--detail-radius` is rendered. The template's base layer uses `maxNativeZoom` = detail_from−1 to upscale outside that area.
- Change both sides together.
- Vector data stops at z14; tileserver-gl overzooms for z15–18.

**Public site:**
- `build_site()` reads `site.toml` and renders each style × the fonts of its category into `site/`. Since 2026-11-22 one font per category (Fira Sans / Maple Mono) to halve the render time on the 2-core VM.
- It deletes `site/` variants that the current `site.toml` no longer produces (old fonts or area), otherwise `variants.js` would list them.
- It turns `streifen.html` into `site/index.html`, drops `compare.html`, and adds `.nojekyll`.
- Publish `site/` as an orphan `gh-pages` branch (force-pushed, no history). Never commit tiles to `main`. The Pages limit is 1 GB.
- `streifen.html` is styled with Tailwind v4, built locally into `vendor/streifen.css`, never from a CDN.
  - The `dark:` variant is bound to `<html data-mode>`, which follows the page's light/dark switch. Without `?mode`, the mode follows `prefers-color-scheme` (reload on change).
  - Classes set from JS are fine, because Tailwind scans the HTML source.
  - Split: the "Teilung" switch sets `?split=cols|rows` (no reload); without it, portrait gets rows. `setSplit()` writes `<html data-split>`, which drives the custom variants `cols:`/`rows:` (title layout, bar position) and `clip()`.
  - Full screen on iPhone: `#map` and `#titles` are `fixed h-lvh` (behind Safari's bars, `viewport-fit=cover`); `.leaflet-bottom` is lifted by `100lvh - 100dvh + safe-area` so zoom and attribution stay visible.
  - Phone (custom variant `compact:` in `src/streifen.css` = portrait or height ≤ 32rem; user request 2026-11-23):
    - `#bar` is hidden. Instead a bottom navigation bar `#nav` (thumb reach) holds ‹ › (`data-step`; swiping over the bar also steps), the style name (opens the `#jump` style list) and ⚙︎ (opens the `#sheet` options).
    - Both are bottom-sheet `<dialog>`s. JS (`place()`) moves `#bar-items` into `#sheet`, where `compact:` classes stack it as large controls.
    - Without `?solo`, phones start in single view on the first style. "Alle" is remembered as an empty `?solo=`. `data-solo` on `<html>` (variant `solo:`) hides `#titles` there.
    - `.leaflet-bottom` is lifted above `#nav`.
- The "Stile" dropdown (`<details id="pick">`) lists the families of the current category as checkboxes. Unchecked ones go into `?aus=Fam1,Fam2`, applied (page reload) when the dropdown closes; at least one strip always stays, and switching category clears `aus`.
- Single view (`?solo=Family`, user request 2026-11-23): the always-visible group "‹ Alle ›" at the top of `#bar` shows one style full-screen and steps through the rendered families without reloading. Hidden strips get their tile layers removed, and the marker takes the shown style. On phones see `#nav` above.
- Compare (`?solo=A&vs=B`, user request 2026-11-23): the "⇆ Vergleich" button (in `#solo` and in `#nav`, both `[data-cmp]`) shows A left/top and B right/bottom, split at `frac` by `clip()`'s `part()`. The `#divider` line has name tags and a `#handle`: dragging moves the line, tapping swaps A and B. ‹ › and the `#jump` list change B; "Alle" ends compare. The direction follows `split`.
- The "Über" dialog holds all attributions. Keep it complete; the user insisted on this.

**Preview pages** (opened via file://):
- Both pages filter by `category` (standard|nerd) and `mode` (light|dark), and pair styles via `family`.
- `streifen.html` is one Leaflet map with one tile layer per family, each in its own pane that is cut to a vertical strip with a `clip-path` polygon. Panes live inside the translated mapPane, so `clip()` subtracts the mapPane position on every move or zoom.
- `compare.html` is a 2×2 grid of iframes. Switching mode swaps each pick for its family counterpart in the same font.
- Map sync uses `postMessage`, because file:// iframes are cross-origin: `template.html` posts on `moveend` when framed, and `compare.html` forwards the message to the other frames.

**Schema choice:** OpenMapTiles was kept on purpose (comparison table in README, "Warum OpenMapTiles?").
- Shortbread (Geofabrik, CC0): leaner, POIs mostly only from z14, little ranking.
- Protomaps Basemap (BSD/CC0): a per-feature `min_zoom`, data up to z15.
- From z14 on, all three carry full OSM detail. They only differ at z10–13.
- Switching would mean rewriting `style/base.json` and every style's layer globs, only to drop the "© OpenMapTiles" credit. The user decided not to switch (2026-11-23). We rely on OMT's `rank` (e.g. hiding `poi_r20`).

## Styles

- POI icons: `build_style()` points `sprite` at `poi_sprite(weight, bg, accent, glyph, dark)`, a copy of `style/ofm(@2x)` in `style/sprites/`. That folder is gitignored, mounted as `/data` in the container, and cached per combination.
  - Every image listed in `style/icons.toml` (OSM Bright sprite name without `_11` → Phosphor icon, vendored in `vendor/phosphor/<weight>/`, MIT) is erased and redrawn as one SVG, rendered by a single Inkscape call.
  - Drawing: circle in the marker accent mixed over the background (dark 22 %, light 16 %), ring 45 %, glyph 62 % of the circle in the style's `poi_*` text colour.
  - Motifs Phosphor lacks are drawn by us in `vendor/phosphor-extra/` (8 icons). They are line art with `stroke-width="16"`, which `poi_sprite()` replaces per weight via `STROKE` (light 12, regular 16, bold 24). Already requested upstream: helicopter #909, playground #577 (phosphor-icons/homepage). Phosphor does not accept icon contributions, only requests.
  - Weight follows the font group: mono → bold, serif → light, else regular.
  - Shapes, shields and patterns stay from ofm.
  - User request (2026-11-23): Phosphor instead of the white OSM Bright discs, still in a circle, the circle a subtle variant of the accent. Sprite PNGs cannot be recoloured by paint properties (not SDF).
- `style/base.json` is OpenFreeMap's OSM Bright, kept close to upstream. The only changes: the source is `mbtiles://{osm}`, the `ne2_shaded` raster layer is removed, and glyphs and the sprite (`ofm*`) are local. Do all customisation in `styles/*.toml`.
- TOML keys:
  - `title` is the window title; the font name is appended.
  - `overlay = "crt"` is a CSS layer in the browser, never in the tiles, so scanlines stay sharp under Leaflet zoom.
    - It draws scanlines and a vignette whose centre glows in the marker colour (`--glow`).
    - It goes into config. `template.html` adds `ov-crt` to `#map` (`::after`, z 650: above tiles and marker, below controls). `streifen.html` creates one fixed `.ov-crt` div per strip, clipped in `clip()` in viewport coordinates.
    - The CSS exists twice (`template.html`, `src/streifen.css`); keep both in sync.
  - `site_font` overrides the font `--site` renders for this style (all families have one since 2026-11-23, first version of the user's per-style font choice; Catppuccin keeps the nerd default Maple Mono). New site fonts must be added to the Über dialog's font list in `streifen.html`.
  - `category`, `mode` and `family` drive the preview pages. `order` (default 50; higher = further right, then alphabetical) sorts the strips. Both cyberpunk styles use 99, so they sit in the rightmost column, as the user asked.
  - `preview_font` is the only font `--all` renders, unless `--all-fonts` is given: Fira Sans for standard styles and Maple Mono for nerd styles, at the user's request, to keep preview renders fast.
  - `font` is the default font. It replaces "Noto Sans" in every `text-font`, and Noto stays in the stack as fallback.
  - `fonts` lists the font groups that `--all --all-fonts` renders. The default is `["sans", "serif"]`; the editor themes add `"mono"`. A single run with `--font`, or `--all --font X`, ignores the groups.
  - `language` (default `de`): `build_style()` swaps OSM Bright's `["get", "name_en"]` in every `text-field` for `name:<language>`, so the label falls back to the local `name`. Upstream prefers English, which showed "Federal Chancellery" etc. in the old Berlin preview.
  - `text_scale` scales `text-size`, except the `*shield*` layers.
  - `hide` is a list of layer-id globs to hide.
  - `[paint."glob"]` / `[layout."glob"]` set properties on matching layer ids. They apply in file order, so the last match wins. Only properties whose prefix fits the layer type are applied, which makes broad globs like `water*` safe.
- Marker: the `[marker]` table in a style is written into the config as `marker` (+ `label` from `--label`, default "hier").
  - `template.html`'s `markerIcon()` draws `type = "terminal"` as an `L.divIcon` (box `~/<label>` + static block cursor, no blinking (user request), + stem + dot, anchored on the dot). `type = "bubble"` (all standard styles) is a speech bubble modelled on Heroicons "chat-bubble-bottom-center": rounded box with the label, plus a centred SVG tail at the bottom whose tip is the anchor. Its colours `color`/`bg`/`fg` follow the style's accent and mode. Anything else falls back to `L.Icon.Default`.
  - The label is set via `textContent`, never as HTML.
  - `streifen.html` carries a copy of `markerIcon()` and its CSS, and uses the middle strip's marker. Keep both copies in sync.
- `--reindex` rewrites every `out/*/index.html` from `template.html` and the current style metadata (category, mode, family, attribution, marker) without rendering. Use it after template or marker changes.
- Nerd styles show green areas (`park`, `landcover-*`, `landuse-cemetery`, `landcover-wood`) in the theme's signature colour instead of green (Tokyo Night magenta2 pink, Dracula/Alucard purple, Catppuccin Latte peach, Nightfox/Dayfox cyan, Solarized yellow, Gruvbox orange; One: wood purple, grass green, see one-dark below), mixed with the background: dark 20 % (wood 28 %), light 25 % (wood 35 %). This was a user request; Tokyo Night uses `magenta2`. Exceptions: Everforest stays green (Everforest green is its signature colour). catppuccin-mocha uses Catppuccin green `#a6e3a1` (18 %, wood 26 %) as part of its pastel character; in solarized-dark the RGB mix with the teal base turned green, so it uses an OKLCH dark gold (#4b3b13), mixed again 45 % (wood 60 %) with base03 so the petrol ground dominates.
- Dark nerd styles each have their own character (user request, because they all looked alike); every colour is still a palette colour or a mix of two. Each file says its character in the comment above `[paint."background"]`.
  - Neon glow (blurred casing in the accent colour) only on `dracula`, `tokyonight-night` and `cyberpunk`.
  - `catppuccin-mocha`: pastel, no glow, surfaces stepped crust < mantle < base < surface, roads lavender/mauve/peach, water sapphire.
  - `solarized-dark`: flat, no glow, roads only in base tones, yellow/orange just for trunk/primary and motorway.
  - `nightfox`: muted navy, no glow, water deep blue, orange motorway the only warm accent.
  - `dracula`: colourful: secondary/tertiary orange, paths green, minor roads comment, water cyan 55 %.
  - `gruvbox-dark`: warm retro, no glow, brown-grey bg steps, roads bg3/fg4, yellow primary, orange motorway, muted blue water.
  - `one-dark`/`one-light` ("rainbow", user request): road hierarchy runs through the 7 syntax colours, motorway red > trunk orange > primary yellow > secondary/tertiary green > minor cyan > service/track blue (a `match` on `class`, because OSM Bright's `highway-minor` holds minor+service+track) > path violet; the lower three are mixed with the background. No glow. Buildings (45 %) and residential/commercial/industrial landuse (22 %) get one of the 7 colours by OSM id (`["%", ["floor", ["/", ["id"], 10]], 7]`; the last id digit is the OSM type). Feature ids exist in our Planetiler mbtiles; at z12 merged landuse looks mostly one colour, so the rainbow shows from z13 (buildings). Grass/park/cemetery green, wood violet, water blue.
  - `everforest-dark`: soft and low-contrast, no glow, green-grey ground, grey/cream roads, yellow primary, orange only motorway.
  - `tokyonight-night`: blue neon for trunk/primary, magenta2 motorway, water blue0.
  - Road ref and major-name labels use the same colours as their road lines.
- Nerd styles colour place and POI labels (`*label*`, `label_*`, `poi_*`, `airport`) in their marker `color` (user request, like cyberpunk's cyan). Where needed it is mixed with the marker `fg` until contrast ≥ 3.5:1 (large text). POIs: dark styles mix 22 % toward the background, light styles 35 % toward `fg`. Each block is marked with a comment.
- Standard styles (clear, cupertino, north, osm, papier, each light/dark; protomaps-dark): place labels stay dark/light but are tinted in the background's OKLCH hue (marker hue if the background is grey; papier already sepia, protomaps-dark only brightened). POIs use the marker `color`, mixed with the label colour until contrast ≥ 4.5:1. Americana, Protomaps light and Wiki keep their upstream POI colours.
- Nerd styles end with a `# >>> Akzent-Beschriftung … # <<<` block. It hides the white shield sprite (`icon-image = ""`, because sprite PNGs cannot be recoloured) and colours road refs by class with a `match` expression: motorway / trunk+primary / rest, using the theme's accent colours. Major road names get the primary accent too. Keep the block at the end of the file so it wins.
- POI layers: a low `rank` means important, so `poi_r1` holds the most important places and `poi_r20` the least. Hide `poi_r20`, not `poi_r1`.
- Styles and their user-chosen names:
  - **Standard:**
    - `clear` (own design, default).
    - `cupertino`: borrows only the overall look of Apple Maps. Own colours, no Apple assets, and no "Apple" in the public attribution.
    - `north`: Hydda palette.
    - `osm-light`: a lighter, decluttered osm.org standard map.
    - `papier`: own design, printed-map look (cream, sepia casings, olive green, Literata); `papier-dark` = dark sepia card.
    - `americana`: OSM Americana colours (CC0): white roads with dark casings, red trunk casing and motorway. `americana-dark` is our own derivation (upstream has no dark flavour).
    - `protomaps-light`/`-dark`: Protomaps Basemaps flavours (design CC0).
    - `wiki`: Wikimedia Maps colours from wikimedia/osm-bright.tm2. The design is CC BY 3.0, so this attribution must stay, in `wiki-dark` too.
  - **Standard dark:** `clear-dark`, `cupertino-dark`, `north-dark`, `osm-dark`, `wiki-dark`, `americana-dark`, `papier-dark`, `protomaps-dark`.
  - **Nerd, own design:** `phosphor` (green P1 CRT: 8 green steps on near-black, glow on major roads and place labels) and `bernstein` (amber P3 CRT, same steps mapped to amber; it plays the "light" role in family "Phosphor" although the image is dark). The user first had a continuous-paper printout as the light variant, then replaced it with amber. Both use VT323 (`site_font` makes the public preview render them in VT323 instead of the category font; `streifen.html` then falls back to a family's own font). Order 98. User request 2026-11-23.
  - **Nerd, own design:** `bluecron` / `bluecron-tag` (working title "Bluecron", user request 2026-11-23; grew out of a "Moos, Nebel, Flieder, Ozean, Sternenhimmel" draft the user found too close to Dracula, then asked for Tron): near-black ground, buildings as wireframe (dark glass, muted cyan edge, toned down at the user's request), primary/trunk white-hot core with cyan glow, orange motorway as the only counter colour, terminal marker, Mozilla Text. Order 97. Must stay distinct from Neon Cyberpunk (no pink/violet). A graticule was tried and removed by the user.
  - **Nerd, not editor themes:** `cyberpunk` ("Neon Cyberpunk", colours 1:1 from maptoposter `neon_cyberpunk.json`, MIT, neon glow on roads) and `cyberpunk-day` (own light counterpart, "Warnfarben", user request 2026-11-23: neon needs a dark ground, so the light variant works through saturation and hard contrast: hazard-yellow ground, cream buildings, pink green areas, cyan water, cyan trunk/primary, pink motorway, white minor roads, black ink casings, no glow; terminal marker black on yellow). cosmicsarthak-neon-theme was checked as inspiration and rejected: its light themes are Solarized Light, and its licence file is missing.
  - **Nerd** (editor-theme palettes): `dayfox`/`nightfox`, `catppuccin-latte`/`-mocha`, `dracula-light` ("Alucard", the official Dracula light palette) / `dracula`, `solarized-light`/`-dark`, `gruvbox-light`/`-dark`, `everforest-light`/`-dark`, `one-light`/`-dark` (Atom One) (all MIT), and `tokyonight-day`/`-night` (Apache-2.0).
- For the recreations, only colour values were taken from the originals, never their style files. That is what the user asked for, to avoid licence problems, and each recreation names its inspiration in `attribution`.
- Dark and editor-theme styles share one role mapping: bg, landuse, buildings, water, green, three road tiers, text.
  - The `*-dark` standard styles were derived in OKLCH, not by inversion (inversion makes white roads darker than the ground). The light background's hue becomes a dark neutral ramp, and accents are relit.
  - Dark styles need the `highway-area` and `aeroway-*` overrides, otherwise OSM Bright's light grey pedestrian areas glare. They also need lighter minor roads to stand out from buildings.
  - The generator scripts were one-offs and are not in the repo. The TOMLs are now the source of truth; edit them by hand.

## 8-bit mode

- `--pixel [4|2]` (user request 2026-11-23, reworked 2026-11-24 after the user sent Sierra/synthwave pixel-art references: the Bayer version "funktioniert nicht", wanted the character of 8-bit art; user chose 4× + outlines). Default 4: for each tile `render()` fetches the z-2 ancestor (`parent()`, an lru_cache cleared per render, because the URL on port 8089 is the same for every style) and `lowres()` crops its 64 px piece (`--pixel 2`: z-1, 128 px). pngquant is not used.
- Labels are rendered separately (user request 2026-11-24): `split_labels()` makes a map style without symbol layers and a labels-only style (transparent ground); `render()` runs two tileservers one after the other, the second writes `<tile>.labels.png`. Placement stays the same, MapLibre only collides labels with labels. Both ancestors are fetched `@{PIXEL_SS}x` (3) for supersampling: each 8-bit pixel is decided from 3×3 image pixels.
- Second pass `dither_tiles()` (needs numpy, Pillow, scipy, imported lazily; name kept, no dithering any more):
  - Map: one 16-colour palette per style from `pixel_palette()` (style hex colours from `style_colors()` weighted by nearest pixels, farthest-point × log(weight)). Per block the most common palette colour: glows and anti-aliasing become hard bands. Lone pixels (all four neighbours equal and different) take the neighbour colour. Outlines (Sierra-like): a pixel of an "area" colour (> 3 % of all pixels) next to a pixel brighter by `OUTLINE_STEP` becomes the darkest palette colour. Textures: water (`water*` fill) wave dashes, `park` dots, only if the fill has its own slot (not 0 = background; in Bluecron water and ground share one and the waves covered everything).
  - Labels: own palette of `LABEL_COLORS` (8) with every `text-color` forced in, appended to the map palette (indexed PNG, up to 24 colours). `snap_labels()`: MapLibre places labels at sub-pixel positions and SDF strokes are ~2.5 of 3 image pixels, so a stroke on a block border vanished ("WESTFALENDAMM" lost its crossbars); per connected label (scipy `ndimage.label`) the shift 0–2 px with the most decisive blocks is chosen. A block becomes text at ≥ 4/9 text pixels, else halo/icon at ≥ 4/9 opaque, else map. Labels are baked into the tile.
  - Nearest upscale ×f (@2x ×2f); oxipng afterwards.
  - Earlier versions (Bayer 4×4 dithering, text detected by palette colour) were replaced: text with a road's colour (Dracula) or missing from the palette (Bluecron shield "B 66") fell apart.
- Map geometry for the coarse grid (user 2026-11-24: road connections got lost, then "große Straßen zu fett", black specks in Cyberpunk Day): `build_style()` with pixel runs `zoom_shift()` over every paint/layout value except `text-size` and lowers layer min/maxzoom by log2(pixel), so the ancestor looks like the target zoom (OSM Bright minor road fill has width 0 below z13.5). Line widths go through `scale_out()`: to scale (÷ pixel) but at least `PIXEL_MIN_LINE` (1.7 grid px); doubling everything made big roads too fat. Plain `*-casing` lines are hidden (half a pixel wide they broke into dots); the outline pass draws the edge. Glow casings (`line-blur`) stay. Outlines only next to bright spots of at least two pixels. An earlier extra vote weight for rare colours caused speckles and was removed.
- Pixel fonts have `grid` in `fonts.toml` (em px at 1 font pixel = 1 image pixel: VT323 12.5, Press Start 2P/Silkscreen 8). `on_grid()` snaps `text-size` to multiples; with `--pixel 4` every label is exactly one grid step and symbol `minzoom` is lowered by 2 (else z14 rendering shows no street names, and labels snapped to 16 px came out 64 css px tall). Halo blur 0, halo `PIXEL_HALO * 2 // pixel`, line-placed labels horizontal (viewport alignment).
- Fonts: group `pixel`. Default Silkscreen for 4, VT323 for 2 (`a.font` in `main()`); Press Start 2P kept as an option. Rejected earlier: Pixelify Sans, Jersey 10, Micro 5, DotGothic16. The pixel group gets bold POI strokes.
- `config.json` carries `pixel`, and `template.html` then sets `image-rendering: pixelated` on the tiles.
- 8-bit marker (user chose "Terminal wie bisher, gepixelt" 2026-11-24): `markerIcon(m, px)` adds class `px` and `--u` = pixel size; `.term.px` CSS (in `template.html` and `src/streifen.css`, keep in sync) draws everything in multiples of `--u`, Silkscreen at 8u, no radius, hard shadow. `snapMarker()` shifts the icon so its pixels sit on the tile pixel grid (grid = pixel × 2^(zoom − native max)). `silkscreen.ttf` is copied next to each standalone pixel page (`render()`) and into every preview folder (`write_previews()`, constant `SILKSCREEN`).
- Public preview: `site.toml` `pixel = ["nerd"]` makes `build_site()` render each nerd style again with `--pixel 4` in Silkscreen (`site/<style>-silkscreen-8bit`). `streifen.html` shows an "8 Bit" button (`?px=1`) only for categories that have pixel variants, and `inSet()` keeps them apart from the normal variants. The Über dialog lists Silkscreen.
- Streets-only on the public preview: `site.toml` `streets = [...]` makes `build_site()` render each style of those categories again with `--streets-only` in its first site font (`site/<style>-<font>-streets`). `streifen.html` shows a "Straßen" button (`?st=1`) for categories that have them; it and "8 Bit" exclude each other (no 8-bit streets variant), and `inSet()` keeps them apart via `config.streets`.

## Streets only

- `--streets-only` (user request 2026-11-23, inspired by maptoposter): `build_style()` hides every layer not in `STREETS_KEEP` (background, water, waterways, `highway-*`/`bridge-*`/`tunnel-*`, `label_*`), and `STREETS_DROP` wins (road names, shields, `highway-area`, railways). Applied after the TOML overrides, so it works with every style. `config.json` carries `streets`. Not in `--site` yet.
- Planned next steps, only if the user likes the look: rendering z14 data shown downscaled for a whole-city view (OMT drops minor roads below z13, which couples to `tiles_for()`/`template.html`), no casings, and a poster overlay (gradient + city name) like `overlay = "crt"`.

## Graticule (parked)

- `graticule = true` in a style TOML adds a lat/lon grid baked into the tiles (`graticule()`, `GRID`): dashed lines in the marker accent below all labels, plus decimal degree labels (`52.016°N`) along the lines with the lowest priority.
- Spacing goes per Leaflet zoom from 0.1° down to 0.001°. Styles use z-1, because tileserver-gl draws 256 px tiles one zoom lower.
- No style enables it yet: the user parked the idea on 2026-11-23 after a Dracula preview. A coordinate readout in `template.html` was dropped for now.

## Fonts

- Only the sources plus licences (`fonts-src/<font>/`) are in git. `style/fonts/` is gitignored and built by `ensure_glyphs()` from the face specs in `style/fonts.toml`.
- `style/fonts.toml`: each table is one font (one variant per style under `--all --all-fonts`).
  - Faces are `Regular`/`Bold`/`Italic` = `{ file, <axis> = value }`. Faces with axes are cut from variable fonts with `fontTools.varLib.instancer`; the rest are copied.
  - Optional keys: `group` (sans|serif|mono), `scale` (multiplies `text_scale`), and `streets` (a face suffix used for the `highway-name*` layers).
- The temp file is named `<Font> <Face>.ttf`, because `build_pbf_glyphs` names output folders after the file stem.
- Only missing folders are rebuilt, so delete a folder after changing its spec.
- Noto Sans is deliberately absent from `fonts.toml`: it is fallback only, because the user dislikes it as a label font.
- `brotli` is not installed, so take new fonts as TTF/OTF from upstream (google/fonts, CTAN), not WOFF2.
- google/fonts can lack styles the foundry ships (Mozilla Text there has no italic; mozilla/mozilla-type-family does). Before calling a font italic-less, check the foundry repo and the user's catalogue `elbym/font-collection`.
