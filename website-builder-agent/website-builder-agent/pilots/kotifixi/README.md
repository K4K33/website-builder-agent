# Kotifixi × Kaurivo — YKSITYINEN CMS-käyttökoe

**Ei julkista sivustoa, ei muutoksia kotifixi.comiin, ei DNS-muutoksia,
ei automaattista julkaisua, ei myyntiä, ei markkinointiviestejä.**
Tämä on aikaisemman Kotifixi-demon paikallinen koekäyttöpaketti,
ei Kotifixin hyväksymä tai julkaistu asiakassivusto.

## Mitä testataan?

1. Yrittäjä kirjautuu omilla GitHub- ja/tai Pages CMS -oikeuksillaan
   erilliseen, **yksityiseen Kotifixi-testirepositorioon**.
2. Hän avaa tiedoston `content/site.json` Pages CMS:n visuaalisessa
   editorissa ja muokkaa otsikkoa, palvelua, aukioloaikoja, yhteystietoja
   sekä omaa luvallista kuvaa. Mitään ei kopioida Kaurivon asiakasrekisteriin.
3. Muutos tallentuu Git-versionhallintaan. GitHub Pages on POIS PÄÄLTÄ.
   Tämä muokkaus ei julkaise sivustoa internetiin.
4. Kaurivo ajaa tiedostot paikallisesti ja näyttää lopputuloksen omassa
   selaimessa tai yrittäjälle näytönjaon kautta.
5. Yrittäjä tarkistaa, voiko hän muokata ja palauttaa alkuperäisen version
   itse ilman koodia. Muutos testataan uudestaan paikallisesti.
6. Tarkistetaan mobiiliasettelu ja ajetaan Chrome Lighthouse DevToolsilla
   paikallinen **lab-testi**. Tulos on laitekohtainen eikä todellista
   Core Web Vitals / kenttädataa.

Tämä **ei** todista julkisen domain-julkaisun, oikean tuotantohostauksen,
asiakkaan live-lomakkeen tai maksullisen toimituksen toimintaa. Niiden
testaus jää erilliseksi ja asiakkaan suostumuksen varaan.

## 1. Ennen pilottia

- Pyydä yrittäjältä lupa vain *yksityiseen* kokeiluun. Ei erillistä
  domainia, hosting-maksua tai olemassaolevan sivun korvaamista.
- Tarkista, mitkä demon faktat/kuvat/väitteet ovat aitoja: tämä vanha
  demo sisältää ulkoisia Unsplash-kuvia ja keskeneräisiä tekstejä.
  Älä käytä demon tekstiä tai kuvia oikeana Kotifixin hyväksymänä
  markkinointina ilman omistajan tarkistusta.
- Luo uusi PRIVATE GitHub-repository, johon kopioidaan vain tämän
  `pilots/kotifixi/`-kansion sisällöt repositorion juureen.
- Erillisen repositorion omistaja hyväksyy GitHub/Pages CMS -oikeudet
  rajatusti vain tähän uuteen testirepositorioon. Älä anna yrittäjälle
  Kaurivon päärepoa, CRM:ää, API-avaimia tai muita asiakastietoja.
- Älä ota GitHub Pagesia käyttöön äläkä lisää Actions-deploytä tai
  custom-domainia. `.pages.yml` on vain CMS:n EDITOINTIkonfiguraatio.

## 2. Todellinen kirjautumis- ja editorikoe

1. Yrittäjä hyväksyy vain tähän projektiin tarvittavan pääsyn.
2. Avaa <https://app.pagescms.org/> ja kirjaudu.
3. Valitse yksityinen Kotifixi-testirepository ja sisältönäkymä.
4. Muuta esimerkiksi etusivun otsikko väliaikaisesti:
   `KOTIFIXI TESTI — palautetaan ennen loppua`.
5. Muokkaa yhtä palvelua ja yhtä kuvaa (vain oma luvallinen kuva).
6. Tallenna. Tarkista, että yksityisen repositorion
   `content/site.json` ja tarvittaessa `media/` päivittyvät.
7. Palauta muutokset CMS:ssä tai erikseen sovitulla
   Git-versionhallinnan palautuksella. Todista molemmat versiot.
8. Kirjaa kirjautumisen, tallennuksen ja palautuksen tulokset
   yksityiseen hyväksymislomakkeeseen; älä laita tunnuksia tai
   asiakastietoja julkiseen repoosi.

Pages CMS:n omien ohjeiden mukaan visuaalinen editori tallentaa muutokset
GitHub-tiedostoihin eikä itse hoida verkkosivujen julkaisua. Siksi
voimme kokeilla editoria ilman tuotantojulkaisua.

## 3. Paikallinen sivuston esikatselu

Kun testipaketin sisältö on hyväksytysti paikallisessa kansiossa:

```bash
python -m unittest pilot_tests -v
python render_site.py
python -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Avaa saman tietokoneen selaimessa `http://127.0.0.1:8000/`.
Terminaali 1: yllä oleva testinäkymän palvelinkomento.
Terminaali 2: käytä muita testikomentoja.
Älä muuta `--bind 127.0.0.1` muotoon `0.0.0.0` ilman erillistä
suostumusta. Paikallinen linkki ei avaudu yrittäjän puhelimella
toiselta laitteelta; näytä se näytönjaolla tai omalla koneella.

Esikatselusivulla on näkyvä TESTI-banneri ja `noindex,nofollow`.
Huomaa, että **noindex ei ole pääsynhallinta**. Yksityisyys syntyy
siitä, että sivua EI HOSTATA julkisesti.

## 4. Mitä pystymme oikeasti todistamaan?

| Testi | Menetelmä | Status ennen oikeaa koetta |
|---|---|---|
| Oikea omistajan kirjautuminen | Pages CMS + vain testirepon oikeudet | EI TESTATTU |
| Teksti, palvelut, yhteystiedot | tallenna ja renderöi paikallisesti | EI TESTATTU yrittäjänä |
| Kuvan vaihto | oma kuva + testi + palauta | EI TESTATTU yrittäjänä |
| Versiohistoria ja palautus | CMS/Git + toinen paikallinen build | EI TESTATTU |
| Mobiili/selaimet | paikalliset viewport-/selaintestit | EI TESTATTU |
| Nopeus | Chrome Lighthouse localhostille | EI MITATTU |
| Todelliset verkkokävijät | vaatii luvallisen live-sivun | EI VOIDA testata nyt |
| Kotifixin domain-julkaisu | vaatii asiakkaan nimenomaisen luvan | EI TEHDÄ |
| Ensimmäinen maksullinen projekti | todellinen sovittu ja maksettu työ | EI OLE PILOTIN TAVOITE |

**Tärkeää:** Kotifixi-ystäväyrittäjän palaute on arvokas käyttäjäkokemuksen
testi, mutta ei automaattisesti riippumaton alan asiantuntijan hinta-arvio.

## 5. Premium-arvon arviointi ilman julkaisua

Esittele ennen/jälkeen-näkymät ja testiraportit, mutta arvioi
verkkosivuston arvo *toimitussisällön* perusteella. Pyydä toiselta
kokeneelta suunnittelijalta saman yhdenmukaisen arviointilomakkeen
mukainen kirjallinen arvio; älä keksi lausuntoa.

Erillisen arvioinnin pisteet 0–5: brändin säilyminen ja ammattimaisuus,
yrityskohtainen visuaalinen suunnittelu, myyntipolku ja yhteydenotto,
mobiili ja saavutettavuus, tekninen toteutus, SEO-perusta, todellinen
CMS-omistajuus ja asiakasluovutus. Liitä riskit ja puutteet.

Hinnan muodostus: sovitun työmäärän realistiset tunnit × kestävän
yritystoiminnan työtuntikustannus + alustalisenssit ja muut suorat
kulut + korjaus-/takuureservi + kate. Vertaa kolmen **samansisältöisen**
toimiston oikeisiin tarjouksiin (ei markkinointihinnan lähtöluvuksi).
Hinnoittele premium vasta kun laatu ja toteutustapa on osoitettu.
