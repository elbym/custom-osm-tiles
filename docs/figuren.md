# Figuren auf den Karten

Einige Stile zeigen kleine Figuren auf der Karte: Anime, Island und die historischen Stile. Dieses Dokument hält fest, wie sie aussehen sollen, was verboten ist und wie man neue Figuren ergänzt.

## Auf einen Blick

| Stil | Figuren | Look | Nachts |
|---|---|---|---|
| **Anime** / Anime Nacht | 48 (28 Menschen, 20 Tiere, Wesen, Essen) | Chibi im Anime-Stil, Tuschekontur, weißer Sticker-Rand | alle schlafen, Menschen auf dem Futon |
| **Island** / Nordlicht | 18 (Tiere, Sagenwesen, Badende) | skandinavische Bilderbuch-Volkskunst, flach, ohne Schraffur | alle schlafen, Menschen unter der Wolldecke |
| **Historisch** / Gaslicht, **Kupferstich** / Kupferplatte | 16 Fabelwesen | kolorierter Holzschnitt (Gessner, 16. Jh.) | Gaslicht: wach, nur umgefärbt |

## Grundregeln für alle Stile

1. **Nur eigene Zeichnungen.** Jede Figur ist neu gezeichnet. Keine Vorlagen aus Filmen, Spielen, Serien oder Büchern, keine fremden Grafiken.
2. **Keine erkennbaren Figuren.** Erlaubt sind Genre-Archetypen (die Schülerin, der Samurai), Volksmotive (Kitsune, Troll), Tiere und Essen. Sobald man an eine bestimmte Figur oder Marke denkt, ist die Zeichnung zu nah dran.
3. **Keine Studios, Filme oder Figuren** in Namen, Titeln oder Namensnennungen.
4. **Klein und lesbar.** Die Figuren sind auf der Karte etwa so groß wie ein Symbol. Eine klare Silhouette ist wichtiger als Details.
5. **Gleiche Figur, gleicher Ort.** Wo eine Figur steht, hängt nur von den Kartendaten ab, nicht vom Stil oder vom Ausschnitt. So bleibt die Karte beim Umschalten ruhig.

## Technik

- **Zeichnungen:** `vendor/figures/<figur>/<pose>.svg`, Raster 64×64, nur Flächen.
- **Generator:** `tools/gen_figures.py` erzeugt alle Zeichnungen aus Bauteilen (Kopf, Rumpf, Gliedmaßen, Körper). Nie die SVG-Dateien von Hand ändern, sondern den Generator anpassen und neu laufen lassen:

  ```sh
  tools/gen_figures.py
  ```

- **Kontur und Rand:** setzt `poi_sprite()` in `make-tiles.py` beim Bau des Sprites. Die Tuschekontur hat die Farbe `ink` (Standard: die Markerfarbe des Stils), der breite Sticker-Rand die Farbe `sticker` (Standard: Hintergrund des Markers). In den Zeichnungen steht dafür `currentColor`.
- **Spiegelung:** Jede Pose gibt es zusätzlich gespiegelt (`-m`), damit nicht alle Figuren in dieselbe Richtung schauen.
- **Einstellungen im Stil** (Tabelle `[figures]`):

  | Schlüssel | Bedeutung |
  |---|---|
  | `names` | welche Figuren der Stil zeigt |
  | `density`, `density_rich` | Anteil der Rasterzellen mit Figur; `rich` gilt für Zellen mit passendem Ort oder Grün |
  | `size`, `line`, `rim` | Größe im Sprite, Konturbreite, Breite des Sticker-Rands |
  | `ink`, `sticker` | Farben von Kontur und Rand, wenn die Markerfarben nicht passen (Nachtstile) |
  | `areas` | zusätzliche Flächen, auf denen Figuren stehen dürfen (z. B. `water`, `farmland`) |
  | `poses` | erlaubte Posen: Liste für alle Figuren oder Tabelle je Figur (`"*"` für die übrigen) |
  | `[figures.places]` | Figur → OSM-Klassen, neben denen sie bevorzugt steht |

### Wo die Figuren stehen

- Die Welt ist in ein festes Raster geteilt (Zellen von etwa 450 × 410 m). In der Innenstadt, wo viele passende Orte liegen, wird eine Zelle in vier geteilt.
- Je Zelle wird höchstens eine Figur gesetzt, in dieser Reihenfolge:
  1. **Passender Ort:** Steht in der Zelle ein Ort aus `[figures.places]`, kommt die passende Figur daneben, zum Beispiel der Samurai an die Burg oder der Kolkrabe auf den Friedhof.
  2. **Grünfläche:** sonst eine Stelle im Park, Wald oder auf der Wiese, meist mit einer Figur, die dorthin passt.
  3. **Wahrzeichen:** sonst neben einem Museum, einer Kirche, einem Aussichtspunkt.
  4. **Irgendwo:** sonst eine freie Stelle, nie im Wasser.
- **Wasserwesen** (Kappa, Koi, Nykur, Wal, Nixe …) stehen nur im Wasser, und im Wasser stehen nur Wasserwesen.
- Figuren halten Abstand zu Straßen, je größer die Straße, desto mehr.
- Häufige Orte wie Spielplätze, Gärten oder Geschäfte eignen sich nicht als `places`: Sonst steht überall dieselbe Figur. Lieber seltene Orte nehmen und die Verteilung prüfen.
- Die Figuren liegen unter aller Beschriftung und kollidieren mit nichts. Sonst würde jede Kachel anders entscheiden, und Figuren würden an Kachelkanten zerschnitten.

## Anime

**Look:** allgemeiner Anime- und Manga-Stil als Chibi: großer Kopf, kleiner Körper, große Augen mit Glanzpunkt, rosa Wangen, dicke Tuschekontur, breiter weißer Sticker-Rand. Fröhlich, nicht albern.

**Figuren:**

- **Menschen (28 Genre-Archetypen):** Schülerin (zu spät, Toast im Mund), Ninja, Samurai, Miko, Zauberin (Magical Girl), Shōnen-Held, Idol, Mecha, Maid, Kendō, Yankee, Schulsprecherin, Lehrer, Baseball, Ramenkoch, Mangaka, Butler, Onmyōji, Mönch, Nekomimi, Schwertkämpfer, Magier, Ritterin, Dämonenkönig, Engel, Vampir, Tengu, Oni.
- **Tiere, Wesen, Essen (20):** Kitsune, Winkekatze, Tanuki, Onigiri, Geist mit Laterne, Kappa, Karakasa, Daruma, Mondhase, Drache, Shiba, Panda, Koi, Taiyaki, Dango, Sushi, Umibōzu, Amabie, Fischotter mit Fisch, Ruderboot.
- **Nur im Wasser:** Kappa, Koi, Umibōzu, Amabie, Fischotter, Ruderboot.

**Posen:**

| Wer | Posen |
|---|---|
| Menschen | steht, winkt, läuft, springt, schläft |
| Tiere, Wesen, Essen | sitzt, schläft, springt |

- **Schlafpose der Menschen:** Die Figur liegt auf einem Futon (cremefarbene Matratze, weißes Kissen), der Körper unter einer hellblauen Decke mit weißen Streifen. Der Kopf bleibt aufrecht und leicht geneigt auf dem Kissen, damit man das Gesicht erkennt. Geschlossene Augen als Bögen, „Zz“ oben rechts.
- **Tagsüber** schlafen die Menschen nie (`[figures.poses]` in `anime.toml`), Tiere dürfen ein Nickerchen machen.
- **Anime Nacht:** nur die Schlafposen, alle 48 Figuren, geringere Dichte.

**Abgelehnt, weil zu nah an bekannten Figuren:**

- Hexe auf dem Besen mit schwarzer Katze
- Pirat mit Strohhut
- Pilot im hautengen Anzug
- tropfenförmiger Schleim
- Baumgeister mit klappernden Köpfen
- großer grauer Waldgeist
- im Wasser: Goldfischmädchen, weißer Flussdrache als Junge, Schlammfluss-Geist, beschworene Riesenkröte

**Weitere Lehren:**

- Die Rotzblase beim Schlafen wurde entfernt: Auf der Karte las sie sich als grauer Punkt.

## Island

**Look:** skandinavische Bilderbuch-Volkskunst, so vom Nutzer freigegeben (an Pferd, Troll und Papageitaucher).

- flache Farbflächen, keine Schraffur
- Schatten als eine einzige dunklere Fläche
- Punktaugen, rote Wangen
- Ornamente ohne Kontur: Lopapeysa-Passe, Zickzack, Punkte
- dünne nachtblaue Kontur (`line = 1.2`), Größe 64
- Farben aus der Palette `ISL` im Generator: Wollweiß, Ochsenblut, Moos, Petrol, Senf, Lavagrau, Lupinenviolett, Gletschertürkis

**Figuren:** Islandpferd, Schaf, Papageitaucher, Polarfuchs, Kolkrabe, Rentier, Troll, Huldufólk, Elfenhaus (Álfhóll), Fee, Weihnachtskatze (Jólakötturinn), Weihnachtskerl (Jólasveinn), Badende im heißen Becken, Nykur (Wasserpferd), Marbendill (Meermann), Seewurm, Wal, Eiderente.

**Regeln:**

- **Weihnachtskerl** darf nicht wie der Weihnachtsmann aussehen: graue Kapuze, braune Wolle, struppiger Bart, Skyr-Schale; keine rote Mütze, kein weißer Bommel.
- **Troll** schläft als bemooster Fels (Trolle werden im Sonnenlicht zu Stein).
- **Huldufólk** (verborgenes Volk) hat die Pose „verschwindet“: halb durchsichtig, mit Funkeln.
- **Nur im Wasser:** Nykur, Marbendill, Seewurm, Wal, Eiderente.

**Nachts (Nordlicht):**

- Alle 18 Figuren schlafen.
- Menschen (Huldufólk, Weihnachtskerl) liegen auf einem Moospolster unter einer ochsenblutroten Wolldecke mit Zickzackborte, Kopf aufrecht auf dem Kissen.
- Marbendill döst im Wasser, das Elfenhaus hat die Lichter aus.
- Kontur dunkel (`ink`), Sticker-Rand im Mondlicht-Blau (`sticker`), damit die Figuren auf dem dunklen Grund nicht verschwinden.
- **Tagsüber** schlafen die Menschen nie (`[figures.poses]` in `island.toml`).

## Historische Stile: Fabelwesen

**Look:** nach kolorierten Holzschnitten von Conrad Gessner (16. Jahrhundert), vom Nutzer am Lindwurm freigegeben. Ausdrücklich nicht Chibi und nicht Comic.

- dünne Kontur, kleine Schuppenbögen
- an- und abschwellende Schraffurlinien auf der Schattenseite, hellerer Ton oben
- kleiner Kopf (`HEAD_SCALE`), schlanke Leiber
- Leiber als verjüngte Schläuche entlang einer Mittellinie (`tube()`)
- **Gliedmaßen wachsen aus dem Körper** (Kontur hinter dem Leib, Füllung darüber). Angesteckt wirkende Beine hat der Nutzer abgelehnt.
- flache Teile mit Füllung und paralleler Schraffur (`hat()`)

**Figuren (16):** Lindwurm, geflügelter Drache, Greif, Einhorn, Seeschlange, Nixe, Wassermann, Waldschrat, Roggenmuhme, Zwerg, Gespenst, Irrlicht, Froschkönig, Kornwolf, Basilisk, Wolpertinger.

**Farbfassungen:**

| Fassung | Stil | Farben |
|---|---|---|
| `<name>` | Historisch | handkoloriert: Grün, Rot, Ocker, Blau auf Papier |
| `<name>-sepia` | Kupferstich | Sepiatöne |
| `<name>-kupfer` | Kupferplatte | dunkle Kupferflächen, helle Schraffur wie frisch gestochen |
| `<name>` mit eigener `ink`/`sticker` | Gaslicht | wie Historisch, Kontur und Rand an die Nacht angepasst |

Anime hat einen eigenen `drache`, deshalb heißt der geflügelte hier `flugdrache`.

## Neue Figur hinzufügen

1. **Idee prüfen:** Archetyp, Volksmotiv, Tier oder Essen? Erinnert sie an eine bestimmte Figur, ein Studio oder ein Spiel? Dann verwerfen.
2. **Zeichnen:** im Generator `tools/gen_figures.py` im passenden Abschnitt (`H` für Anime-Menschen, `A` für Anime-Tiere und -Wesen, `ISLAND`, `FABEL`), mit Beschreibung in `DESC` bzw. im Tupel. Alle Posen des Stils anlegen, auch „schläft“.
3. **Generator laufen lassen:** `tools/gen_figures.py`.
4. **Im Stil eintragen:** Name in `names`, passende Orte in `[figures.places]`; für Nachtstile ebenso. Menschen tagsüber in `[figures.poses]` ohne „schläft“ eintragen.
5. **Verteilung prüfen:** einen Probelauf von `figures()` machen und zählen, wie oft jede Figur vorkommt. Keine Figur sollte die Karte beherrschen.
6. **Ansehen:** Stil rendern und die Figur auf der Karte bei Zoom 15 und 16 prüfen, hell und dunkel.
