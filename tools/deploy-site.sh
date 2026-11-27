#!/bin/sh
# Öffentliche Vorschau bauen und als Branch gh-pages veröffentlichen (GitHub Pages).
#   tools/deploy-site.sh            site/ ergänzen (--missing) und veröffentlichen
#   tools/deploy-site.sh --no-build nur das vorhandene site/ veröffentlichen
# gh-pages wird jedes Mal durch einen einzigen Commit ersetzt (Force-Push), damit sich keine alten Kacheln ansammeln.
# Läuft niedrig priorisiert (nice/ionice), damit Webserver und Datenbank auf dem Server (ionos) flüssig bleiben.
set -eu
cd "$(dirname "$0")/.."

[ "${1:-}" = "--no-build" ] || nice -n 10 ionice -c 2 -n 7 ./make-tiles.py --site --missing

remote=$(git remote get-url origin)
# Git-Verzeichnis auf der Platte (data/ ist gitignored), nicht in /tmp: das ist auf ionos ein tmpfs im RAM (1,9 GB),
# und site/ ist 350–700 MB groß
tmp=$(mktemp -d -p data deploy.XXXXXX)
trap 'rm -rf "$tmp"' EXIT
g() { nice -n 10 git --git-dir="$tmp" --work-tree=site "$@"; }
g init -q -b gh-pages
# Kacheln sind schon komprimierte PNGs: zlib und Delta-Suche kosten nur Zeit (gemessen 701 MB site/, 8 Kerne:
# add+commit 38 -> 14 s, Packen 57 -> 7 s, Pack 647 -> 652 MB)
g config core.compression 0
g config pack.window 0
g config gc.auto 0   # sonst packt ein Hintergrund-gc die >6700 losen Objekte noch einmal, während der trap löscht
g add -A
g commit -qm "Vorschau $(date +%F)"
g push -f "$remote" gh-pages
echo "veröffentlicht; GitHub Pages baut in ein paar Minuten neu: https://elbym.github.io/custom-osm-tiles/"
