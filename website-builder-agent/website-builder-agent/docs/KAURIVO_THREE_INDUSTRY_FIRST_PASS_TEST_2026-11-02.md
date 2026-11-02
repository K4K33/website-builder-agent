# Kaurivo — kolmen eri toimialan ensiversiotesti

Päiväys: 2026-11-02
Tila: yritykset VALITTU; demosivustoja ei ole vielä rakennettu tai esitelty asiakkaille.

## Tavoite

Todentaa Kotifixi V15:stä opitut Builder/QA-standardit kolmella aidosti
erilaisella suomalaisella pk-yrityksellä. Kolmen toisistaan riippumattoman
alan ensiesikatselun tavoite on vähintään noin 9/10 todellista laatua
ilman käyttäjän 14 peräkkäistä palautekierrosta. Sisäiset kehityskierrokset
ja mock-testit ovat sallittuja ennen ensimmäistä omistajalle näytettävää
linkkiä. Pidemmän aikavälin ≥9,5/10 laatukynnys säilyy.

## 1. AUTOKORJAAMO — TE-Service Oy

- Sijainti: Kirkkonummi / Lapinkylä.
- Yrityksen sivu: https://te-service.fi/
- Yrityksen virallinen nimi: TE-Service Oy, y-tunnus 2612679-5.
- Todennettu yrityksen omalta sivulta: autohuolto, korjaus, monimerkkipalvelu,
  pakettiauto-osaaminen, sijaisautopalvelu, yhteydenottotiedot.
- Testin lähtötaso: nykyisellä sivulla on paljon erillisiä huoltokategorioita,
  useita painikkeita ja historiallisia asiakasarvioita.
- Ensiversion oma tavoite: nopea, käytännöllinen ja visuaalisesti tekninen
  korjaamosivusto, selkeät huoltopalvelut sekä todennettu ajanvarauspolku.
  Älä rakenna toimimattomia varausnappeja tai tee fiktiivisiä takuu-/hinta-
  lupauksia. Säilytä Fixus-ketjuun liittyvät faktat vain varmennettuina.
- Alkuperäiset lähteet:
  https://te-service.fi/
  https://te-service.fi/yhteystiedot/yritys/
  https://www.asiakastieto.fi/yritykset/fi/te-service-oy/26126795/rekisteritiedot

## 2. RAVINTOLA — Ravintola Rosanne

- Sijainti: Laukaa, Laukaantie 22–24.
- Yrityksen sivu: https://www.ravintolarosanne.fi/
- Rekisteröity toimija: Cafe Anne-Maria Oy (0926122-3), Ravintola Rosanne
  käytössä yrityksen liiketoiminnan nimenä. Eri sivuilla esiintyvien
  yritysnimien julkiseen käyttöön tarvitaan lähdeuskollinen tarkistus.
- Yrityksen omalta sivulta: kotiruokalounas, kahvila, juhlapalvelu,
  kokouspalvelu, vaihtuva viikkolounas ja Grilli Rosanne -tiedot.
- Testin lähtötaso: lounaslista ja ajankohtaistiedotteet ovat etusivulla
  pitkänä tekstinä; eri sivujen ilmoitetut aukioloajat vaihtelevat.
  Toimimattomasta palautesivusta kerrotaan suoraan.
- Ensiversion oma tavoite: ruoka- ja tunnelmakeskeinen identiteetti,
  selkeä päivitettävä viikkolounaslista, aukioloajat ja yhteystiedot,
  sekä erillinen juhlapalvelun polku. Ei oleta todellista varausjärjestelmää.
  Jos ajat/ruokalista ovat keskenään ristiriitaisia tai vanhenevat,
  säilytä ne demo-fiktioina selvästi merkittyinä tai jätä pois,
  älä väitä tämän viikon listaksi. Päivitettävä CMS on tärkeä.
- Alkuperäiset lähteet:
  https://www.ravintolarosanne.fi/
  https://www.ravintolarosanne.fi/lounas
  https://www.ravintolarosanne.fi/yhteystiedot
  https://laukaa.yrityshakemistot.fi/

## 3. RAKENNUSLIIKE — Rakennuspalvelu RI-LI Oy

- Sijainti: Mikkeli / Etelä-Savo.
- Yrityksen sivu: https://www.rakennuspalvelurili.com/
- Y-tunnus: 2843312-3.
- Yrityksen sivulta: uudisrakentaminen, remontit, sauna- ja
  kylpyhuonesaneeraukset, huoneistotyöt, palvelualue Etelä-Savossa
  sekä esimerkkejä valmistuneista työkohteista.
- Testin lähtötaso: pitkät palvelu- ja UKK-tekstit, monia kuvaosioita,
  sivun oma kotitalousvähennysluku 35 % (päivitettävä/verifioitava
  viranomaislähteestä, EI kopioitava demoon oletusarvona).
- Ensiversion oma tavoite: arkkitehtoninen, luottamusta herättävä
  rakennusalan ulkoasu, palvelut selkeinä kokonaisuuksina, työkuva-
  gallerialle laadukas pohja ja harkittu tarjouspyyntöpolku.
  Yrityksen aitona työnä esitettyjä projektikuvia tai asiakkaiden
  arvosteluja ei saa julkaista uudelleen ilman käyttöoikeutta.
- Alkuperäiset lähteet:
  https://www.rakennuspalvelurili.com/
  https://www.asiakastieto.fi/yritykset/fi/rakennuspalvelu-ri-li-oy/28433123/rekisteritiedot

## Yhteiset toteutus- ja laaturajat

- Kolme **erilaista** brändiä, sivurakennetta, typografista järjestelmää
  ja kuvien art directionia. ÄLÄ kopioi Kotifixin sinistä ulkoasua.
- Tutki jokaisen toimialan 3 laadukasta aitoa vertailusivua ennen designia.
- Ylläpidä erottelu: lähteestä varmistettu fakta / asiakkaalta puuttuva tieto /
  havainnollistava esimerkkisisältö. Älä keksi joukkueita, työntekijöitä,
  asiakasarvosteluja, palvelulupauksia tai kuvattuja referenssejä.
- Käytä ensin maksuttomia local/mock/fixture/browser-testejä. Älä kuluta
  rajallisia ulkoisia AI/API-krediittejä ilman perusteltua tarvetta.
- Jokaisella sivulla luonnollinen suomi, max yksi retorinen
  vastakohtapari koko sivustolla (mieluiten nolla), saavutettavuus,
  nopeat natiivit scrollit, hillitty ja toimiva liike sekä CMS-pohja,
  jota oikea asiakas voi käyttää itse.
- Ennen ensimmäistä omistajalle lähetettyä previewta: käy sisäiset
  korjauskierrokset, mobiili+desktop-laatuportit, riippumaton
  arvio ja oikea painike-/lomake-/navigaatiotestaus läpi.
- Jokaisen valmiin demon arviointilinkki annetaan automaattisesti
  valmistumisvastauksessa. Sisäinen GitHub Pages -osoite ei ole
  asiakkaille lähetettävä myyntilinkki.
- Demo selkeästi merkitty Kaurivon riippumattomaksi konseptiksi,
  ei yrityksen viralliseksi sivustoksi. Asiakkaisiin ei oteta
  yhteyttä eikä domainia osteta ilman erillistä hyväksyntää.
- Kolmen demon tulokset kirjataan erikseen: 1. ensimmäisen sinulle
  näytettävän version laatu, 2. kuinka monta sisäistä korjausta,
  3. liiketoimintafaktat, 4. mobiili/suorituskyky, 5. CMS-handover.
