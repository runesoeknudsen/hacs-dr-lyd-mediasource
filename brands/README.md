# Brands-assets til Home Assistant

HACS-oversigten og integrationsikonet inde i Home Assistant hentes IKKE fra dette
repos README, men fra det centrale [`home-assistant/brands`](https://github.com/home-assistant/brands)-repo
og serveres via `https://brands.home-assistant.io/<domain>/icon.png`. Derfor skal
ikonet bidrages dertil — det kan ikke linkes fra en ekstern URL.

Ikonerne her er genereret ud fra DR's officielle DR LYD-logo (primaer, RGB) fra
DR's logopakke: <https://downol.dr.dk/Download/Designmanager/BRANDS/DRLYD/LOGOPAKKE.zip>
(se <https://www.dr.dk/om-dr/designmanager/dr-koncern/download-drs-logoer>).

- `custom_integrations/dr_lyd/icon.png` — 256x256
- `custom_integrations/dr_lyd/icon@2x.png` — 512x512

## Sådan får du ikonet vist (PR til home-assistant/brands)

1. Fork `home-assistant/brands` på GitHub (med din `runesoeknudsen`-konto).
2. Klon din fork (brug SSH-aliaset, så det sker som runesoeknudsen):

   ```bash
   git clone git@github-runesoeknudsen:runesoeknudsen/brands.git
   cd brands
   ```

3. Kopiér ikonerne ind:

   ```bash
   mkdir -p custom_integrations/dr_lyd
   cp /sti/til/dette/repo/brands/custom_integrations/dr_lyd/icon.png   custom_integrations/dr_lyd/
   cp /sti/til/dette/repo/brands/custom_integrations/dr_lyd/icon@2x.png custom_integrations/dr_lyd/
   ```

4. Commit og push til din fork, og opret en PR mod `home-assistant/brands`.
5. Når PR'en er merget, viser HACS og Home Assistant automatisk ikonet (caching
   kan forsinke det lidt).

## Licens / varemærke

DR, DR LYD og DR-logoet er DR's (Danmarks Radio) varemaerke. Logoet er hentet fra
DR's officielt udgivne logopakke og bruges udelukkende til at repraesentere
DR LYD-tjenesten i integrationen. Det er ikke omfattet af projektets MIT-licens.
