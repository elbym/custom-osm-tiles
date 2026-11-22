# tiles

Statische Kacheln (WebP) für Leaflet, nur für einen kleinen Bereich um einen Marker, selbst gehostet.

```sh
./make-tiles.py   # Standard: styles/clear.toml, Bielefeld, 5 km, z10-18 -> out/clear
./make-tiles.py --lat 52.115 --lon 8.67 --style styles/north.toml --out out/kunde-xy
# ab z17 nur 1 km um den Marker: --detail-from 17 --detail-radius 1
# optional: --retina (@2x), --area <geofabrik-name>, --viewport 2560x1440 (größte Kartengröße, damit niedrige Zoomstufen sie füllen)
```

Ergebnis in `out/<name>/` (`tiles/`, `leaflet/`, `index.html`): einfach neben die Website hochladen.

## Stile

Jeder Stil ist eine kurze Textdatei in `styles/`. Das Skript baut daraus zusammen mit der Grundlage `style/base.json` (OSM Bright) den fertigen Stil.

```toml
title = "North"              # Fenstertitel, die Schrift wird angehängt
font = "Overpass"            # Standardschrift, siehe Abschnitt Schriften
text_scale = 1.15            # Faktor für alle Beschriftungen
attribution = "Stil inspiriert von …"
hide = ["poi_*"]             # Ebenen ausblenden

[paint."*-motorway*"]        # Ebenen per Namensmuster, später stehende gewinnen
line-color = "#e892a2"
```

Die Ebenennamen stehen in `style/base.json`. Pro Ebene werden nur passende Eigenschaften gesetzt (`fill-*` auf Flächen, `line-*` auf Linien, `text-*`/`icon-*` auf Beschriftungen).

| Datei | Vorbild |
|---|---|
| `clear.toml` | **Clear**: eigener Stil, kühl und reduziert, Farbe nur für Hauptstraßen (Standard) |
| `cupertino.toml` | **Cupertino**: angelehnt an den Gesamteindruck von Apple Maps (eigene Farbwahl) |
| `north.toml` | **North**: Farben nach der Palette von Hydda (BSD-3) |
| `osm-light.toml` | **OSM light**: OSM-Standardkarte (Mapnik/openstreetmap-carto, CC0), aufgehellt und aufgeräumt |
| `wiki.toml` | **Wiki**: Wikimedia Maps („osm-intl“, Farben aus github.com/wikimedia/osm-bright.tm2; Design CC BY 3.0, Namensnennung im Stil) |
| `clear-dark.toml`, `cupertino-dark.toml`, `north-dark.toml`, `osm-dark.toml`, `wiki-dark.toml` | dunkle Varianten der fünf Stile oben (automatisch abgeleitet, siehe unten) |
| `dayfox.toml`, `nightfox.toml` | **Dayfox** / **Nightfox**: Farben des Editor-Themes Nightfox (MIT), hell / dunkel |
| `catppuccin-latte.toml`, `catppuccin-mocha.toml` | **Catppuccin Latte** / **Mocha**: Farben von Catppuccin (MIT), hell / dunkel |
| `dracula.toml` | **Dracula**: Farben des Dracula-Themes (MIT), dunkel |
| `solarized-light.toml`, `solarized-dark.toml` | **Solarized Light** / **Dark**: Farben von Solarized (MIT) |
| `tokyonight-day.toml`, `tokyonight-night.toml` | **Tokyo Night Day** / **Tokyo Night**: Farben von tokyonight.nvim (Apache-2.0) |

Die dunklen Varianten sind nicht invertiert (dann würden weiße Straßen dunkler als der Grund), sondern über Kartenrollen abgeleitet: Aus dem Farbton des hellen Grunds entsteht eine dunkle Graustufenleiter mit demselben Charakter (Clear kühl, Wiki warm), Wasser, Grün und Straßenfarben behalten Farbton und Sättigung und werden nur in der Helligkeit angepasst (OKLCH). Die Dateien sind danach normale Stil-Dateien und können von Hand nachjustiert werden.

Die Editor-Theme-Stile ordnen jeder Palette dieselben Kartenrollen zu (Grund, Gebäude, Wasser, Grün, drei Straßenstufen, Schrift) und werden mit `fonts = ["sans", "serif", "mono"]` zusätzlich mit Monoschriften gerendert.

Die Stile sind eigene Umsetzungen. Von den Vorbildern sind nur Farbwerte übernommen, keine Stildateien. Beim Stil Wiki verlangt die Lizenz (CC BY 3.0) eine Namensnennung; sie steht in `attribution` und erscheint auf der Karte.

## Varianten vergleichen

```sh
./make-tiles.py --all --zoom 16-16 --radius 1.5 --retina   # jeder Stil × jede Schrift -> out/<stil>-<schrift>
./make-tiles.py --all --style styles/clear.toml ...          # nur ein Stil, alle Schriften
./make-tiles.py --all --missing ...                         # nur noch nicht gerenderte Varianten
```

`--all` kombiniert jeden Stil in `styles/` mit jeder Schrift in `style/fonts/`. Eine neue Schrift oder ein neuer Stil ergibt also automatisch alle Kombinationen. `out/compare.html` zeigt vier davon im 2×2-Raster mit synchronem Ausschnitt; jedes Fenster hat eine eigene Auswahl.

Beide Vorschauseiten haben oben zwei Schalter: **Standard | Nerd** (Gruppe) und **Hell | Dunkel** (Modus). Dafür trägt jeder Stil in seiner Datei `category` (standard/nerd), `mode` (light/dark) und `family`. Stile derselben Familie sind Gegenstücke: Beim Umschalten wird aus Clear „Clear Dark“, aus Catppuccin Latte „Mocha“. Hat eine Familie einen Modus nicht (Dracula gibt es nur dunkel), bleibt ihr Streifen leer und ist beschriftet.

`out/streifen.html` zeigt eine einzige durchgehende Karte, senkrecht in einen Streifen pro Stil geteilt. Alle Streifen nutzen dieselbe Schrift (Auswahl links oben, steht in der URL als `?font=…`). So sieht man, wie dieselben Straßen in jedem Stil wirken.

## Ablauf

1. **Planetiler** (Podman) baut aus dem Geofabrik-Extrakt `--area` einmalig `data/<area>.mbtiles` (OpenMapTiles-Schema). Zum Aktualisieren die Datei löschen.
2. **tileserver-gl** (Podman) rendert den Stil zu WebP. Das Skript fragt nur die nötigen Kacheln ab.
3. Der Container wird danach gestoppt. Im Ergebnis gibt es keine Anfragen an Dritte, auch Leaflet liegt lokal.

Der Bereich muss innerhalb von `--area` liegen (Namen siehe https://download.geofabrik.de).

## Schriften

Im Git liegen nur die Schriftquellen samt Lizenz (`fonts-src/<schrift>/`). Die Glyphen, die die Karte braucht, erzeugt `make-tiles.py` beim ersten Lauf nach `style/fonts/`. Dafür nötig:

```sh
pip install -r requirements.txt        # fontTools
cargo install build_pbf_glyphs         # Rust-Programm, nicht über pip
```

Welche Schnitte aus welcher Datei entstehen, steht in `style/fonts.toml`. Jede Tabelle dort ist eine Schrift und damit eine Variante bei `--all`:

```toml
[Literata]
Regular = { file = "literata/Literata-VF.ttf", wght = 400, opsz = 12 }
Bold    = { file = "literata/Literata-VF.ttf", wght = 700, opsz = 12 }
Italic  = { file = "literata/Literata-Italic-VF.ttf", wght = 400, opsz = 12 }
group   = "serif"  # sans | serif | mono; ein Stil wählt mit fonts = [...] die Gruppen für --all
scale   = 1.05     # optional: Größenfaktor
streets = "450"    # optional: eigener Schnitt für Straßennamen (muss oben als Schnitt stehen)
```

Ohne Achsenwerte wird die Datei unverändert übernommen. Mit Achsenwerten wird aus der variablen Schrift ein fester Schnitt erzeugt. Neue Schrift: Dateien nach `fonts-src/<schrift>/` legen, Tabelle in `fonts.toml` ergänzen, fertig. Nach einer Änderung an einem bestehenden Schnitt dessen Ordner in `style/fonts/` löschen, damit er neu erzeugt wird.

| Schrift | Art | Lizenz |
|---|---|---|
| Fira Sans, Inter, Overpass, Public Sans | serifenlos | OFL |
| Literata | Serifen | OFL |
| TeX Gyre Schola | Serifen | GUST Font License |
| Fira Code, JetBrains Mono, Maple Mono, Victor Mono | Mono (nur für Stile mit `fonts = [..., "mono"]`) | OFL |

Noto Sans ist keine eigene Variante, sondern nur Ersatz für Zeichen, die einer Schrift fehlen (z. B. Kyrillisch). `make-tiles.py` lädt sie beim ersten Lauf fertig herunter. Mit `--font "<Name>"` lässt sich eine einzelne Schrift rendern, zusammen mit `--all` in allen Stilen.

Namensnennung: © OpenStreetMap-Mitwirkende (ODbL), © OpenMapTiles, dazu das `attribution` des Stils.
