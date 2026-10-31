# Kaurivo — käyttöönotto ja laadunvarmistus 31.10.2026

## Mikä on toteutettu

- Suomen ajassa 04.13 PRH-yöhaku, 06.17 vara-ajo, jos saman päivän
  ensimmäisen ajon onnistumista ei ole vahvistettu GitHubista.
- Administa käynnistyvä varahaku; enintään 3 per Suomen päivä, vähintään
  25 minuutin väli, enintään 6 PRH-API-kyselyä per ajo.
- Yöajon OIDC-todennettu suojattu tietokantatallennus ja erillinen
  epäonnistumisen OIDC-raportointi. Todellinen uusien rivien lisäysmäärä
  erotetaan käsiteltyjen tietueiden määrästä. Tulos tallennetaan
  yksityiseen kaurivo_pipeline_events-tauluun.
- Aamuilmoituksen 08.00 / 08.27 best-effort GitHub-ajot raportoivat
  onnistumisen, epäonnistumisen tai nollatuloksen samaan lokiin.
  Palvelin kertoo yhdelle adminille rekisteröityjen laitteiden määrän.
  Pelkkä iOS-ilmoituslupa ei tarkoita tallennettua push-tilausta.
- Aamun yritykset -näytössä Automaation tila on kokoontaitettava,
  ei vie turhaan tilaa. Tilan puuttuminen EI ole todiste virheestä.
- Yrityksen asiakasprioriteetti 0–100 lasketaan vain ihmisen kirjaamasta
  verkkosivun, aktiivisuuden, tarpeen ja lähteen tutkimuksesta.
  Pistemäärä on sisäisen tarkistuksen prioriteetti, ei
  ostotodennäköisyys tai vahvistettu maksukyky.
- Merkitään toiminta, sivuston uudistustarve, maksukykyhavainnon
  perustelu, lähde-URL, demobriefin vaihe ja yhteydenoton lainmukaisuuden
  tila. Maksukyvyn tietoa ei keksitä PRH:n perustiedoista.
- Ilmaiseksi tuotettava **sisäinen demobrief-luonnos**, jonka on
  tarkoitus auttaa oikean premium-demon myöhempää rakentamista ja
  kolmeen alan vertailusivustoon perustuvaa QA:ta. Demobrief EI ole
  valmis asiakkaalle julkaistava sivusto eikä mikään viesti lähde ulos.
- Markkinointikielto lukitsee yrityksen yhteydenottostatuksen.
  Palvelintason CHECK-rajoitukset estävät ihmisen hyväksynnän ilman
  aktiivisuuden havaintoa ja lähdettä, estävät lähetetyksi kirjaamisen
  ilman hyväksyntää sekä vaativat tallennetun demobriefin kun
  demobrief on merkitty valmistelluksi.
- Valitun päivän myyntisuppilossa näkyvät tarkistetut, linkit,
  demobriefit, käsin kirjatut yhteydenotot, vastaukset, vahvistetut
  CRM-kaupat ja kiellot. Yhteydenottoluvut ovat KÄSIN kirjattuja,
  eivät Gmailiin sidottua lähetystodennetta.

## Mitä käyttäjän tulee vielä tehdä

1. Avaa Kaurivon aloitusnäytölle asennettu iPhone-sovellus.
2. Kirjaudu admin-tilillä ja avaa Aamun yritykset > Lisätiedot
   ja asetukset > **Salli ilmoitukset**. Selaimessa hyväksytty
   ilmoituslupa ei yksin synnytä Supabase-palvelintilausta.
3. Tarkista tekstistä: **Push-tilaus vahvistettu palvelimella** ja
   laitteiden määrä, ja suorita **Testaa ilmoitus**.
4. Katso sunnuntain 1.11.2026 yöhaun jälkeen 04.13 sekä 06.17
   varmistus ja aamun 08.00 / 08.27 tila. GitHub ajastus ei takaa
   täsmällistä aloitusminuuttia eikä iOS toimitushetkeä.
5. Haluatko automaattisia verkkosivuehdotuksia? Lisää
   **KAURIVO_TAVILY_API_KEY** vain GitHub Actions -salaisuudeksi,
   jos Tavilyssä on nimenomaan ilmainen plan ilman maksullista
   pay-as-you-go -käyttöä. Enintään 12 basic-hakua ajoa kohden.
   Ilman avainta täysin pois päältä, eikä AI-krediittejä käytetä.
6. Jokainen liidi vaatii todellisen sivuston ja lähteen tarkistuksen
   sekä realistisen maksukykytarkistuksen. Älä merkitse havaintoa
   todeksi PRH:n tyhjän verkkosivukentän vuoksi.

## Mitä ei pidä väittää valmiiksi

- Kokonaisen yksilöllisen asiakasdemon automaattinen tuotanto ja julkaisu
  ei ole toteutettu. Nyt valmiina on vain yksilölliseen tutkimukseen
  perustuvan briefin valmisteluun tarkoitettu työnkulku.
- Automaattinen yritysten maksukyky- ja verkkosivun laatupäätös ei ole
  luotettavasti mahdollinen pelkkien rekisteritietojen perusteella.
- Ei automaattista kylmäsähköpostia, henkilökontaktien keruuta,
  myyntiviestejä tai markkinointikiellon ohittamista.
- Ei vielä vahvistusta, että kyseisen käyttäjän iPhone on todella
  tilannut pushit ja saa ne klo 8; vain fyysinen laitetesti todistaa.
- Yöajon ensimmäisen onnistuneen suorituksen tila vaatii oikeat
  GitHub Actions-, Supabase- ja laitetestit.

## Tekninen turvallisuus

Kaikki Supabasen tapahtuma- ja yritystiedot ovat RLS:n takana ja
vain vahvistettu Kaurivon admin saa lukea niitä. Julkinen GitHub Pages
saa vain julkisen Supabase anon-avaimen. Service role ja VAPID-yksityisavain
pysyvät palvelimella, GitHub Actions käyttää lyhytkestoista OIDC:tä.
Tietokanta ei talleta salaisia push-avaimia tapahtumalokiin eikä
henkilöitä koskevia yksityisiä havaintoja ilman arviointia.

Oikeudelliset portit: docs/KAURIVO_LEGAL_COMPLIANCE.md.
Verkkosivututkimuksen rajat: docs/KAURIVO_WEBSITE_RESEARCH.md.
