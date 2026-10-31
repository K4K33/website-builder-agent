# Kaurivo — yrityshaun, demojen ja yhteydenottojen lakisääteiset portit

Päivitetty 31.10.2026. Tämä on projektin tekninen compliance-ohje,
ei asianajajan antama oikeudellinen lausunto. Arvioi vaatimukset uudelleen
ennen uusien tietolähteiden, maiden, viestikanavien tai automaattisten
lähetysten käyttöönottoa.

## NYT SALLITTU — yöllinen ja manuaalinen yrityshaku

- Vain virallinen PRH/YTJ avoin data. Nimeä lähde: **PRH/YTJ open data,
  CC BY 4.0** ja linkitä alkuperäiseen lähteeseen.
- Älä käytä PRH:n tai YTJ:n logoa tai esitä Kaurivoa näiden virallisena
  palveluna. Älä muuta virallisen datan alkuperää epäselväksi.
- Tallenna vain tarpeelliset perustiedot: yrityksen nimi, Y-tunnus,
  paikkakuntavihje, toimiala, rekisterissä ilmoitettu URL, lähde,
  hakupäivä ja tarkistuksen vaihe.
- Rekisterissä **ei mainittua verkkosivua** ei saa esittää todistettuna
  "ei verkkosivua" -havaintona. PRH:n rekisterimerkintä ei myöskään
  todista, että yritys toimii nyt, pystyy ostamaan sivuston tai että
  nykyinen sivusto on huono.
- Pidä haut hallittuina: manuaalinen varahaku enintään kuusi virallisen
  rajapinnan kyselyä per käynnistys, kolmen käynnistyksen päiväkatto,
  vähintään 25 min käynnistysten välissä; reagoi HTTP 429 -rajoitukseen.
  Valtakunnallinen yöajo hakee aineiston yhdellä rajatulla ZIP-pyynnöllä.
- Säilytä lista admin-rajatussa tietokannassa (RLS). Ei julkisia liidilistoja,
  sähköpostiosoitteiden keräämistä massoittain tai datan myyntiä.
- PRH:n YTJ-avoindata ei kata yksityisiä elinkeinonharjoittajia eikä tarjoa
  yritysten sähköposteja tai puhelinnumeroita. Älä lisää niitä toisesta
  lähteestä ilman erillistä käyttötarkoitus-, lisenssi- ja tietosuojatarkistusta.

## ESTETTY — automaattinen outreach nykyisessä vaiheessa

**Älä koskaan kytke PRH-liidin tallennusta automaattiseen
sähköpostin lähetykseen.** Haku, demoehdotus ja viestiluonnos eivät ole
laillisuusarvio tai lupaa kontaktointiin. Ei automaattisia myyntiviestejä,
viestijonoja lähetystilassa, eikä "valmis kontaktoitavaksi" -merkintää
vain rekisteritietojen perusteella.

Ennen mahdollista yhteydenottoa vaaditaan:

1. Todellinen aktiivinen yritys, toimintaa vastaava palvelutarve,
   oikean verkkosivun käsin tarkistus ja mahdolliset kieltoilmoitukset.
2. Vastaanottajan luokittelu. Suomen sähköisen viestinnän palveluista
   annetun lain 202 §:n mukainen yhteisölle kohdistettu B2B-viesti voi
   olla sallittu ilman ennakkosuostumusta, jos yhteisö ei ole kieltänyt.
   Henkilökohtaisiin osoitteisiin sovelletaan pääsääntöisesti
   200 §:n ennakkosuostumusta; työntekijän tehtäväasemaan liittyvää
   poikkeusta ei saa olettaa yleiseksi luvaksi. Epäselvässä tilanteessa
   älä lähetä ilman suostumusta.
3. Tunnistettava markkinointiviesti, todellinen lähettäjä Kaurivo ja
   voimassa oleva vastausosoite. **Jokaisessa markkinointiviestissä**
   helppo maksuton kielto-ohje (esim. "Jos ette halua yhteydenottoja
   Kaurivolta, voitte vastata tähän viestiin: ei yhteydenottoja.").
   Älä poista tätä vaatimusta ulkoasutoiveen vuoksi.
4. Toteuta kielto heti, kirjaa vähimmäistieto suojattuun estolistaan
   uudelleenkontaktoinnin ehkäisemiseksi, myös uusista liidilähteistä.
   Tarkista estolista aina ennen uutta viestiä.
5. Jos talletetaan tunnistettavan henkilön nimi, henkilösähköposti,
   puhelin tai muu henkilötieto, dokumentoi käyttötarkoitus,
   käsittelyperuste (mahdollinen oikeutettu etu arvioituna tapauskohtaisesti),
   etutesti, säilytysaika, vastaanottajat ja tietoturva. Tarjoa
   ymmärrettävä tietosuojainformaatio (myös lähde), tarvittaessa
   viimeistään ensimmäisellä yhteydenotolla tai kuukaudessa
   GDPR 14 artiklan mukaisesti. Käsittele poisto-, tieto- ja
   vastustamispyynnöt asianmukaisesti.
6. Valmistele tietosuojaseloste, tietojen minimointi,
   poistokäytännöt ja palveluntarjoajien tietojenkäsittelysopimukset
   ennen oikean henkilöyhteystietorekisterin käyttöönottoa.
7. Hanki käyttöoikeus kuviin, fontteihin ja logoihin. Demoa ei saa
   esittää asiakkaan tilaamana, toteutettuna tai suosittelemana.
   Älä julkaise asiakkaan brandia hyödyntävää demo-osoitetta
   harhaanjohtavalla tavalla. Ei keksittyjä referenssejä eikä arvioita.
8. Varmista nettisivun/kolmannen osapuolen tietolähteen käyttöehdot ennen
   mitään erillistä crawlausta tai kontaktitietojen poimintaa.
9. Lähetys vasta **erillisen ihmisen hyväksynnän** ja viestikohtaisen
   lainmukaisuustarkistuksen jälkeen. Viestin vastaanottajat tarkistetaan
   yksitellen. Lähetys ei sisälly yöajoon eikä manuaaliseen yrityshakuun.

## Viralliset lähteet

- PRH avoin data: https://avoindata.prh.fi/en/info/swagger-ui
- PRH YTJ OpenAPI: https://avoindata.prh.fi/opendata-ytj-api/v3/schema?lang=fi
- CC BY 4.0: https://creativecommons.org/licenses/by/4.0/
- Laki sähköisen viestinnän palveluista 917/2014, erityisesti 200–203 §:
  https://www.finlex.fi/fi/lainsaadanto/2014/917
- Tietosuojavaltuutetun päätös henkilökohtaisesta vs. yhteisöosoitteesta:
  https://www.finlex.fi/fi/viranomaiset/tietosuojavaltuutettu/2020/629
- EDPB vastustamisoikeus:
  https://www.edpb.europa.eu/sme/be-compliant/respect-individuals-rights_en
- Euroopan komissio, GDPR:n perusteet:
  https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/legal-grounds-processing-data_en

## Tämänhetkinen todennus (31.10.2026)

- PRH:n rajapinnan hakuehdot `location`, `companyForm` ja `page`
  vastaavat virallista OpenAPI-kuvausta.
- Kaurivon yrityslistan Supabase-taululla on RLS, ja tietueiden
  luku/muokkaus on rajattu `kaurivo_internal.is_kaurivo_admin()`-tarkistuksella.
- Kaurivon Push VAPID-, tilaaja- ja manuaalisen hakujen taulut eivät
  myönnä suoraa pääsyä julkisille tai tavallisille kirjautuneille
  rooleille; palvelin vastaa tunnistautumisesta.
- PRH-haun luotettava tuotantosuoritus ja ensimmäinen aidosti perille
  mennyt push-ilmoitus ovat edelleen erikseen todennettavia.
