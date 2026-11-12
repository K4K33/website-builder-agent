# Kaurivo: maksuton Windows-rakentaja

Tämä on **oikea paikallinen työntekijä**, ei pelkkä Githubin työjonon laukaisin.
Kun ohjelma on käynnissä, se tarkistaa Kaurivon suojatun Supabase-jonon
noin kerran sekunnissa ja aloittaa vapaan työn heti. Selainta ei tarvitse pitää
auki. Työ ei läpäise laatutarkistuksia ilman oikeaa QA:ta.

## Ennen asentamista

- Windows 10/11, tarpeeksi levytilaa kahdelle paikalliselle Ollama-mallille
  (noin 9–12 GB plus rakennustiedostot).
- [Python 3.11](https://www.python.org/downloads/windows/), valitse *Add Python to PATH*.
- [Git for Windows](https://git-scm.com/download/win) sekä Git Credential Manager.
- [Ollama for Windows](https://ollama.com/download/windows). Paikallisten mallien
  nopeus ja laatu riippuvat koneesi muistista ja näytönohjaimesta.
- GitHubin kirjautuminen Git Credential Manageriin, jolla on
  **Contents: Read and write** repositorioon `K4K33/website-builder-agent`.
  Pelkkä aiemmin luotu **Actions: Read and write** ei riitä demon julkaisuun.
  Älä koskaan tallenna GitHub-tokenia verkkosivun HTML-koodiin.
- Avaa Windowsissa Ollama; `http://127.0.0.1:11434/api/tags` toimii vain
  omalla koneella, ei julkisena palvelimena.

## Asenna

1. Avaa Kaurivon [Demot-hallinta](https://k4k33.github.io/website-builder-agent/kaurivo/admin/).
   Paina **Luo Windows-rakentajan avain**. Kopioi kertaluonteinen `kvl_`-avain.
   Huomaa: uuden avaimen luominen mitätöi vanhan; älä jaa sitä keskusteluun.
2. Avaa Windows PowerShell (tavallisena käyttäjänä):
   ```powershell
   cd $env:USERPROFILE
   git clone https://github.com/K4K33/website-builder-agent.git
   cd website-builder-agent\website-builder-agent\website-builder-agent\scripts
   .\setup_kaurivo_windows.ps1
   ```
   Jos PowerShell estää paikallisen skriptin suorittamisen, voit käyttää
   `powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_kaurivo_windows.ps1`.
   Älä kopioi komentoa tuntemattomasta lähteestä.
3. Asennus pyytää hyväksynnän kahdelle **maksuttomalle paikalliselle AI-mallille**
   (`qwen2.5-coder:7b` ja näkökykyinen `llava:7b`) sekä suojatun
   Windows-avaimen. Mallit ladataan suoraan Ollamaan.
4. Hyväksy Windowsin sisäänkirjautumisen yhteydessä käynnistyvä työntekijä.
   Jos valitset Ei, käynnistä työntekijä käsin:
   ```powershell
   .\start_kaurivo_worker.ps1
   ```

## Käynnistys ja todennus

- Kun PowerShell näyttää **Kaurivo local AI valmis**, työntekijä kuittaa
  olevansa käytettävissä Supabasessa. Demopainike ei silloin lähetä työtä
  GitHub Actionsin suorittajajonoon. Itse työn aloittamisen vahvistaa
  tietokannan `researching`-tila.
- Kun kone on suljettu, nukkuu tai mallit eivät ole valmiina, käytetään
  nykyistä GitHub-varareittiä; tällöin sekuntitavoitetta ei voida taata.
- Paikallisen työtekijän valmisteluaika riippuu koneen tehosta. Noin yhden
  sekunnin **jonon havainto** ei tarkoita, että koko verkkosivu valmistuu
  sekunnissa.
- Kun työntekijä tekee jo toista sivua, seuraava työ odottaa sen
  vapautumista. Nykyinen yhden työntekijän versio ei rakenna useaa
  asiakassivua rinnakkain.
- Jos paikallinen AI jää riittämättömäksi 9,5/10 tasoon, QA pysäyttää
  julkaisun. Laadunvarmistusta ei ohiteta vain nopeuden takia.

## Julkaisu ja tiedot

Julkaisu käyttää samaa `auto/kaurivo-demos`-haaraa Render-esikatseluun kuin
nykyinen rakennusagentti, mutta **Git Credential Managerin** kirjautumista
Windows-käyttäjänä. Sisäinen QA-raportti julkaistaan samalla kertaa
`qa.html`-tiedostona ja tarkistetaan oikeasta HTTPS-osoitteesta ennen kuin
Supabase saa `internal_preview`-tilan.

AI-kutsut menevät vain oman koneen Ollama-palveluun (`127.0.0.1`);
maksullisia OpenRouter-kutsuja ei tehdä. Julkisen yrityksen lähdetutkimus
tarvitsee kuitenkin internetyhteyden, ja Kaurivon nykyinen pipeline voi
käyttää muita maksuttomia lähdehakuja niiden sallittujen rajojen mukaan.
Lähdemateriaalin, kuvien käyttöoikeuksien, brändin ja QA:n tarkistukset
säilyvät pakollisina.

## Turvallisuus ja palautuminen

- Windowsin asennusohjelma salaa laiteavaimen käyttäjäkohtaisesti
  **Windows DPAPI** -suojauksella. Supabasen tietokantaan jää vain
  SHA-256-tiiviste. Et tarvitse `service_role`-avainta tietokoneelle.
- Jos avain vuotaa tai haluat vaihtaa konetta, paina Demot-näkymässä
  **Luo Windows-rakentajan avain** uudestaan. Vanha lakkaa toimimasta.
- Työ käyttää edelleen Supabasen yksityisiä rakennusvaiheiden tarkistuspisteitä,
  ja tilapäiset virheet siirretään hallittuun uusintaan.
- Jos työntekijä ei saa riittäviä yritysfaktoja tai riippumaton QA hylkää sivun,
  automaatio merkitsee työn korjattavaksi. Se ei julkaise keksittyjä tietoja
  eikä kierrä virheitä rajattomasti.
- Windows Task Scheduler käynnistää työntekijän käyttäjän sisäänkirjautuessa.
  Koneen pitää olla päällä, hereillä ja verkkoyhteydessä.

## Vianetsintä

- `local AI ei vielä valmis`: varmista, että Ollama on käynnissä ja
  `ollama list` näyttää molemmat mallit; myös QA-mallin on tuettava kuvia.
- `local_worker_not_enrolled`: luo uusi Windows-avain Demot-sivulla ja aja
  asennusohjelman avaintallennus uudelleen.
- `preview_publication_failed`: tarkista Git Credential Managerin
  `Contents: Write` -oikeus ja että Render seuraa oikeaa haaraa.
- `source_research_incomplete`: kyse on lähdesisällön ongelmasta, ei
  Windows-jonosta. Tarkista virheilmoituksessa mainittu alkuperäinen URL.
- `quality_gate_not_approved`: sivustoa ei julkaista ennen korjausta.
