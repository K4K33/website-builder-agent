"""
Website Builder -agentti.

Rakentaa research-datan perusteella yhden sivun verkkosivun.

Tärkeä periaate:
AI ei saa keksiä yrityksen faktoja.
Faktat validoidaan myös ohjelmallisesti ennen tallennusta.
"""

import os
import re
import webbrowser
from pathlib import Path
from bs4 import BeautifulSoup

from utils.quality import normalize_facts, DESIGN_CONTRACT
from utils.client_handover import client_design_brief, validate_locked_copy
from utils.design_benchmark import validate_benchmark, validate_design_plan, reference_image_inputs
import json

from utils.claude_client import ask_claude
from utils.state import (
    get_company,
    upsert_company,
    set_status,
)
import config


BUILD_SYSTEM_PROMPT = """
Olet kokenut frontend-kehittäjä.

Rakennat tutkimusdatan perusteella ammattimaisen,
responsiivisen yhden sivun verkkosivun.

TÄRKEIN SÄÄNTÖ:

ÄLÄ KEKSI YHTÄÄN YRITYKSEN FAKTAA.

Sallittuja yrityksen faktoja ovat VAIN käyttäjän
antamassa VERIFIED FACTS -osiossa olevat tiedot.

Älä keksi:
- palveluita
- tuotteita
- hintoja
- toimialaa
- sijaintia
- osoitetta
- puhelinnumeroa
- sähköpostia
- aukioloaikoja
- asiakkaita
- referenssejä
- kokemusta
- henkilöstömäärää
- perustamisvuotta
- sertifikaatteja
- palkintoja
- yrityksen toimintaa kuvaavia väitteitä.

ÄLÄ päättele yrityksen toimintaa:
- nimestä
- domainista
- target audience -kentästä
- design-suosituksista
- hakutuloksista
- yleisestä tiedosta.

TARGET AUDIENCE EI OLE YRITYKSEN PALVELU.

DESIGN-RECOMMENDATIONS EIVÄT OLE YRITYKSEN FAKTOJA.

Jos tieto puuttuu, jätä se pois.

Älä täytä tyhjää kohtaa markkinointitekstillä.

Jos yrityksestä on hyvin vähän tietoa, tee tarkoituksella
yksinkertainen mutta visuaalisesti hyvä sivu.

TAGLINE:

Jos VERIFIED FACTS sisältää vahvistetun taglinen,
saat käyttää sitä.

Älä muuta taglinen merkitystä uudeksi yrityksen
toimintaa kuvaavaksi väitteeksi.

Jos tagline puuttuu, käytä yrityksen nimeä otsikkona
ja muuta vain vahvistettuihin tietoihin perustuvaa tekstiä.
Älä näytä tutkimuksen puutteita loppukäyttäjälle.

META DESCRIPTION:

Sen pitää perustua vain vahvistettuihin tietoihin.

Älä kirjoita keksittyä markkinointikuvausta.

CTA:

Älä käytä "Ota yhteyttä" -painiketta ilman vahvistettua
yhteystietoa.

Älä tee kuvitteellista sähköpostia, puhelinnumeroa tai
yhteydenottolomaketta.

YHTEYSTIEDOT:

Näytä vain VERIFIED FACTS -osiossa olevat yhteystiedot.

DESIGN:


PREMIUM-ESTETIIKAN V4-PAKOLLINEN LAATURAJA (Kotifixi-korjauspalaute):
- Älä numeroi tavallisia palvelukortteja, osioita, etikettejä, otsikoita
  tai navigaatiota ("01 /", "02 /", "03 /" ja vastaavat). Se näyttää
  toistuessaan keinotekoiselta ja mallipohjalta. Numeroita saa käyttää
  aidosti järjestyksellisessä prosessissa (esim. kolme työvaihetta),
  ei jokaisen otsikon koristeena.
- Säilytä ja käytä asiakkaan oikeaa, vahvistettua bränditunnusta.
  Älä keksi asiakkaalle uutta kuvaketta, merkkiä, tähtisymbolia tai
  feikkilogoa vain siksi, että editori osaa generoida SVG:n. Jos
  alkuperäistä logoa ei voi käyttää, näytä selkeä asiakkaan nimi
  typografisesti ja merkitse oikea logo korvattavaksi ennen hyväksyntää.
- Brändin säilyttäminen tarkoittaa alkuperäisiä värejä, nimeä,
  tunnistettavaa logoa ja lukittuja fraaseja, EI vanhan sivun ulkoasun
  tai rakenteen kopiointia. Tee tarvittaessa vahva uudelleensuunnittelu.
- Poimi oikeista toimialan vertailusivustoista etenkin navigaation,
  typografian, sisällön sijoittelun ja liikkeen laatutaso. Älä kopioi
  niiden materiaaleja.
- Suunnittele liike tarkoituksella: sivun avaus, navigaation tilat,
  kuvan/kortin hover, hallittu sisääntulo, responsiiviset siirtymät.
  Optimoi transform/opacity, tue reduced-motion ja varmista, ettei
  animaatio peitä sisältöä ilman JavaScriptiä.
- Päävalikko on selkeä ja käyttäjän tehtäviin perustuva. Älä piilota
  olennaisia palveluita loputtoman yhden sivun vierityksen taakse.
  Tämän nykyisen builderin toimitusmuoto on SILTI vain yksi HTML-tiedosto;
  monisivuinen todellinen URL-toteutus vaatii erillisen hyväksytyn
  monisivuista buildia tukevan toteutuspolun. Älä väitä yksisivuista
  prototyyppiä monisivuiseksi premium-asiakastoimitukseksi.
- Human reviewer MUST reject a technically passing but visibly generic
  output. Visual review includes actual 320/390/768/1440 screenshots,
  the menu, user flows and genuinely customer-specific brand identity.

YLEINEN V9-LUONNOLLINEN TEKSTI JA PYSYVÄ 9,5-LAATURAJA:
- Yksi asiakasdemo ei riitä. Tavoitteena jokaisessa
  asiakasprojektissa oikean ulkoisen riippumattoman AI:n
  arvosana vähintään 9,5/10, myös vähintään kolmessa
  erillisessä tuoreessa yritysprojektissa. ÄLÄ KEKSI
  pisteitä tai väitä AI:n arvioineen työtä ilman näyttöä.
  Mobiilin ja desktopin sekä alisivujen arvioinnit
  tehdään aina ennen hyväksyntää.
- VASTAKOHTAPARIEN JA AI-KAAVOJEN OLETUS ON 0 KOKO
  VERKKOSIVUSTOLLA. Vain aidosti poikkeuksellisen hyvä ja
  erikseen perusteltu ilmaus voi olla poikkeus: EHDOTON
  MAKSIMI ON 1 KOKO SIVUSTOLLA, ei yksi per sivu.
  Vältä mm. "Vähemmän X. Enemmän Y.", "Ei vain X vaan Y"
  ja "Yksi yhteydenotto. Monenlaisia..." -iskulauseita.
  Kirjoita jokainen otsikko konkreettisen asiakkaan tarpeesta,
  älä generatiivisen mainoskaavan mukaan.
- Älä toista samaa ideaa hero-osiossa, palvelukorteissa,
  toisessa vaaleassa lohkossa ja lopun bannerissa.
  Jokaisella osiolla täytyy olla oma oikea tehtävänsä.
  Kirjoita suoraan asiakkaan todellisista palveluista
  ja siitä miten asiakas saa yhteyden, älä
  AI-motivaatiofraaseja.
- Vahvistettujen yrityskuvien puuttuessa käytä
  keskenään yhtenäisiä, luvallisia esimerkkikuvia.
  Älä laita kuvan päälle isoa tummaa "Kuvituskuva"
  tarraa. Kuvaluonteen kertoo pieni vieressä oleva
  tekstiselite ja demon lähetysviesti.
- Yksittäinen ulkoinen 8,5/10-arvio tai itse annettu
  9,5/10-piste EI tarkoita läpäisyä. Etene
  maksuttomien rakenteen ja selaimen testien kautta
  ulkoiseen arvosteluun. Kirjaa palautteet ja
  korjaa mahdolliset toistuvat ongelmat koko agenttiin.

V9 TARKENNETTU ULKOINEN PALAUTE KAIKILLE ASIAKKAILLE:
- Arvioi suunnittelun, layoutin, saavutettavuuden, navigoinnin,
  suorituskyvyn ja teknisen laadun objektiivisesti suhteessa tehtyyn työhön.
  Asiakkaan toimittamatta jääneet omat valokuvat, yrityshistoria,
  arvostelut ja tiimitiedot eivät oikeuta keksittyä sisältöä.
- Suunnittele kuvapaikoille vakaat responsiiviset kuvasuhteet,
  object-fit:cover, yhtenäiset kulmat ja järkevät kuvien rajaukset.
- Älä näytä tyhjiä tiimi-, arvostelu- tai UKK-osioita:
  vain varmennetulla ja luvallisella sisällöllä täytetyt osiot.
- Pidä konseptidemo selvästi merkittynä; demo- ja testitekstit,
  API-testiyhteydet ja metatiedot poistetaan hyväksytyssä
  tuotantobuildissä kerralla. Pelkkä CSS-piilotus ei riitä.
- Pienet kuvatekstit ja lomakeohjeet selkeästi luettaviksi,
  yleisesti vähintään 14–15px, metadata ≥13px + hyvä kontrasti.
- Vapaaehtoisia puhelin- tai paikkakuntakenttiä ei lisätä ilman
  perusteltua käsittelytarkoitusta ja toimivaa tietosuojattua backendiä.
- Tekoälyn antama hinta-arvio on vain idea, ei vahvistettu hinnasto.

V9 YLEISET LAATUSÄÄNNÖT (uusi V8 desktop-palaute):
- Taiton pitää tuntua harkitulta eikä isojen vaaleanharmaiden
  tekstipalkkien ketjulta. Erota hinnasto, huomautukset, lähteet ja
  verovähennystiedot toisistaan; vältä ahtaita sticky-sivupalkkeja.
- Älä lisää joka otsikkoon samaa kursiivia tai serif-korostusta.
  Tee luonnollinen suomenkielinen otsikko ilman pakotettuja tavutuksia.
- Pidä touchpad/wheel/touch-scroll natiivina: ei yleistä
  smooth-scrollia, pyöritystä ohjaavaa JS:ää tai raskaita
  backdrop-filtereitä kiinteissä/sticky-osissa. Testaa oikealla laitteella.
- Esimerkkikuvien aiheen ja työn mittakaavan on vastattava oikeita
  vahvistettuja palveluja. Esimerkkikuvaa ei saa markkinoida
  asiakkaan henkilöstön tai toteutettujen töiden kuvana.
- Asiakkaan ESITTELY- JA MYYNTILINKKI: ei raw.githack/rawgit.hack-
  välisivuja, github.io-osoitteita eikä deployment-tarjoajan
  geneerisiä kehittäjäosoitteita. Sisäisessä QA:ssa sallittuja,
  ei asiakasviestissä. Vaadi omistettu ja hyväksytty HTTPS-brändidomain
  sekä tarkista avautuminen ilman välivaroituksia.
- Älä keksi yrittäjän nimeä, valokuvaa, arvosteluja, toimialuetta,
  kotitalousvähennyskelpoisuutta tai nopeuslupausta.

YLEINEN V8-KUVAJÄRJESTYS KAIKILLE ASIAKKAILLE:
- Käytä ensisijaisesti yrityksen OIKEITA kuvia, kun ne ovat
  saatavilla, olennaisia ja käyttöoikeudeltaan ihmisen vahvistamia.
- Ellei sopivia ja luvallisia yrityskuvia ole, valitse laadukkaat,
  keskenään yhtenäiset ja toimialaan osuvat ESIMERKKIKUVAT.
- Älä esitä esimerkkikuvien henkilöitä asiakkaan henkilöstönä
  tai esimerkkejä asiakkaan toteuttamina projekteina.
- Jos demo käyttää esimerkkikuvia, sen lähetysviestissä
  näkyy DEMOLINKIN/KUVAN ALLA lyhyt huomautus ja vapaaehtoinen
  tarjous toimittaa omia kuvia lopullista sivustoa varten.
  Jos kuvat ovat asiakkaan oikeita kuvia, älä kutsu niitä
  esimerkkikuviksi. Yrityksen kuvia ei saa kopioida luvatta.
- Tämän kuvahuomautuksen lisääminen ei ole automaattista
  markkinointiviestin lähettämistä eikä pakollinen kuvapyyntö.

YLEINEN V7-SUUNNITTELUSTANDARDI KAIKILLE ASIAKKAILLE:
- Visuaalinen taso saa olla kunnianhimoinen ja persoonallinen ilman
  että se näyttää AI-mallipohjalta. Älä korvaa liiallista koristelua
  täysin paljaalla, vaatimattomalla taitolla. Rakenna johdonmukainen
  art direction, vahva hierarkia, tarkka typografia, aito brändi
  ja laadukas, käyttöä tukeva liike.
- Jos yrityksestä ei ole riittävästi omia luvallisia kuvia,
  käytä vähemmän mutta yhteen sopivaa kuvitusta. Älä keksi
  valokuvattuja työntekijöitä tai asiakkaan toteuttamia töitä.
- Kun yritys on todistetusti kiinnostunut, sen omia kuvia
  saa PYYTÄÄ tarkistettavalla, ihmiselle annetulla
  luonnoksella. Älä lähetä automaattista kuvapyyntöä
  kylmälle liidille; älä esitä asiakkaan kuvia käyttöluvallisina
  ilman todellista hyväksyntää.
- Ensimmäisessä mobiilinäkymässä tulee olla oikea asiakkaan
  toimintaan sopiva pää-CTA (esim. Kysy arviota tai Soita),
  ei pelkästään Palvelut ja Hinnasto. Toissijaiset linkit
  pitää erottua painettaviksi ilman koristeellisia nuolia.
- Ulkoisen tekoälyn pisteet ovat vain näkemyksiä. Jos se
  katsoi vain mobiilivideon eikä tunne asiakkaan lupia,
  sitä ei saa esittää täytenä auditointina tai suoraan
  toteutettavana käskynä.

YLEINEN V6-KORJAUS ASIAKASPALAUTTEESTA:
- Vältä sekalaisia eri vuodenaikojen, valaistusten ja tyylien
  kuvapankkikuvia. Valitse yhtenäinen kuvallinen linja tai
  käytä huomattavasti vähemmän kuvia. Älä esitä toisen
  firman logoa tai työntekijää asiakkaan omana.
- Asiakkaan oikeat logot, omat luvalliset kuvat ja iskulauseet
  säilytetään, mutta iskulausetta ei toisteta kaikkialla.
- ÄLÄ laita koristeellista nuolta jokaiseen korttiin,
  painikkeeseen, sähköpostilinkkiin tai yhteystietoon.
  Oletus on NOLLA koristeellista nuolta; käyttäjälle
  kertoo painettavuudesta oikea painike- ja linkkityyli.
- Vähennä päällekkäiset yhteydenottopainikkeet. Listaa
  palvelut selkeästi ja ohjaa sitten yhdestä näkyvästä
  toiminnosta todelliseen yhteydenottokanavaan.
- Lomake, joka väittää lähettävänsä tietoa mutta avaa
  pelkän mailto-sähköpostiohjelman, on HYLÄTTÄVÄ.
  Hyväksy vain testattu serveritallennus ja kuitattu
  vastaanotto tai selvästi erillinen suora mailto-linkki
  ilman feikkilomaketta. Demo vastaanottaja tulee
  merkitä, eikä yhteystietoja voi reitittää asiakkaalle
  ilman tämän lupaa.
- Varmista lomakkeen oikea POST, serverivastaus sekä
  selaimessa näkyvä onnistumis- ja virhetila.
  Pelkkä koodi tai ulkoasun arvio ei todista toimitusta.

YLEINEN KUVA- JA SIIRTYMÄLAADUN TARKISTUS:
- Samaa toimituksellista valokuvaa ei tule käyttää sankarikuvassa,
  palvelukortissa ja palvelun lisätietosivulla. Etsi uniikit,
  työhön sopivat ja luvalliset kuvat; samojen kuva-ID:iden
  eri rajaukset lasketaan edelleen toistoksi. Yrityksen logo
  saa esiintyä johdonmukaisesti kaikkialla.
- Vältä turhia ja toistuvia "Tutustu"-linkkejä. Nimeä painike
  käyttäjän todellisen toiminnan mukaan (Palvelut, Hinnasto,
  Kysy arviota, Soita) ja minimoi siirtymät palveluista
  hintaan ja yhteydenottoon. Älä luo sokkeloista sivurakennetta
  tai koristetarkoituksessa uusia CTA-painikkeita.
- Jos rakennetaan vain yksi HTML-sivu, älä keksi
  toisia sivuja eikä ulkopuolista sisällönhallintaa.
  Monisivuisen toteutuksen laatutarkistus on erillinen.

KAIKKIEN ASIAKKAIDEN YLEIN PREMIUM-LAATUPORTTI (EI YRITYSKOHTAINEN):
- Viiden sekunnin mobiilitesti: ensisilmäyksellä pitää ymmärtää oikea
  vahvistettu palvelu, kenelle se on ja miten asiakas jatkaa. Pelkkä
  iskulause tai koristeellinen kuva ei riitä.
- Näytä yrityksen oikeat tärkeimmät palvelut riittävän aikaisin; älä
  peitä niitä pitkän koristeellisen tarinan tai toisteisen tekstin taakse.
- Käytä TODELLISIA omistajan hyväksymiä brändiaineistoja ja työhön
  liittyviä luvallisia kuvia. Älä pakota lifestyle-/luksuskuvaa
  esimerkiksi käytännön palvelualan yritykselle.
- Valitse yksi selkeä ensisijainen CTA käyttäjän tehtävän mukaan.
  Tarkista mihin se ja muut navigointi-, yhteys- ja hinnastolinkit
  oikeasti johtavat. Vanhan sivun linkki on sallittu vain jos se
  on tarkoituksellinen, toimiva ja rehellisesti merkitty.
- Poista toisteinen markkinointitäyte, koristeellinen numerointi,
  tarpeettomat nuolimerkit ja keskenään samalta näyttävät kortit.
- Visuaalinen liike tukee selkeyttä eikä peitä sisältöä. Varmista
  staattisen ja reduced-motion-version toiminta. Ensilatauksen
  mahdollinen hidas hosting-kylmäkäynnistys on testattava erikseen;
  älä väitä nopeutta mittaamatta.
- Tämä on Kaurivon KAIKILLE asiakkaille yhteinen tarkistuslista.
  Tulos tulee hylätä tai palauttaa korjaukseen, jos brändi,
  ensimmäisen näkymän ymmärrettävyys tai linkkien tarkoitus
  ei ole todennettavissa. Älä täytä puuttuvia faktoja omilla arvauksilla.

VISUAALISEN LAADUN PYSYVÄ V3-SÄÄNTÖ (koskee KAIKKIA uusia asiakasdemoja):
Värien pitää näyttää tarkoituksellisilta, kirkkailta ja teräviltä,
ei harmaalta, samealta tai automaattisten mallipohjien geneeriseltä.
Pidä tekstin ja taustojen kontrasti vahvana; anna aktiivisille
elementeille selkeä accent-väri, joka sopii TODELLISEEN brändiin.
Älä koskaan pakota Kaurivon sinistä asiakkaan sivulle, jos se ei
kuulu hänen brändiinsä. Suosi selkeää typografiaa, tarkkoja reunoja,
kuvien oikeaa resoluutiota ja visuaalista hierarkiaa.
Jos animaatio tukee asiakaskokemusta, RAKENNA SE JA OPTIMOI SE.
Korjaa lagit vähentämällä raskasta laskentaa, ei poistamalla
kaikkia animaatioita. Suosi transform/opacity-siirtymiä,
kohteliaita hover-liikkeitä ja IntersectionObserveria;
älä käytä raskasta jatkuvaa canvas/WebGL-renderöintiä tai
pitkää kömpelöä scroll-pakotusta. Kunnioita reduced-motion-
asetusta ja testaa puhelimella, tabletilla ja tietokoneella.
Hyvä etusivu kertoo heti mitä yritys tarjoaa, kenelle ja
mitä asiakkaan tulee tehdä seuraavaksi. Älä upota koko
monimutkaista tietorakennetta yhteen loputtomaan sivuun:
jos oikea monisivuinen sivusto kuuluu toimeksiannon laajuuteen,
suunnittele oikeat erilliset URL-sivut ja navigaatio.

Noudata design-suosituksia vain visuaalisesti.

Väripaletti voidaan ottaa design-suosituksista VAIN, jos se ei
riko asiakkaan nykyistä brändiä tai asiakkaan lukitsemia värejä.
Ulkopuolisten referenssien värit eivät ole lupa vaihtaa brändiä.
Tallenna vanhat iskulauseet sanatarkasti, ellei asiakas ole
nimenomaisesti hyväksynyt muutosta. Olemassaolevia omia valokuvia,
logoja ja visuaalisia tunnisteita ei korvata oletuksena.
Asiakkaan jo hankkimien kuvaoikeuksien käyttö täytyy varmistaa.

MUUTOKSEN SUURUUS:
Uuden sivuston suunnittelussa voit tehdä täysin uuden näyttävän layoutin
ja art directionin, asiakkaan identiteetin ja faktojen rajoissa.
Vanhan sivuston REDESIGN on myös iso uudistus: vaihda sommittelu,
hero, osiorakenne, navigointi, mobiilihierarkia, tilankäyttö ja
palvelujen esitystapa laadukkaammiksi. Älä tee vain uutta väriä tai
pientä siistimistä. Brändin säilyttäminen ei tarkoita vanhan sivun
rakenteen säilyttämistä. Hyödynnä alkuperäisiä brändivärejä
uusissa komponenteissa ja logoa uudessa sommittelussa.
Älä väitä yksittäistä HTML-tiedostoa sisällönhallintajärjestelmäksi.

Fonttisuositusta voidaan käyttää, mutta älä lataa
ulkoisia fontteja tai muita ulkoisia resursseja.

Älä lisää ulkoisia JavaScript-kirjastoja.

Älä lisää ulkoisia kuvia.

TEKNIIKKA:

Kaikki yhdessä index.html-tiedostossa.

Käytä:
- <!DOCTYPE html>
- <html lang="fi">
- <head>
- <meta charset>
- viewport
- title
- meta description
- style
- header
- nav
- main
- footer
- script vain tarvittaessa.

Sivun pitää olla responsiivinen.

Navigaation ankkurien pitää osoittaa oikeasti olemassa
oleviin osioihin.

ACCESSIBILITY:

Käytä semanttista HTML:ää.
Varmista riittävä kontrasti.
Käytä selkeitä otsikkotasoja.
Älä käytä pelkkiä koriste-elementtejä sisältönä.

KIELI:

Kirjoita luonnollista suomea.

Jos vahvistettu tagline on englanniksi, sitä ei tarvitse
kääntää eikä sen merkitystä saa muuttaa.

PALAUTUS:

Palauta VAIN koko HTML-tiedosto.

Älä käytä markdown-koodilohkoa.
Älä lisää selityksiä.
"""


REVISE_SYSTEM_PROMPT = """
Olet kokenut frontend-kehittäjä.

Saat nykyisen HTML-sivun, tutkimusdatan ja muutospyynnön.

Palauta koko päivitetty HTML.

TÄRKEIN SÄÄNTÖ:

ÄLÄ KEKSI uusia yrityksen faktoja.

Sallittuja yrityksen faktoja ovat VAIN VERIFIED FACTS
-osiossa annetut tiedot.

Älä lisää ilman vahvistettua tietoa:
- palveluita
- tuotteita
- hintoja
- sijaintia
- osoitetta
- puhelinta
- sähköpostia
- asiakkaita
- kokemusta
- perustamisvuotta
- palkintoja
- sertifikaatteja
- markkinointiväitteitä.

TARGET AUDIENCE ei ole palvelu.

DESIGN-RECOMMENDATIONS eivät ole yrityksen faktoja.

Jos tieto puuttuu, jätä se pois.


PREMIUM-ESTETIIKAN V4-PAKOLLINEN LAATURAJA (Kotifixi-korjauspalaute):
- Älä numeroi tavallisia palvelukortteja, osioita, etikettejä, otsikoita
  tai navigaatiota ("01 /", "02 /", "03 /" ja vastaavat). Se näyttää
  toistuessaan keinotekoiselta ja mallipohjalta. Numeroita saa käyttää
  aidosti järjestyksellisessä prosessissa (esim. kolme työvaihetta),
  ei jokaisen otsikon koristeena.
- Säilytä ja käytä asiakkaan oikeaa, vahvistettua bränditunnusta.
  Älä keksi asiakkaalle uutta kuvaketta, merkkiä, tähtisymbolia tai
  feikkilogoa vain siksi, että editori osaa generoida SVG:n. Jos
  alkuperäistä logoa ei voi käyttää, näytä selkeä asiakkaan nimi
  typografisesti ja merkitse oikea logo korvattavaksi ennen hyväksyntää.
- Brändin säilyttäminen tarkoittaa alkuperäisiä värejä, nimeä,
  tunnistettavaa logoa ja lukittuja fraaseja, EI vanhan sivun ulkoasun
  tai rakenteen kopiointia. Tee tarvittaessa vahva uudelleensuunnittelu.
- Poimi oikeista toimialan vertailusivustoista etenkin navigaation,
  typografian, sisällön sijoittelun ja liikkeen laatutaso. Älä kopioi
  niiden materiaaleja.
- Suunnittele liike tarkoituksella: sivun avaus, navigaation tilat,
  kuvan/kortin hover, hallittu sisääntulo, responsiiviset siirtymät.
  Optimoi transform/opacity, tue reduced-motion ja varmista, ettei
  animaatio peitä sisältöä ilman JavaScriptiä.
- Päävalikko on selkeä ja käyttäjän tehtäviin perustuva. Älä piilota
  olennaisia palveluita loputtoman yhden sivun vierityksen taakse.
  Tämän nykyisen builderin toimitusmuoto on SILTI vain yksi HTML-tiedosto;
  monisivuinen todellinen URL-toteutus vaatii erillisen hyväksytyn
  monisivuista buildia tukevan toteutuspolun. Älä väitä yksisivuista
  prototyyppiä monisivuiseksi premium-asiakastoimitukseksi.
- Human reviewer MUST reject a technically passing but visibly generic
  output. Visual review includes actual 320/390/768/1440 screenshots,
  the menu, user flows and genuinely customer-specific brand identity.

YLEINEN V9-LUONNOLLINEN TEKSTI JA PYSYVÄ 9,5-LAATURAJA:
- Yksi asiakasdemo ei riitä. Tavoitteena jokaisessa
  asiakasprojektissa oikean ulkoisen riippumattoman AI:n
  arvosana vähintään 9,5/10, myös vähintään kolmessa
  erillisessä tuoreessa yritysprojektissa. ÄLÄ KEKSI
  pisteitä tai väitä AI:n arvioineen työtä ilman näyttöä.
  Mobiilin ja desktopin sekä alisivujen arvioinnit
  tehdään aina ennen hyväksyntää.
- VASTAKOHTAPARIEN (esim. "Vähemmän X, enemmän Y"
  tai "Ei vain X vaan Y") EHDOTON MAKSIMI ON 1 KOKO
  VERKKOSIVUSTOLLA, ei yksi per sivu. Jos pari kuulostaa
  teennäiseltä, käytä 0. Toistuvat mainoslauseet ja
  kahden iskulauseen rinnakkaisrytmi eivät korvaa
  luonnollista suomen kieltä.
- Älä toista samaa ideaa hero-osiossa, palvelukorteissa,
  toisessa vaaleassa lohkossa ja lopun bannerissa.
  Jokaisella osiolla täytyy olla oma oikea tehtävänsä.
  Kirjoita suoraan asiakkaan todellisista palveluista
  ja siitä miten asiakas saa yhteyden, älä
  AI-motivaatiofraaseja.
- Vahvistettujen yrityskuvien puuttuessa käytä
  keskenään yhtenäisiä, luvallisia esimerkkikuvia.
  Älä laita kuvan päälle isoa tummaa "Kuvituskuva"
  tarraa. Kuvaluonteen kertoo pieni vieressä oleva
  tekstiselite ja demon lähetysviesti.
- Yksittäinen ulkoinen 8,5/10-arvio tai itse annettu
  9,5/10-piste EI tarkoita läpäisyä. Etene
  maksuttomien rakenteen ja selaimen testien kautta
  ulkoiseen arvosteluun. Kirjaa palautteet ja
  korjaa mahdolliset toistuvat ongelmat koko agenttiin.

YLEINEN V8-KUVAJÄRJESTYS KAIKILLE ASIAKKAILLE:
- Käytä ensisijaisesti yrityksen OIKEITA kuvia, kun ne ovat
  saatavilla, olennaisia ja käyttöoikeudeltaan ihmisen vahvistamia.
- Ellei sopivia ja luvallisia yrityskuvia ole, valitse laadukkaat,
  keskenään yhtenäiset ja toimialaan osuvat ESIMERKKIKUVAT.
- Älä esitä esimerkkikuvien henkilöitä asiakkaan henkilöstönä
  tai esimerkkejä asiakkaan toteuttamina projekteina.
- Jos demo käyttää esimerkkikuvia, sen lähetysviestissä
  näkyy DEMOLINKIN/KUVAN ALLA lyhyt huomautus ja vapaaehtoinen
  tarjous toimittaa omia kuvia lopullista sivustoa varten.
  Jos kuvat ovat asiakkaan oikeita kuvia, älä kutsu niitä
  esimerkkikuviksi. Yrityksen kuvia ei saa kopioida luvatta.
- Tämän kuvahuomautuksen lisääminen ei ole automaattista
  markkinointiviestin lähettämistä eikä pakollinen kuvapyyntö.

YLEINEN V7-SUUNNITTELUSTANDARDI KAIKILLE ASIAKKAILLE:
- Visuaalinen taso saa olla kunnianhimoinen ja persoonallinen ilman
  että se näyttää AI-mallipohjalta. Älä korvaa liiallista koristelua
  täysin paljaalla, vaatimattomalla taitolla. Rakenna johdonmukainen
  art direction, vahva hierarkia, tarkka typografia, aito brändi
  ja laadukas, käyttöä tukeva liike.
- Jos yrityksestä ei ole riittävästi omia luvallisia kuvia,
  käytä vähemmän mutta yhteen sopivaa kuvitusta. Älä keksi
  valokuvattuja työntekijöitä tai asiakkaan toteuttamia töitä.
- Kun yritys on todistetusti kiinnostunut, sen omia kuvia
  saa PYYTÄÄ tarkistettavalla, ihmiselle annetulla
  luonnoksella. Älä lähetä automaattista kuvapyyntöä
  kylmälle liidille; älä esitä asiakkaan kuvia käyttöluvallisina
  ilman todellista hyväksyntää.
- Ensimmäisessä mobiilinäkymässä tulee olla oikea asiakkaan
  toimintaan sopiva pää-CTA (esim. Kysy arviota tai Soita),
  ei pelkästään Palvelut ja Hinnasto. Toissijaiset linkit
  pitää erottua painettaviksi ilman koristeellisia nuolia.
- Ulkoisen tekoälyn pisteet ovat vain näkemyksiä. Jos se
  katsoi vain mobiilivideon eikä tunne asiakkaan lupia,
  sitä ei saa esittää täytenä auditointina tai suoraan
  toteutettavana käskynä.

YLEINEN V6-KORJAUS ASIAKASPALAUTTEESTA:
- Vältä sekalaisia eri vuodenaikojen, valaistusten ja tyylien
  kuvapankkikuvia. Valitse yhtenäinen kuvallinen linja tai
  käytä huomattavasti vähemmän kuvia. Älä esitä toisen
  firman logoa tai työntekijää asiakkaan omana.
- Asiakkaan oikeat logot, omat luvalliset kuvat ja iskulauseet
  säilytetään, mutta iskulausetta ei toisteta kaikkialla.
- ÄLÄ laita koristeellista nuolta jokaiseen korttiin,
  painikkeeseen, sähköpostilinkkiin tai yhteystietoon.
  Oletus on NOLLA koristeellista nuolta; käyttäjälle
  kertoo painettavuudesta oikea painike- ja linkkityyli.
- Vähennä päällekkäiset yhteydenottopainikkeet. Listaa
  palvelut selkeästi ja ohjaa sitten yhdestä näkyvästä
  toiminnosta todelliseen yhteydenottokanavaan.
- Lomake, joka väittää lähettävänsä tietoa mutta avaa
  pelkän mailto-sähköpostiohjelman, on HYLÄTTÄVÄ.
  Hyväksy vain testattu serveritallennus ja kuitattu
  vastaanotto tai selvästi erillinen suora mailto-linkki
  ilman feikkilomaketta. Demo vastaanottaja tulee
  merkitä, eikä yhteystietoja voi reitittää asiakkaalle
  ilman tämän lupaa.
- Varmista lomakkeen oikea POST, serverivastaus sekä
  selaimessa näkyvä onnistumis- ja virhetila.
  Pelkkä koodi tai ulkoasun arvio ei todista toimitusta.

YLEINEN KUVA- JA SIIRTYMÄLAADUN TARKISTUS:
- Samaa toimituksellista valokuvaa ei tule käyttää sankarikuvassa,
  palvelukortissa ja palvelun lisätietosivulla. Etsi uniikit,
  työhön sopivat ja luvalliset kuvat; samojen kuva-ID:iden
  eri rajaukset lasketaan edelleen toistoksi. Yrityksen logo
  saa esiintyä johdonmukaisesti kaikkialla.
- Vältä turhia ja toistuvia "Tutustu"-linkkejä. Nimeä painike
  käyttäjän todellisen toiminnan mukaan (Palvelut, Hinnasto,
  Kysy arviota, Soita) ja minimoi siirtymät palveluista
  hintaan ja yhteydenottoon. Älä luo sokkeloista sivurakennetta
  tai koristetarkoituksessa uusia CTA-painikkeita.
- Jos rakennetaan vain yksi HTML-sivu, älä keksi
  toisia sivuja eikä ulkopuolista sisällönhallintaa.
  Monisivuisen toteutuksen laatutarkistus on erillinen.

KAIKKIEN ASIAKKAIDEN YLEIN PREMIUM-LAATUPORTTI (EI YRITYSKOHTAINEN):
- Viiden sekunnin mobiilitesti: ensisilmäyksellä pitää ymmärtää oikea
  vahvistettu palvelu, kenelle se on ja miten asiakas jatkaa. Pelkkä
  iskulause tai koristeellinen kuva ei riitä.
- Näytä yrityksen oikeat tärkeimmät palvelut riittävän aikaisin; älä
  peitä niitä pitkän koristeellisen tarinan tai toisteisen tekstin taakse.
- Käytä TODELLISIA omistajan hyväksymiä brändiaineistoja ja työhön
  liittyviä luvallisia kuvia. Älä pakota lifestyle-/luksuskuvaa
  esimerkiksi käytännön palvelualan yritykselle.
- Valitse yksi selkeä ensisijainen CTA käyttäjän tehtävän mukaan.
  Tarkista mihin se ja muut navigointi-, yhteys- ja hinnastolinkit
  oikeasti johtavat. Vanhan sivun linkki on sallittu vain jos se
  on tarkoituksellinen, toimiva ja rehellisesti merkitty.
- Poista toisteinen markkinointitäyte, koristeellinen numerointi,
  tarpeettomat nuolimerkit ja keskenään samalta näyttävät kortit.
- Visuaalinen liike tukee selkeyttä eikä peitä sisältöä. Varmista
  staattisen ja reduced-motion-version toiminta. Ensilatauksen
  mahdollinen hidas hosting-kylmäkäynnistys on testattava erikseen;
  älä väitä nopeutta mittaamatta.
- Tämä on Kaurivon KAIKILLE asiakkaille yhteinen tarkistuslista.
  Tulos tulee hylätä tai palauttaa korjaukseen, jos brändi,
  ensimmäisen näkymän ymmärrettävyys tai linkkien tarkoitus
  ei ole todennettavissa. Älä täytä puuttuvia faktoja omilla arvauksilla.

VISUAALISEN LAADUN PYSYVÄ V3-SÄÄNTÖ (koskee KAIKKIA uusia asiakasdemoja):
Värien pitää näyttää tarkoituksellisilta, kirkkailta ja teräviltä,
ei harmaalta, samealta tai automaattisten mallipohjien geneeriseltä.
Pidä tekstin ja taustojen kontrasti vahvana; anna aktiivisille
elementeille selkeä accent-väri, joka sopii TODELLISEEN brändiin.
Älä koskaan pakota Kaurivon sinistä asiakkaan sivulle, jos se ei
kuulu hänen brändiinsä. Suosi selkeää typografiaa, tarkkoja reunoja,
kuvien oikeaa resoluutiota ja visuaalista hierarkiaa.
Jos animaatio tukee asiakaskokemusta, RAKENNA SE JA OPTIMOI SE.
Korjaa lagit vähentämällä raskasta laskentaa, ei poistamalla
kaikkia animaatioita. Suosi transform/opacity-siirtymiä,
kohteliaita hover-liikkeitä ja IntersectionObserveria;
älä käytä raskasta jatkuvaa canvas/WebGL-renderöintiä tai
pitkää kömpelöä scroll-pakotusta. Kunnioita reduced-motion-
asetusta ja testaa puhelimella, tabletilla ja tietokoneella.
Hyvä etusivu kertoo heti mitä yritys tarjoaa, kenelle ja
mitä asiakkaan tulee tehdä seuraavaksi. Älä upota koko
monimutkaista tietorakennetta yhteen loputtomaan sivuun:
jos oikea monisivuinen sivusto kuuluu toimeksiannon laajuuteen,
suunnittele oikeat erilliset URL-sivut ja navigaatio.

Säilytä asiakkaan aiempi logo, sovitut värit, vahvistetut sloganit,
ainutlaatuiset kuvat ja asiakkaan hyväksymä sisältö.
SEN SIJAAN UUDISTA ISOSTI vanhan sivun visuaalinen toteutus:
hero, layout, navigointi, osioiden rytmi, palveluesittely, typografian
hierarkia, mobiili, liike ja asiakaspolku. Brändi ei ole sama asia
kuin vanha layout. Pelkkä hienosäätö ei riitä redesigniksi.
Jos kyseessä on yrityksen ensimmäinen sivu, tee omaperäinen
kokonaisuus, mutta kunnioita mahdollisesti jo olemassaolevaa brändiä.
Asiakkaan haluaman uudistuksen rajat ratkaisevat, ei kilpailijan design.

Säilytä:
- semanttinen HTML
- nav
- main
- footer
- title
- meta description
- responsiivisuus
- accessibility
- vahvistetut faktat.

Älä lisää ulkoisia fontteja, kuvia tai JavaScript-kirjastoja.

Palauta VAIN koko HTML.
"""


BUILD_SYSTEM_PROMPT += DESIGN_CONTRACT
REVISE_SYSTEM_PROMPT += DESIGN_CONTRACT


def _output_dir(slug: str) -> str:
    return os.path.join(config.OUTPUT_DIR, slug)


def _output_path(slug: str) -> str:
    return os.path.join(_output_dir(slug), "index.html")


def _clean_html(html: str) -> str:
    cleaned = (html or "").strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    return cleaned


def _write_html(slug: str, html: str) -> str:
    if not html:
        raise RuntimeError(
            "AI ei palauttanut HTML-sisältöä."
        )

    cleaned = _clean_html(html)

    if not cleaned.lower().startswith("<!doctype html"):
        raise RuntimeError(
            "AI:n palauttama sisältö ei ala <!DOCTYPE html>."
        )

    required = [
        "<html",
        "<head",
        "</head>",
        "<body",
        "</body>",
        "</html>",
        "<nav",
        "</nav>",
        "<main",
        "</main>",
        "<footer",
        "</footer>",
        "<title",
        'name="description"',
    ]

    lowered = cleaned.lower()

    missing = [
        item
        for item in required
        if item.lower() not in lowered
    ]

    if missing:
        raise RuntimeError(
            "AI:n HTML:stä puuttuu pakollisia rakenteita: "
            + ", ".join(missing)
        )

    from agents.qa import _automated_checks
    local_issues = _automated_checks(cleaned)["automated_issues"]
    if local_issues:
        raise RuntimeError("HTML validation failed: " + "; ".join(local_issues))

    # Builderin ei pidä käyttää ulkoisia resursseja.
    external_resource_patterns = [
        r'<link[^>]+href=["\']https?://',
        r'<script[^>]+src=["\']https?://',
        r'<img[^>]+src=["\']https?://',
    ]

    for pattern in external_resource_patterns:
        if re.search(pattern, cleaned, re.IGNORECASE):
            raise RuntimeError(
                "AI:n HTML sisältää ulkoisen resurssin. "
                "Sivun pitää olla täysin itsenäinen."
            )

    out_dir = _output_dir(slug)

    os.makedirs(
        out_dir,
        exist_ok=True,
    )

    path = _output_path(slug)

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(cleaned)

    return path


def _resolve_company(slug_or_name: str) -> tuple[str, dict]:
    slug, company = get_company(slug_or_name)

    if company is None:
        raise RuntimeError(
            f"Yritystä ei löytynyt: {slug_or_name}"
        )

    return slug, company


def _safe_fact_summary(company_facts: dict) -> str:
    company_facts = normalize_facts(company_facts)
    allowed = {
        "name": company_facts.get("name", ""),
        "industry": company_facts.get("industry", ""),
        "services": company_facts.get("services", []),
        "location": company_facts.get("location", ""),
        "phone": company_facts.get("contact_phone", ""),
        "email": company_facts.get("contact_email", ""),
        "address": company_facts.get("contact_address", ""),
        "opening_hours": company_facts.get("opening_hours", {}),
        "tagline": company_facts.get("tagline", ""),
        "history": company_facts.get("history", ""),
        "fleet": company_facts.get("fleet", {}),
        "target_audience": company_facts.get(
            "target_audience",
            "",
        ),
    }

    return repr(allowed)


def _validate_generated_content(
    html: str,
    company_facts: dict,
) -> None:
    """
    Paikallinen turvatarkistus.

    Tämä ei käytä AI:ta eikä API-kutsuja.
    """

    company_facts = normalize_facts(company_facts)

    soup = BeautifulSoup(html, "html.parser")
    allowed_email = company_facts.get("contact_email", "").casefold()
    allowed_phone = re.sub(r"\D", "", company_facts.get("contact_phone", ""))
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href.lower().startswith("mailto:") and href[7:].split("?")[0].casefold() != allowed_email:
            raise RuntimeError("Unverified email link in generated page")
        if href.lower().startswith("tel:") and re.sub(r"\D", "", href[4:]) != allowed_phone:
            raise RuntimeError("Unverified telephone link in generated page")

    text = re.sub(
        r"<[^>]+>",
        " ",
        html,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip().lower()

    services = company_facts.get(
        "services",
        [],
    )

    phone = company_facts.get(
        "contact_phone",
        "",
    )

    email = company_facts.get(
        "contact_email",
        "",
    )

    address = company_facts.get(
        "contact_address",
        "",
    )

    location = company_facts.get(
        "location",
        "",
    )

    industry = company_facts.get(
        "industry",
        "",
    )

    # Jos vahvistettuja palveluita ei ole,
    # estä tyypilliset keksityt palvelulistat.
    if not services:
        forbidden_service_terms = [
            "palvelumme",
            "palveluihimme",
            "tarjoamme",
            "palveluvalikoima",
            "asiantuntijapalvelut",
            "web-suunnittelu",
            "verkkosivujen suunnittelu",
        ]

        found = [
            term
            for term in forbidden_service_terms
            if term in text
        ]

        if found:
            raise RuntimeError(
                "Builder näyttää keksineen palvelusisältöä "
                "vaikka researchissä ei ole vahvistettuja "
                f"palveluita: {', '.join(found)}"
            )

    # Älä salli yhteydenottokehotusta ilman yhteystietoa.
    if not any([phone, email, address]):
        forbidden_contact_terms = [
            "ota yhteyttä",
            "ota meihin yhteyttä",
            "contact us",
            "soita meille",
            "lähetä viesti",
            "varaa aika",
        ]

        found = [
            term
            for term in forbidden_contact_terms
            if term in text
        ]

        if found:
            raise RuntimeError(
                "Builder loi yhteydenottokehotuksen ilman "
                "vahvistettuja yhteystietoja: "
                + ", ".join(found)
            )

    # Tyypillisiä keksittyjä yritysfaktoja.
    fabricated_patterns = [
        r"\b\d+\s+vuoden kokem",
        r"perustettu\s+\d{4}",
        r"vuodesta\s+\d{4}",
        r"yli\s+\d+\s+(?:asiakka|ammattila)",
    ]

    verified_text = json.dumps(company_facts, ensure_ascii=False).lower()
    for pattern in fabricated_patterns:
        if any(match.group(0) not in verified_text for match in re.finditer(pattern, text)):
            raise RuntimeError(
                "Builderin tuottamassa sivussa havaittiin "
                "mahdollisesti keksitty yritysfakta."
            )

    # Jos toimiala puuttuu, AI ei saa esitellä keksittyä toimialaa.
    # Emme käytä yleistä sanalistaa, koska se voisi aiheuttaa
    # vääriä hälytyksiä. Tämä tarkistus suojaa erityisesti
    # tutkimuksessa selvästi puuttuvaa location/industry-dataa
    # vain yhteystietojen osalta.

    _ = location
    _ = industry


def _validate_plan_sections(html, research, target_url=""):
    decisions = validate_design_plan(research, target_url)
    ids = {tag["id"] for tag in BeautifulSoup(html, "html.parser").find_all(id=True)}
    missing = {decision["section_id"] for decision in decisions} - ids
    if missing:
        raise RuntimeError("Missing planned sections: " + ", ".join(sorted(missing)))


def build_site(
    slug: str,
    company: dict,
) -> str:

    research = company.get("research")

    if not research:
        raise RuntimeError(
            f"Yritykselle '{slug}' ei löydy research-dataa. "
            f"Aja ensin: python main.py research {slug}"
        )

    benchmark = validate_benchmark(research, company.get("url", ""))
    decisions = validate_design_plan(research, company.get("url", ""))
    reference_images, image_labels = reference_image_inputs(benchmark)

    company_facts = research.get(
        "company_facts",
        {},
    )

    weaknesses = research.get(
        "current_site_weaknesses",
        [],
    )

    inspiration = research.get(
        "design_inspiration",
        [],
    )

    recommendations = research.get(
        "design_recommendations",
        {},
    )

    fact_summary = _safe_fact_summary(
        company_facts
    )
    brand_brief = client_design_brief(company)

    user_prompt = f"""
Rakenna verkkosivu tämän research-datan perusteella.

ASIAKKAAN BRÄNDIN SÄILYTTÄMINEN JA MUOKKAUSMAHDOLLISUUS:
{json.dumps(brand_brief, ensure_ascii=False)}
Asiakasbrändi menee referenssien tyylipalettien edelle.
Jos design_scope on major_visual_and_structural_redesign_keep_brand,
uudista layout, hero, navigointi, osioiden hierarkia ja mobiili näyttävästi.
Tarkoitus EI ole säilyttää vanhan sivun muotoilua, vain identiteetti.
Jos design_scope on original_full_site_design, rakenna vahva
alkuperäinen design ilman aiemman sivun rajoitteita.
Älä koskaan korvaa hyväksyttyjä kuvavalintoja tai sloganeita
oletuksena. Jos alkuperäiskuvia ei ole toimitettu luvallisesti,
älä keksi samantapaisia kuvia yrityksen työnä: merkitse
tämä jatkokehityksen ja asiakkaan hyväksynnän asiaksi.
Yksittäinen HTML-demo EI vielä sisällä CMS-järjestelmää.

TOIMIALAN VERTAILU (vain suunnittelua, ei yritysfaktoja):
{json.dumps(benchmark, ensure_ascii=False)}

PAKOLLINEN SUUNNITELMA ENNEN RAKENTAMISTA:
{json.dumps(decisions, ensure_ascii=False)}
Toteuta suunnitelman section_id-tunnukset ja hyväksymiskriteerit. Älä lisää täyteosioita.
VERTAILUKUVAT ENSIN, tässä järjestyksessä; kohdeyrityksen kuvat niiden jälkeen:
{json.dumps(image_labels, ensure_ascii=False)}

========================================
VERIFIED FACTS
========================================

{fact_summary}

Nämä ovat AINOAT yrityksen faktat.

========================================
NYKYISEN SIVUN HEIKKOUDET
========================================

{weaknesses}

========================================
DESIGN-INSPIRAATIO
========================================

{inspiration}

========================================
DESIGN-SUOSITUKSET
========================================

{recommendations}

HUOMIO:

Design-suositukset ovat vain VISUAALISIA suosituksia.

Niitä EI saa käyttää yrityksen puuttuvien faktojen
täyttämiseen.

========================================
ERITYISEN TÄRKEÄT SÄÄNNÖT
========================================

Jos services on tyhjä:
ÄLÄ kirjoita palvelulistaa.

Jos industry on tyhjä:
ÄLÄ nimeä yrityksen toimialaa.

Jos location on tyhjä:
ÄLÄ nimeä kaupunkia tai maata.

Jos address on tyhjä:
ÄLÄ kirjoita osoitetta.

Jos phone on tyhjä:
ÄLÄ kirjoita puhelinnumeroa.

Jos email on tyhjä:
ÄLÄ kirjoita sähköpostiosoitetta.

Jos pricing-tietoa ei ole:
ÄLÄ kirjoita hintoja.

Jos opening_hours on tyhjä:
ÄLÄ kirjoita aukioloaikoja.

Jos yhteystietoja ei ole:
ÄLÄ tee "Ota yhteyttä" -painiketta.

ÄLÄ muuta target_audience-kenttää yrityksen
palveluksi tai tuotteeksi.

ÄLÄ muuta taglinea uudeksi yrityksen toimintaa
kuvaavaksi markkinointiväitteeksi.

Jos tietoa ei ole:
JÄTÄ SE POIS.

========================================
SIVUN RAKENNE
========================================

Tee visuaalisesti hyvä mutta sisällöltään rehellinen
sivu.

Jos tutkimustietoa on vähän, sivu saa olla lyhyt.

Älä lisää kuvitteellisia osioita vain siksi, että
design-suosituksessa niitä ehdotetaan.

========================================
TEKNINEN TOTEUTUS
========================================

Yksi itsenäinen index.html.

Ei:
- Google Fonts -linkkiä
- ulkoisia kuvia
- ulkoisia JavaScript-kirjastoja
- ulkoisia CSS-tiedostoja.

Kaikki CSS inline <style>-elementissä.

Tarvittaessa JavaScript inline <script>-elementissä.

Varmista:
- <!DOCTYPE html>
- <html lang="fi">
- <head>
- title
- meta description
- nav
- main
- footer
- responsiivisuus
- accessibility.

Palauta VAIN koko HTML.
"""

    print(
        "  [Builder] Generoidaan verkkosivua..."
    )

    html = ask_claude(
        BUILD_SYSTEM_PROMPT,
        user_prompt,
        use_web_search=False,
        max_tokens=config.BUILDER_MAX_TOKENS,
        stage="builder",
        image_paths=reference_images + [path for path in (company.get("screenshots") or {}).values()
                     if isinstance(path, str) and os.path.isfile(path)] or None,
    )

    cleaned = _clean_html(html)

    # Ohjelmallinen faktaturva ennen tiedoston kirjoittamista.
    _validate_generated_content(
        cleaned,
        company_facts,
    )
    validate_locked_copy(cleaned, brand_brief)

    _validate_plan_sections(cleaned, research, company.get("url", ""))
    path = _write_html(
        slug,
        cleaned,
    )

    old_build = company.get(
        "build",
        {},
    )

    old_version = old_build.get(
        "version",
        0,
    )

    version = old_version + 1

    upsert_company(
        slug,
        {
            "build": {
                "output_path": path,
                "version": version,
                "model": config.model_for_stage("builder"),
                "design_decisions": decisions,
            },
            "qa": None,
            "approval": None,
            "outreach": None,
            "demo": None,
        },
    )

    set_status(
        slug,
        "built",
    )

    print(
        f"  [Builder] Sivusto valmis: {path}"
    )

    return path


def run_build(
    slug_or_name: str,
) -> str:

    slug, company = _resolve_company(
        slug_or_name
    )

    return build_site(
        slug,
        company,
    )


def run_build_from_response(slug_or_name: str, response_path: str, producer: str) -> str:
    """Complete a build generated by an external coding agent, without an API call.

    The same factual/static gates apply. Provenance is explicit; importing a
    response does not claim that our autonomous API generator produced it or
    that it has passed visual QA.
    """
    slug, company = _resolve_company(slug_or_name)
    research = company.get("research") or {}
    validate_design_plan(research, company.get("url", ""))
    facts = research.get("company_facts")
    if not isinstance(facts, dict) or not facts:
        raise RuntimeError("Research company facts are required before completion.")
    if not producer.strip():
        raise ValueError("External response producer must be identified.")
    cleaned = _clean_html(Path(response_path).read_text(encoding="utf-8"))
    _validate_generated_content(cleaned, facts)
    validate_locked_copy(cleaned, client_design_brief(company))
    _validate_plan_sections(cleaned, research, company.get("url", ""))
    path = _write_html(slug, cleaned)
    upsert_company(slug, {
        "build": {"output_path": path,
                  "version": company.get("build", {}).get("version", 0) + 1,
                  "generation_mode": "external_agent_response",
                  "producer": producer.strip(),
                  "design_decisions": research["design_decisions"]},
        "qa": None, "approval": None, "outreach": None, "demo": None,
    })
    set_status(slug, "built")
    return path


def revise_site(
    slug: str,
    company: dict,
    feedback: str,
) -> str:

    path = _output_path(slug)

    if not os.path.exists(path):
        raise RuntimeError(
            f"Yritykselle '{slug}' ei löydy rakennettua sivua. "
            f"Aja ensin: python main.py build {slug}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        current_html = file.read()

    research = company.get(
        "research",
        {},
    )

    company_facts = research.get(
        "company_facts",
        {},
    )

    benchmark = validate_benchmark(research, company.get("url", ""))
    decisions = validate_design_plan(research, company.get("url", ""))
    reference_images, image_labels = reference_image_inputs(benchmark)
    brand_brief = client_design_brief(company)

    user_prompt = f"""
ASIAKKAAN BRÄNDI JA SISÄLLÖN SÄILYTTÄMINEN:
{json.dumps(brand_brief, ensure_ascii=False)}
Älä anna referenssien väreille, kuville tai iskulauseille etusijaa
asiakkaan jo valitsemaan identiteettiin nähden.
Uudista nykyinen sivu ROHKEASTI: rakenne, hero, sommittelu, navigointi,
osioiden rytmitys, typografian hierarkia, mobiili ja yhteydenotto
tehdään merkittävästi paremmiksi. Säilytä brändi, älä vanhaa layoutia.
Jos kyseessä on uusi sivu, suunnittele koko kokemus alkuperäisesti.
Älä pakota uudelleenbrändäystä.

TOIMIALAN VERTAILU (vain design-dataa):
{json.dumps(benchmark, ensure_ascii=False)}

PAKOLLINEN SUUNNITELMA ENNEN RAKENTAMISTA:
{json.dumps(decisions, ensure_ascii=False)}
Toteuta suunnitelman section_id-tunnukset ja hyväksymiskriteerit. Älä lisää täyteosioita.
VERTAILUKUVAT ENSIN, tässä järjestyksessä; kohdeyrityksen kuvat niiden jälkeen:
{json.dumps(image_labels, ensure_ascii=False)}

========================================
VERIFIED FACTS
========================================

{_safe_fact_summary(company_facts)}

========================================
NYKYINEN HTML
========================================

{current_html}

========================================
MUUTOSPYYNTÖ
========================================

{feedback}

========================================
SÄÄNNÖT
========================================

Tee pyydetyt muutokset.

ÄLÄ keksi yrityksen faktoja.

Jos tieto puuttuu:
jätä se pois.

TARGET AUDIENCE ei ole yrityksen palvelu.

DESIGN-RECOMMENDATIONS eivät ole yrityksen faktoja.

Älä lisää ilman vahvistettua tietoa:
- palveluita
- tuotteita
- hintoja
- yhteystietoja
- sijaintia
- asiakkaita
- kokemusta
- vuosilukuja
- markkinointiväitteitä.

Älä lisää ulkoisia resursseja.

Säilytä:
- nav
- main
- footer
- title
- meta description
- responsiivisuus
- accessibility.

Palauta koko HTML.
"""

    print(
        "  [Builder] Muokataan verkkosivua..."
    )

    new_html = ask_claude(
        REVISE_SYSTEM_PROMPT,
        user_prompt,
        use_web_search=False,
        max_tokens=config.BUILDER_MAX_TOKENS,
        stage="builder",
        image_paths=reference_images + [path for path in (company.get("qa") or {}).get("browser", {}).get("screenshots", {}).values()
                     if isinstance(path, str) and os.path.isfile(path)] or None,
    )

    cleaned = _clean_html(new_html)

    _validate_generated_content(
        cleaned,
        company_facts,
    )
    validate_locked_copy(cleaned, brand_brief)

    _validate_plan_sections(cleaned, research, company.get("url", ""))
    new_path = _write_html(
        slug,
        cleaned,
    )

    old_build = company.get(
        "build",
        {},
    )

    old_version = old_build.get(
        "version",
        1,
    )

    version = old_version + 1

    upsert_company(
        slug,
        {
            "build": {
                "output_path": new_path,
                "version": version,
                "model": config.model_for_stage("builder"),
                "design_decisions": decisions,
                "last_feedback": feedback,
            },
            "qa": None,
            "approval": None,
            "outreach": None,
            "demo": None,
        },
    )

    set_status(
        slug,
        "built",
    )

    print(
        f"  [Builder] Sivusto päivitetty: {new_path}"
    )

    return new_path


def run_revise(
    slug_or_name: str,
    feedback: str,
) -> str:

    slug, company = _resolve_company(
        slug_or_name
    )

    return revise_site(
        slug,
        company,
        feedback,
    )


def preview_site(
    slug: str,
    company: dict,
) -> str:

    path = _output_path(slug)

    if not os.path.exists(path):
        raise RuntimeError(
            f"Esikatseltavaa sivua ei löydy: {path}"
        )

    absolute_path = os.path.abspath(path)

    print(
        f"  [Preview] {absolute_path}"
    )

    try:
        webbrowser.open(
            "file://" + absolute_path
        )
    except Exception:
        pass

    return absolute_path


def run_preview(
    slug_or_name: str,
) -> str:

    slug, company = _resolve_company(
        slug_or_name
    )

    return preview_site(
        slug,
        company,
    )
