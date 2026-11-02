# Kaurivo — toimialalähtöinen rakennusputki (2026-11-02)

## Muutetaan järjestelmä, ei yksittäisiä kolmea testiyritystä

TE-Service, Rosanne ja RI-LI ovat **läpäisytestejä**, eivät
kehityksen kovakoodattuja erikoistapauksia. V1-kierros epäonnistui,
koska sama sivupohja värjättiin kolmesti. V2-luonnoksia ei julkaista
myyntiin tai merkitä hyväksytyiksi ennen kuin yleinen prosessi,
sisältöaineisto ja itsenäinen arvio ovat kunnossa.

## Toteutettu yleinen tietovirta

1. **Research ensin.** `utils.industry_workflow.crawl_original_website`
   kerää yrityksen omalta verkkotunnukselta enintään 12 sivun
   lähdeaineiston sekä tunnistaa tärkeät alisivut. Ei Tavily-kutsuja
   eikä uusia AI-ajokertoja tätä vaihetta varten. Tuloksissa on
   jokaisen kerätyn sivun URL, näkyvä teksti, otsikot, kuvat,
   lomakekuvaus sekä headerin ja footerin logokandidaatit.
2. **Rakennus estyy, jos tiedot puuttuvat.** `validate_inventory`
   vaatii alkuperäisen sivuston usean sivun tutkimuksen, jos yrityksellä
   on nykyinen sivusto. Jos tärkeät sivut jäi tutkimatta tai
   tarkastetuissa oli virheitä, käsittely pysähtyy jo ennen
   Builderin AI-kutsua. Puuttuvia faktoja ei keksitä.
3. **Toimialan käyttäjätehtävät ohjaavat art directionia.**
   `sector_guidance` tunnistaa tällä hetkellä autoalan,
   ravintolat, rakennusalan, vähittäiskaupan ja hyvinvoinnin
   yleiset sisällölliset tarpeet sekä käyttää tuntemattomille
   aloille omaa neutraalia lähtökohtaa. Nämä ovat vain
   tutkimus- ja tietovaatimuksia, **ei HTML-, kortti- tai
   sivuasettelumalleja**. Tavoitteena laajentua muihin aloihin
   oikean tutkimuksen perusteella.
4. **Yrityskohtainen brief.** `create_industry_brief` yhdistää
   alkuperäisen sivuston todennetut aineistot,
   toimialan asiakastehtävät ja jo vaaditun kolmen
   saman toimialan vertailusivun analyysin.
   Jokaisen sivuston oman layoutin, kuvat, typografian,
   sisältörytmin ja liiketehosteet suunnittelee Builder
   näiden pohjalta.
5. **Laadun kaksoisportti.** `design_distinctness`
   estää ilmeisen saman HTML-rungon kierrättämisen.
   Sitä seuraa oikea visuaalinen desktop/mobiili-vertailu,
   jonka tulos on tallennettava ja arvosteltava ulkoisesti.
   Samanlaisen näköiset sivut voivat silti läpäistä
   pelkän teknisen DOM-tarkistuksen; tämä ei ole 9/10-todiste.

## Yrityksen oma identiteetti ja tiedot

Käyttäjälle näkyvässä copyssa kerrotaan palveluista suoraan.
Lähdehuomautukset kuuluvat QA-raporttiin ja sisäisen demon
läpinäkyvään erilliseen merkintään, eivät jokaisen
palvelukuvauksen perään. Kaikki tärkeät vanhat sivut,
aito alkuperäinen logo, hyväksytyt värit, yhteystiedot,
hinnat, palvelut, ruokavaliotiedot, referenssit sekä
footerin sponsorit ja kumppanit säilyvät oikeilla rooleilla.
Kuvien oikeuksia ja vanhentuneita yhteistyösuhteita ei arvata.
Keksittyjä 01/02/03-merkintöjä tai samaa neljän kortin
valmista ulkoasua ei käytetä.

## Rajoitukset ja seuraava laatuportti

12 sivun HTTP-tutkimus on rajattu **lähdeotos**, ei takuu
koko sivuston täydellisestä inventaariosta. Monimutkaiset
sivustot, JS-renderöity sisältö ja PDF:t vaativat lisätutkimusta;
näkyvät puutteet ovat estävä merkintä, eivät piilotettava
virhe. Pelkkä logo-URL ei anna oikeutta käyttää kuvaa
asiakkaalle julkisesti. Erillinen hyväksytty sisältö- ja
kuvaomaisuus, kontrastin mittaus, saavutettavuus,
todellinen CMS, yhteydenottojen toimitus ja itsenäinen
9/10-ensiesikatselun vertailu ovat vielä erillisiä portteja.

Tämä prosessi ei saa kuluttaa rajallisia AI/API-krediittejä
paikallisessa validoinnissa. Käytä fixture- ja mock-testejä,
älä oikeiden yritysten API-hakuja testidatassa.
