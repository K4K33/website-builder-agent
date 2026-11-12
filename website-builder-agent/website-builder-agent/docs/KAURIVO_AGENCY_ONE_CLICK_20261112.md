# Kaurivo: toimistotason työnkulku ja todennettava Rakenna demo -ketju

## Konkretiaksi muutetut kilpailijaopit

- **Relume-tyylinen suunnittelun luovutus**: yrityksen oma sivukartta ja
  jokaisen reitin asiakastehtävä ennen koodausta. Kaurivon olemassa oleva
  `brand_design_blueprint` toimii pohjana, ja
  `utils/agency_handoff.py` kulkee samoilla tiedoilla Builderiin,
  korjaukseen ja riippumattomaan kuvalliseen QA:han.
- **Framer/Webflow-tyylinen selkeämpi visuaalinen kieli**: yrityskohtainen
  rytmi, typografia, oikea media ja tehtävään liittyvät vuorovaikutukset.
  Ei geneeristä komponenttien sommitelmaa eikä samaa mallipohjaa kaikille.
- **10Webin URL-aloitus, mutta parempi sisältö- ja toimintojen säilytys**:
  kaikki alkuperäiset palvelut, varaukset, yhteystiedot, kauppa, kieliversiot
  ja oikeudet kartoitetaan ennen hyväksyntää. Puuttuva tieto = HOLD.
- **Dudan asiakasluovutuksen periaate**: omistajan hyväksyntä,
  kommentointi ja CMS-luovutus pysyvät erillisinä työvaiheina.
  **Huom. Kommentointi-/CMS-editoria ei lisätty tässä muutoksessa eikä
  olemassa olevaa staattista demoa saa väittää asiakkaalle muokattavaksi.**
- Master-Prompt V6 ladataan `utils.service_quality.POLICY`-kontraktiin
  jokaisessa Research/Builder/Revision/QA-vaiheessa. Handoff vaatii
  lisäksi TÄSMÄLLEEN nykyisen Master-Promptin SHA:n.
- Lopullinen hyväksyntä edellyttää edelleen todellista selaintestiä,
  lähdesisällön säilymistä, riippumattoman arvioijan näyttöä ja
  julkaisun jälkeisiä kaikkien reittien tarkistuksia.

## Rakenna demo

1. Ylläpitäjän kirjautunut painallus luo tai palauttaa **yhden**
   yrityskohtaiseen prospektiin sidotun Supabase-työn.
2. Uusi oma Ollama-työntekijä ilmoittaa `backend=ollama` ja
   `ready=true`. Pelkkä vanhan Codex-työntekijän heartbeat **ei
   enää tarkoita**, että maksuton paikallinen AI on valmis.
3. Realtime-ilmoitus herättää työntekijän. Painetun yrityksen
   `dispatch_requested_at` tallentuu yksityiseen jonoon; valinta
   käsitellään jonossa ensimmäisenä. Ei henkilö- eikä yritystietoa
   lähetetä Realtime-viestissä.
4. Jos aiempi Codex-työ käytti kolme päiväyritystä, uusi paikallinen
   Ollama saa **yhden lisäyrityksen saman päivän aikana**. Merkintä
   `offline_recovery_day` estää rajattoman kierron.
5. Painikkeen toistaminen jo jonossa olevalle yritykselle yrittää
   herätystä uudelleen. Käyttäjälle erotetaan "käynnistys lähetetty"
   ja todellinen `researching`-tila.
6. Jos paikallinen AI ei ole asennettu, kone on lepotilassa tai
   tutkimus/QA hylkää tuloksen, järjestelmä **ei** väitä demoa
   valmiiksi. Maksuttomuus ei takaa rajatonta laskentakapasiteettia.

## Käyttöönoton ja todentamisen rajat

Uusi SQL-migraatio, Edge Function sekä Windows-worker täytyy ottaa käyttöön
yhdessä. GitHubin vihreä yksikkötesti ei vahvista Windows-koneen muistia,
Git Credential Manageria, paikallista Ollama-mallia eikä Koxmaticin
todellista loppuun saakka hyväksyttyä 9.5/10-esikatselua.

Työntekijän päivitys Windowsissa:
```powershell
cd C:\Users\oppilas\kaurivo-rakentaja\website-builder-agent\website-builder-agent\scripts
git pull --ff-only
powershell -NoProfile -ExecutionPolicy Bypass -File .\switch_kaurivo_to_offline.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_kaurivo_worker.ps1
```
Älä aloita kahta workeria samanaikaisesti, äläkä kopioi PowerShell-kehotetta
komentojen edelle. Julkaisemisen tulee onnistua vain oikean riippumattoman
QA:n ja julkisen selaintarkistuksen jälkeen.
