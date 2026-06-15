# DR LYD til Home Assistant

En custom integration der lægger hele DR LYD-podcastkataloget (dr.dk/lyd) ind i Home Assistants mediebrowser som en *media source*. Du kan så browse programmer og afspille afsnit til en hvilken som helst medieafspiller — fx en moOde-baseret Raspberry Pi via MPD-integrationen — præcis som du allerede gør med "media radio" (Radio Browser).

## Sådan virker det

```
HA Media-browser  ->  DR LYD media source  ->  api.dr.dk/radio/v2 (x-apikey)
                                            ->  afspiller (moOde / MPD) med mp3-URL
```

Integrationen henter DR LYD's serie- og episodeliste via DR's interne API og udvælger ved afspilning den bedste progressive MP3 (tættest på 192 kbps). URL'en sendes direkte til din afspiller.

> Bemærk: DR har lukket de fleste offentlige RSS-feeds og tilbyder ikke et officielt offentligt API. Integrationen bruger derfor DR LYD's interne API med en API-nøgle (`x-apikey`). Nøglen kan blive skiftet af DR; se [Opdatering af API-nøgle](#opdatering-af-api-nøgle).

## Installation

### Via HACS (anbefalet)

1. HACS → Integrationer → menuen øverst til højre → **Custom repositories**.
2. Tilføj denne repo-URL med kategori **Integration**.
3. Find "DR LYD" på listen, installér, og genstart Home Assistant.

### Manuelt

1. Kopiér mappen `custom_components/dr_lyd` til din Home Assistant `config/custom_components/`-mappe, så stien bliver `config/custom_components/dr_lyd/`.
2. Genstart Home Assistant.

## Opsætning

1. Indstillinger → Enheder & tjenester → **Tilføj integration** → søg efter **DR LYD**.
2. Bekræft eller indtast API-nøglen (en fungerende standardnøgle er forudfyldt).

## Brug

1. Åbn **Medier** i sidemenuen → vælg **DR LYD**.
2. Browse via **Kategorier** eller **Alle programmer (A-Å)** → vælg et program → vælg et afsnit.
3. Klik **Afspil på...** og vælg din moOde-afspiller (eller en anden medieafspiller).

Du kan også afspille fra en automatisering/script. Find episodens `media-source://`-URI i mediebrowseren, eller brug en direkte mp3-URL:

```yaml
action: media_player.play_media
target:
  entity_id: media_player.moode
data:
  media_content_type: music
  media_content_id: media-source://dr_lyd/e/<base64-url>
```

## Opdatering af API-nøgle

Hvis afspilning/browsing pludselig fejler med en autorisationsfejl, er DR's nøgle sandsynligvis skiftet:

1. Åbn `https://www.dr.dk/lyd` i en browser og start afspilning af et afsnit.
2. Åbn udviklerværktøjer → **Network**.
3. Find et kald til `api.dr.dk/radio/...` og kopiér værdien af request-headeren `x-apikey`.
4. I Home Assistant: fjern DR LYD-integrationen og tilføj den igen med den nye nøgle.

## Test mod moOde (MPD)

1. Sørg for at din moOde-enhed er tilføjet i Home Assistant via **MPD**-integrationen, så den vises som en `media_player`.
2. Browse til et afsnit i DR LYD og vælg **Afspil på → moOde**.
3. moOde modtager mp3-URL'en (DR's `assetlinks`-URL redirecter til selve filen, som MPD følger) og begynder afspilning.

## Begrænsninger

- Bruger DR's interne, udokumenterede API. Endpoints og nøgler kan ændre sig uden varsel.
- Live-radiokanaler er ikke en del af denne integration (brug Radio Browser til det).
