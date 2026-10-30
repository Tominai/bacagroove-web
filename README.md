# bacagroove.com

Oficiální web Bača Groove Orchestra – rozcestník na Spotify, YouTube, YouTube Music, Apple Music a sítě.

- `site.json` – texty, odkazy, píseň na úvodní kartě (`featured`), klip (`video`) a pořadí písní (`songs`)
- obaly a odkazy písní se berou z dat směřovacích stránek (`Tominai/bgo-listen`, složka `_data/`)
- `build.py` sestaví web do `dist/`; GitHub Actions ho nasadí na GitHub Pages po každé změně a denně
- místně: `python3 build.py --listen ../bgo-listen` (náhled bez měření: `--preview`)

Spravuje Claude / Hermes. Stránky se needitují ručně, mění se `site.json`.
