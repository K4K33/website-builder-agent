# Kaurivo: monikielisten yritysten käsittely (1.11.2026)

## Yhteydenotto ja demo ovat eri kielipäätöksiä

- Rekisterinimen Ab, ruotsinkielinen kunta tai Ahvenanmaa on vain vihje. Ne eivät todista yhteydenottokieltä.
- Yhteydenottokieli: fi, sv, en. Demon sisältökieli: fi, sv, fi_sv, en. Molemmat ovat oletuksena undetermined.
- Kielen valinta vaatii lähdelinkin (language_evidence_url). Ilman sitä yhteydenottoa ei voida hyväksyä eikä demobriefiä valmistella.
- Ruotsinkielinen myyntiviesti kirjoitetaan kokonaan ruotsiksi, myös yksilöllinen, tarkistettu havainto (outreach_observation_sv) ja maksuton yhteydenottokielto.
- Kaksikielisen sivun demobriefissä vaaditaan oikeat erilliset FI/SV-sisällöt, navigaatio, lomakkeet, metatiedot ja kielenvaihto. Ei pelkkää suomenkielistä sivustoa ruotsinkielisille.
- Ammattimainen ruotsin kieli tarkistetaan ennen mahdollista asiakkaalle lähettämistä. Mitään sähköpostia ei lähetetä automaattisesti.
- Suojaus on sekä käyttöliittymässä että Supabasen tarkistustriggerissä.
- Älä väitä PRH:n tyhjää verkkosivukenttää todistukseksi sivun puuttumisesta.

## Todennettuja esimerkkejä

Norrgårds Busstrafik Ab: Asiakastieto ilmoittaa yrityksen kieleksi ruotsin. Yhteydenottokieleksi merkitty sv. Sivustokieli tarkistamatta.
Lähde: https://www.asiakastieto.fi/yritykset/fi/norrgards-busstrafik-ab/28891335/rekisteritiedot

Västra Hamnens Restaurangdrift Ab: ravintolan nykyinen verkkosivusto on ruotsinkielinen. Sivustokieleksi merkitty sv, ja yhteydenottokieli alustavasti sv (vastaanottajan kieli vielä varmistettava ennen lähettämistä).
Lähde: https://www.paviljongen.ax/

## 1.11.2026 ajot

PRH:n klo 04.13 paikallisaikainen haku käynnistyi todellisuudessa 11.12 Suomen aikaa; tallennettu 50 yritystä. Klo 06.17 vara-ajo käynnistyi vasta 13.17 ja tallensi 50 uutta, vaikka päähaku oli jo onnistunut. Väärä kellonaikaan sidottu estoehto korjattiin. Historiatiedot säilyvät: yhteensä 100 yritystä päivän 1.11. listalla.

PRH:n valmistumisen jälkeen suoritettava push-askel on ajettu GitHubissa, mutta palvelin vastasi, ettei tilaajalaitteita ole. Pelkkä iPhonen ilmoituslupa ei luo palvelimelle rekisteröityä tilausta. Kaurivon asennetun PWA-sovelluksen tilausta on edelleen testattava.

GitHub Actions -ajastukset ovat best effort -toimitus, eivät tasan klo 8 takuu. Oikeat lähetys- ja asiakaskontaktikäytännöt: docs/KAURIVO_LEGAL_COMPLIANCE.md.
