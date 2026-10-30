# Heaven Bar – Testvorschau

Konzept-Prototyp der Website für die Heaven Bar (1. OG, Einsiedlerstraße 9, 64579 Gernsheim).
Nur zum internen Testen, Zugang über den NFC-Chip. Inhalte sind teilweise Platzhalter.

## Aufbau

| Pfad | Inhalt |
|---|---|
| `index.html` | Die veröffentlichte Seite (GitHub Pages), inkl. Zugangssperre und `noindex` |
| `robots.txt`, `.nojekyll` | Suchmaschinen aussperren, Pages ohne Jekyll ausliefern |
| `quelle/seite.html` | Quelltext der Seite mit Platzhaltern für Texturen, Fotos und Schriften |
| `quelle/texturen/` | Erzeugte Marmor-, Türkis- und Blattgold-Texturen, Wolken-Sprite |
| `quelle/fotos/` | Aufbereitete Fotos aus den Handy-Videos der Bar |
| `quelle/werkzeuge/` | Python-Skripte: Texturen erzeugen, Fotos aufbereiten, Seite bauen, veröffentlichen |

## Inhalte ändern

Getränkekarte, Events, Anlässe und Verleih-Extras stehen gesammelt im Block `const DATA = {...}` in `quelle/seite.html`.
Später wird dieser Block durch ein CMS ersetzt, in dem das Team die Inhalte pflegt.

## Neu bauen

```bash
npm install                   # Schriften laden (einmalig)
cd quelle/werkzeuge
python3 bauen.py              # Texturen, Fotos und Schriften einbetten → build/heaven-bar.html
NFC_KEY=<schlüssel> python3 veroeffentlichen.py   # Zugangssperre davor → index.html
```

Schriften (Cinzel, Cormorant Garamond, Jost, Pinyon Script, alle SIL Open Font License) kommen aus den npm-Paketen `@fontsource/*` und werden eingebettet, es gibt keine Verbindung zu Google Fonts.
Der NFC-Schlüssel steht nicht im Repo, nur sein Hash in `index.html`.
