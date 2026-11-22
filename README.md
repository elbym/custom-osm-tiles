# tiles

Statische Kacheln (WebP) für Leaflet, nur für einen kleinen Bereich um einen Marker, selbst gehostet.

```sh
./make-tiles.py   # Standard: styles/klar.toml, Bielefeld, 5 km, z10-18 -> out/klar
./make-tiles.py --lat 52.115 --lon 8.67 --style styles/hydda.toml --out out/kunde-xy
# ab z17 nur 1 km um den Marker: --detail-from 17 --detail-radius 1
# optional: --retina (@2x), --area <geofabrik-name>, --viewport 2560x1440 (größte Kartengröße, damit niedrige Zoomstufen sie füllen)
```

Ergebnis in `out/<name>/` (`tiles/`, `leaflet/`, `index.html`): einfach neben die Website hochladen.

## Stile

Jeder Stil ist eine kurze Textdatei in `styles/`. Das Skript baut daraus zusammen mit der Grundlage `style/base.json` (OSM Bright) den fertigen Stil.

```toml
title = "Hydda (nachempfunden)"  # Fenstertitel, die Schrift wird angehängt
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
| `klar.toml` | eigener Stil: kühl und reduziert, Farbe nur für Hauptstraßen (Standard) |
| `apple.toml` | angelehnt an den Gesamteindruck von Apple Maps (eigene Farbwahl) |
| `hydda.toml` | Farben nach der Palette von Hydda (BSD-3) |
| `osm-openmaptiles.toml` | inspiriert von OSM OpenMapTiles, Farben nach openstreetmap-carto (CC0) |
| `osm-leicht.toml` | OSM-Standardkarte (Mapnik/openstreetmap-carto, CC0), aufgehellt und aufgeräumt |
| `wikimedia.toml` | Wikimedia Maps („osm-intl“, Farben aus github.com/wikimedia/osm-bright.tm2; Design CC BY 3.0, Namensnennung im Stil) |

Die Stile sind eigene Umsetzungen. Von den Vorbildern sind nur Farbwerte übernommen, keine Stildateien. Beim Wikimedia-Stil verlangt die Lizenz (CC BY 3.0) eine Namensnennung; sie steht in `attribution` und erscheint auf der Karte.

## Varianten vergleichen

```sh
./make-tiles.py --all --zoom 16-16 --radius 1.5 --retina   # jeder Stil × jede Schrift -> out/<stil>-<schrift>
./make-tiles.py --all --style styles/klar.toml ...          # nur ein Stil, alle Schriften
```

`--all` kombiniert jeden Stil in `styles/` mit jeder Schrift in `style/fonts/`. Eine neue Schrift oder ein neuer Stil ergibt also automatisch alle Kombinationen. `out/compare.html` zeigt vier davon im 2×2-Raster mit synchronem Ausschnitt; jedes Fenster hat eine eigene Auswahl.

`out/streifen.html` zeigt eine einzige durchgehende Karte, senkrecht in einen Streifen pro Stil geteilt. Alle Streifen nutzen dieselbe Schrift (Auswahl links oben, steht in der URL als `?font=…`). So sieht man, wie dieselben Straßen in jedem Stil wirken.

## Ablauf

1. **Planetiler** (Podman) baut aus dem Geofabrik-Extrakt `--area` einmalig `data/<area>.mbtiles` (OpenMapTiles-Schema). Zum Aktualisieren die Datei löschen.
2. **tileserver-gl** (Podman) rendert den Stil zu WebP. Das Skript fragt nur die nötigen Kacheln ab.
3. Der Container wird danach gestoppt. Im Ergebnis gibt es keine Anfragen an Dritte, auch Leaflet liegt lokal.

Der Bereich muss innerhalb von `--area` liegen (Namen siehe https://download.geofabrik.de).

## Schriften

Die Schriften liegen als Glyphen in `style/fonts/`, die Quellen samt Lizenz in `fonts-src/<schrift>/`. Noto Sans ist keine eigene Variante, sondern nur Ersatz für Zeichen, die einer Schrift fehlen (z. B. Kyrillisch). Sie ist nicht im Git, `make-tiles.py` lädt sie beim ersten Lauf.

| Schrift | Art | Lizenz |
|---|---|---|
| Atkinson Hyperlegible Next, Fira Sans, Inter, Overpass, Public Sans | serifenlos | OFL |
| Literata, Newsreader | Serifen | OFL |
| TeX Gyre Schola | Serifen | GUST Font License |

Liegt eine Schrift nur als variable Datei vor (Atkinson Hyperlegible Next, Literata, Public Sans, Newsreader), werden die Schnitte daraus erzeugt: Regular = Gewicht 400, Bold = 700. Literata und Newsreader haben zusätzlich eine Achse für die optische Größe; dafür gilt 12, passend zur Größe der Beschriftungen.

`style/fonts.toml` enthält Einstellungen pro Schrift: `scale` gleicht unterschiedlich große Schriftbilder aus, `streets` wählt einen eigenen Schnitt für Straßennamen (zum Beispiel Gewicht 450). Einen solchen Schnitt erzeugt man aus der variablen Schrift:

```sh
python3 -m fontTools.varLib.instancer fonts-src/public-sans/PublicSans-VF.ttf wght=450 -o "/tmp/w/Public Sans 450.ttf"
build_pbf_glyphs /tmp/w /tmp/g && mv "/tmp/g/Public Sans 450" style/fonts/
```
 Mit `--font "<Name>"` lässt sich eine einzelne Schrift rendern, zusammen mit `--all` in allen Stilen.

Neue Schrift einbauen: TTF oder OTF nach `fonts-src/<schrift>/` legen, dann `build_pbf_glyphs fonts-src/<schrift> style/fonts` ausführen. Die Ordner danach in `<Name> Regular|Bold|Italic` umbenennen.

Namensnennung: © OpenStreetMap-Mitwirkende (ODbL), © OpenMapTiles, dazu das `attribution` des Stils.
