#!/bin/sh
# Öffentliche Vorschau bauen und als Branch gh-pages veröffentlichen (GitHub Pages).
#   tools/deploy-site.sh            site/ ergänzen (--missing) und veröffentlichen
#   tools/deploy-site.sh --no-build nur das vorhandene site/ veröffentlichen
# gh-pages wird jedes Mal durch einen einzigen Commit ersetzt (Force-Push), damit sich keine alten Kacheln ansammeln.
set -eu
cd "$(dirname "$0")/.."

[ "${1:-}" = "--no-build" ] || ./make-tiles.py --site --missing

remote=$(git remote get-url origin)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
# eigenes Git-Verzeichnis außerhalb von site/, das Projekt-Repo bleibt unberührt
git --git-dir="$tmp" --work-tree=site init -q -b gh-pages
git --git-dir="$tmp" --work-tree=site add -A
git --git-dir="$tmp" --work-tree=site commit -qm "Vorschau $(date +%F)"
git --git-dir="$tmp" --work-tree=site push -f "$remote" gh-pages
echo "veröffentlicht; GitHub Pages baut in ein paar Minuten neu: https://elbym.github.io/custom-osm-tiles/"
