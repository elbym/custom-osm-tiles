# tiles

Statische Rasterkacheln für Leaflet, nur für einen kleinen Bereich um einen Marker, selbst gehostet.

```sh
./make-tiles.py   # Standard: Bielefeld, 5 km, z10-18 -> out/test
./make-tiles.py --lat 52.115 --lon 8.67 --radius 5 --zoom 10-18 --out out/kunde-xy
# ab z17 nur 1 km um den Marker: --detail-from 17 --detail-radius 1
# optional: --retina (@2x), --area <geofabrik-name>, --viewport 2560x1440 (größte Kartengröße, damit niedrige Zoomstufen sie füllen)
```

Ergebnis in `out/kunde-xy/` (`tiles/`, `leaflet/`, `index.html`): einfach neben die Website hochladen.

## Ablauf

1. **Planetiler** (Podman) baut aus dem Geofabrik-Extrakt `--area` einmalig `data/<area>.mbtiles` (OpenMapTiles-Schema). Zum Aktualisieren die Datei löschen.
2. **tileserver-gl** (Podman) rendert `style/style.json` zu PNG. Das Skript fragt nur die nötigen Kacheln ab.
3. Der Container wird danach gestoppt. Im Ergebnis gibt es keine Anfragen an Dritte, auch Leaflet liegt lokal.

Der Bereich muss innerhalb von `--area` liegen (Namen siehe https://download.geofabrik.de).

## Stil

`style/style.json` ist **OSM Bright** (OpenMapTiles/OpenFreeMap). Davon stammt auch Wikimedias „osm-intl“ ab. Farben direkt dort anpassen. Schriften: DINish (OFL, github.com/playbeing/dinish, Quelle in `fonts-src/`), Noto Sans als Ersatz für fehlende Zeichen (nicht im Git, `make-tiles.py` lädt ihn beim ersten Lauf). Neue Schrift: TTF nach `fonts-src/`, `build_pbf_glyphs fonts-src style/fonts`, Ordner wie in `style.json` benennen. Sprites: OpenFreeMap.

Namensnennung: © OpenStreetMap-Mitwirkende (ODbL), © OpenMapTiles.
