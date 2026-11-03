> **Kaurivo premium delivery / sales safety (2026-11-01):** [Premium launch & QA playbook](docs/KAURIVO_PREMIUM_PLAYBOOK.md) and [Private client offer template](docs/KAURIVO_CUSTOMER_OFFER_TEMPLATE.md).
> Zero-cost local gates: `python main.py demo-evidence SLUG`, `premium-pitch-check SLUG`, `premium-audit --html PATH --root ROOT`, `project-terms --file PRIVATE_JSON`, `handover-check SLUG`, `delivery-preflight SLUG --html PATH --root ROOT`, and `sales-funnel`. **No automatic sends, client CMS activation, paid API calls, site publication or invented analytics.**
> The Kaurivo demo review form asks for the client's conversion goals, editing priorities and brand/photo preferences, without treating these as rights or signed approval.

> Current quality controls, model setup, costs and remaining validation: [QUALITY.md](QUALITY.md).
> Client brand preservation, approved image/copy changes, editable websites and CMS handover: [CLIENT_HANDOVER.md](docs/CLIENT_HANDOVER.md).
> **Mandatory for every final client delivery:** the customer can personally edit text, services, images and contact details via a secure CMS. Static demos are allowed for review, never labelled as editable delivered sites. Verify with `python main.py handover-check COMPANY_SLUG` before the actual client handover.\n> Customer-specific email research, persuasive copy and sending safeguards: [OUTREACH.md](docs/OUTREACH.md).

> **National daily discovery at 04:13 Europe/Helsinki:** process the PRH bulk company ZIP via one capped request; inspect the entire registry locally, queue at most 5,000 unseen prospects and show 50 for human review. A small 03:17 OSM pilot supplements this. Neither job uses paid AI, creates demos or sends outreach. [NIGHTLY_ACQUISITION.md](docs/NIGHTLY_ACQUISITION.md).

# Website Builder Agent

## Kaurivon uusi ihmisen hyväksymä asiakastyönkulku

Nykyisessä 0 € -työnkulussa **ChatGPT avustaa yritysten valinnassa ja
rakentaa hyväksytyn yrityksen demonsa**, mutta yrityksille ei lähetetä
viestejä automaattisesti.

1. Löydä yrityksiä maksuttomilla lähteillä:
   `python main.py scout --discovery-only --count 10 --industry kampaamo --location Tampere`
   (OSM/Overpass-kutsuja voidaan tehdä; ei kuluta OpenRouter- tai Tavily-krediittejä).
2. Luo selkeä käyttäjän tarkistuslista:
   `python main.py shortlist --limit 10 --format markdown`
   (ei verkkoyhteyksiä eikä AI-kutsuja).
3. Käyttäjä tutkii valitun yrityksen, erityisesti sen toiminnan
   aktiivisuuden ja onko sillä todella jo verkkosivu. Merkintä
   `website_not_listed` tarkoittaa ainoastaan, että sivua ei ollut
   lähteessä listattuna.
4. Tallenna päätös:
   `python main.py review-lead SLUG --decision select --note "Sopiva demo"`.
   Vaihtoehdot ovat `select`, `later` ja `skip`. Tämä **ei** tee
   AI-ajokutsua, käynnistä demoa, todenna verkkosivun puuttumista
   eikä anna yhteydenottolupaa.
5. Käyttäjä sanoo ChatGPT-keskustelussa esimerkiksi `Tee tälle yritykselle
   laadukas sivusto`. ChatGPT voi tehdä yritystutkimuksen, vertailla
   oikeita saman alan referenssisivustoja, toteuttaa koodin GitHubiin
   ja käyttää maksuttomia testejä ilman erillistä OpenRouter-ajokutsua.
   Tämä kuluttaa ChatGPT-käyttöoikeuksia, ei automaattisesti
   OpenRouter-krediittejä. Tuotannon laatu pitää tarkistaa.
6. Käyttäjä hyväksyy demonstraation ja lähetysviestin erikseen.
   Gmail-integraatio voi laatia ja lähettää yhden viestin erillisellä
   nimenomaisella pyynnöllä. Tämä Python-työkalu ei koskaan lähetä
   sähköposteja eikä automaattisesti poimi henkilöiden yhteystietoja.

Markkinointiviestien osoitteet ja oikeusperuste tarkistetaan erikseen.
Suomen sähköisessä B2B-suoramarkkinoinnissa yhteisölle osoitetut viestit
ja luonnolliselle henkilölle osoitetut viestit eivät ole sama asia.
Vastaanottajan markkinointikielto on aina huomioitava, ja viestissä
on ilmoitettava selkeästi mahdollisuudesta kieltäytyä.
Älä oleta, että kenen tahansa henkilökohtainen sähköposti on
vapaasti markkinoitavissa vain, koska sen osoite löytyy verkosta.

Luettelon aktiivisuuskriteeri on säilynyt ensisijaisena;
hyvät arvostelut, monen toimipaikan omistaminen tai tilinpäätös eivät
ole vaatimuksia. Muutokset ovat työkulun valmistelua. Ne eivät
tarkoita, että ChatGPT jo lähettäisi taustalla automaattisesti uusia
liidilistoja; jatkuva ilmoitus vaatii erikseen asetetun ajastuksen.

## V9: maksuton tuotantotila hyödyntää aidot ilmaiskiintiöt

**Oletus:** `AI_BACKEND=ollama` ja `FREE_ONLY=1`. V9 sallii tässä
maksuttomassa tilassa **OpenRouterin nollahintaiset `:free`-mallit**
(tarkalla mallivalinnalla; Research voi käyttää `openrouter/free`-reititintä)
sekä **Tavily Researcher -tilin vahvistetut maksuttomat hakukrediitit**.
Maksulliset malliversiot ja vahvistamattomien Tavily-tilien pyynnöt
estetään. Maksulliseen käyttöön ei koskaan siirrytä automaattisesti.

Katso täydelliset käyttörajat, turvaehdot, tilivahvistus ja hybridi-
esimerkki: `docs/KAURIVO_V9_VERIFIED_FREE_TIERS.md`.

**Käyttökustannus:** ei maksullisia tekoäly-/hakupalvelukutsuja, mutta
laitteisto, sähkö, internet ja mahdolliset hosting-palvelut eivät ole
kirjaimellisesti ilmaisia. Paikallista mallia EI asenneta automaattisesti,
eikä GitHubin pilviajokone voi ajaa käyttäjän koneen Ollamaa.

Aseta omalla Windows-koneella PowerShellissä ensin paikallisesti asennetut
mallit (vaatii riittävän suuren, kuvien ymmärtämistä tukevan QA-mallin):

```powershell
$env:AI_BACKEND = "ollama"
$env:FREE_ONLY = "1"
$env:OLLAMA_MODEL = "OMA_PAIKALLINEN_TEKSTIMALLI"
$env:OLLAMA_BUILDER_MODEL = "OMA_PAIKALLINEN_KOODIMALLI"
$env:OLLAMA_QA_MODEL = "OMA_PAIKALLINEN_KUVAMALLI"
python main.py free-readiness
```

Korvaa nimet **todella asennetuilla** paikallisilla malleilla. En ole
varmistanut tässä projektissa, että käyttäjän laitteessa on edes Ollama tai
että tietty paikallinen malli kykenee vaadittuun premium-tason koodaukseen ja
kuvien analysointiin. Paikallisen palvelun häiriö **ei** siirrä kutsua pilveen.
Lisätiedot: https://docs.ollama.com/api .

Uudet Research-vaiheen saman toimialan **todelliset yritysreferenssit**
haetaan ensin maksuttomasta OpenStreetMap/Overpass-lähteestä sekä jo
todennetuista välimuisteista. Jos toimialan todellisia ehdokkaita on liian
vähän, vahvistetun Tavily Researcher -tilin jäljellä olevia ilmaiskrediittejä
voidaan käyttää hallitusti. Referenssit vaativat
edelleen alkuperäissivuston sisällön tarkistuksen, vertailukuvakaappaukset ja
vähintään kolme lähteisiin sidottua saman toimialan yritystä. Julkisen OSM-
palvelun käytölle voi olla rajoituksia, virheitä ja verkkokuormitusta.
Hakua rajoitetaan kohtuullisiin aluekyselyihin, tulokset talletetaan
toimialakohtaiseen välimuistiin, sivustotekstit ja todelliset
referenssikuvakaappaukset uudelleenkäytetään aikarajallisesti. Puuttuvia
referenssejä ei keksitä eikä korvata maksullisella haulla.

Maksuton vapaa jono käsittelee kaikki aiemmin löydetyt ja tallennetut
kelvolliset yritykset ilman **ohjelmiston keinotekoista kappalemäärärajaa**:

```powershell
# Yritystietojen julkiset verkkopyynnöt on erikseen sallittava.
python main.py free-batch --allow-public-lookups --limit 0
# Voit myös jakaa työn eriin. Seuraavalla ajolla jatketaan jonosta.
python main.py free-batch --allow-public-lookups --limit 20
# Jos esteenä ollut tieto korjattiin:
python main.py free-batch --allow-public-lookups --retry-failed
```

Tämä käyttää paikallisia malleja tai täsmällisesti valittuja
maksuttomia OpenRouter-malleja Researchiin, Builderiin ja visuaaliseen
QA:han. Paikallinen malli jää käyttöön maksuttoman pilvikiintiön
täyttyessä, jos se on asennettu. Agentti tekee enintään kaksi
saman yrityksen havaintopohjaista
korjauskierrokseen (vaihdettavissa `--max-revisions 0..3`).
Yksittäiset ongelmat pysäytetään ilman, että loppujonon työ katoaa.
Jokainen tulos kirjataan `output/_kaurivo_free_batch.json`-tiedostoon.
Käytettävissä on myös täysin ilman tekoälyä tehtävä kuvavertailu
`python main.py visual-evidence SLUG --refresh-original`.

**Yöllinen Kaurivo-adminin PRH-haku:** ajastettu kansallinen PRH ZIP -ajo
käy edelleen läpi korkeintaan 9 000 ehdokasta paikallisesti ja muodostaa
50 yrityksen shortlistin. Vahvistetun maksuttoman Tavily-tilin
enintään 12 lisähakua per ajo voidaan nyt tehdä vain turvallisen
palvelinpuoleisen 750 krediitin kuukausivarauksen kautta.
Vahvistuksen puuttuessa hakuja ei tehdä. Tämä EI automaattisesti todista puuttuvaa yrityksen
verkkosivua eikä säilytä aiempia maksullisella haulla saatuja 12
verkkosivuehdotusta: ilman luotettavaa ilmaista näyttöä verkkosivun
tilanne jää tarkistettavaksi. Yritysten määrää ei hiljaisesti pienennetä
sen takia. OSM:n julkista reilun käytön rajaa ei kierretä.

**Määrä ja laatu:** numeroa sivustoa/päivä ei voi luvata ennen paikallisen
koneen nopeuden, mallien laadun ja todellisen jonon mittaamista.
`free-batch` raportoi onnistuneiden ajokertojen toteutuneet kestot ja
niistä laskennallisen 8 tunnin kapasiteetin. Raportin `completed` tarkoittaa
vain, että prosessi valmistui; se ei ole 9,5/10-hyväksyntä. Laadun pitää
säilyä kaikissa projekteissa, eikä asiakasviestejä lähetetä automaattisesti.

## Maksuton asiakashaku ja turvallinen pilotointi (2026-10-29)

Uusi ehdotettu kuluton alkuprosessi:

```bash
python main.py scout --count 10 --industry ravintola --location Tampere --discovery-only
python main.py enrich-free --max-companies 5 --confirm-public-lookups
python main.py leads
```

Ensimmäinen ja viimeinen komento eivät käytä AI-krediittejä. Keskimmäinen
tekee korkeintaan rajatun määrän maksuttomia PRH:n avoimen datan verkkopyyntöjä.
PRH:n tilinpäätösrajapinnasta tarkistetaan vain, **onko tilikausia saatavana**;
se ei vielä anna luotettavaa liikevaihto-/voittosummaa ilman raportin
taksonomiatulkintaa. Arvostelut vaativat edelleen sallituista lähteistä
varmistetun arvion ja arvostelumäärän; puuttuva tieto ei tarkoita huonoa
yritystä.

Verkkosivuton yritys voi siirtyä rakentamiseen vain, kun verkkosivun
puuttuminen ja yrityksen todelliset palvelut on tarkistettu:

```bash
python main.py screen-lead YRITYS --evidence lead-evidence.json
python main.py attach-profile YRITYS --profile verified-profile.json
python main.py research YRITYS --confirm-paid-apis
```

Huom. `research` sekä muut AI-pohjaiset yksittäiset komennot edellyttävät
`--confirm-paid-apis`; `pipeline` edellyttää `--confirm-live-run`.
Tarkista palveluntarjoajan euro-/kulukatto ennen maksullisia ajoja.
Tarkka profiilin ja tietolähteiden skeema sekä rajoitukset: [QUALITY.md](QUALITY.md).


> **Turvallinen käyttö:** `pipeline` tekee oikeita ulkoisia API-kutsuja ja voi aiheuttaa maksuja. Käytä sitä tietoisesti `python main.py pipeline --confirm-live-run --count 1 --industry kampaamo --location Tampere` -komennolla vasta, kun mallin asetukset ja palveluntarjoajan kulukatto on tarkistettu. GitHub Actionsin manuaalisen työnkulun oletus on maksuton `offline`-testi. `python main.py readiness --min-industries 3` tarkistaa kerätyt tuotantotodisteet maksutta. Katso [QUALITY.md](QUALITY.md).


Agenttijärjestelmä, joka automatisoi verkkosivujen uudistusprosessin
yrityksille: löytää yrityksiä joiden sivut ovat vanhentuneita, tutkii
yrityksen ja toimialan, suunnittelee ja rakentaa uuden ammattimaisen
verkkosivun, tarkistaa sen laadun, ja lopuksi valmistelee (muttei
automaattisesti lähetä) henkilökohtaisen yhteydenottoviestin.

Rakennettu samalla periaatteella kuin aiempi OddsPapi-arbitraasiscanneri:
selkeä, moduulipohjainen Python-projekti, jonka voi ladata suoraan
GitHubiin ja jota voi kehittää eteenpäin.

## Miten järjestelmä toimii

Viisi erillistä agenttia, jotka toimivat peräkkäin yhden yrityksen kohdalla:

1. **Scout** (`agents/scout.py`) - etsii web-haulla yrityksiä, joiden
   sivut vaikuttavat vanhentuneilta.
2. **Research** (`agents/research.py`) - lukee yrityksen nykyisen sivun,
   tunnistaa toimialan ja faktat, hakee inspiraatiota moderneista
   saman alan sivustoista (ei kopioi niitä).
3. **Builder** (`agents/builder.py`) - rakentaa oikean, toimivan
   `index.html`-sivun annettujen faktojen ja design-suositusten pohjalta.
   Tukee myös muokkauspyyntöjä luonnollisella kielellä (`revise`).
4. **QA** (`agents/qa.py`) - tarkistaa automaattisesti mobiilioptimoinnin,
   rikkinäiset linkit, placeholder-jäänteet ym., ja pyytää lisäksi
   Claudelta sisällön laatutarkistuksen.
5. **Outreach** (`agents/outreach.py`) - kirjoittaa sähköpostiluonnoksen,
   kun olet itse hyväksynyt sivun. **Ei koskaan lähetä mitään
   automaattisesti** - se on tietoinen rajaus tässä versiossa.

Kaikki tila (mikä yritys on missäkin vaiheessa) tallennetaan
`data/companies.json`-tiedostoon, joten voit aina tarkistaa missä mennään.

## Tärkeä huomio tekijänoikeuksista

Builder-agentti on ohjeistettu (system-promptissa) olemaan kopioimatta
tekstejä, kuvia, logoja tai koodia miltään oikealta sivustolta.
Referenssisivustoja käytetään vain yleisten design-periaatteiden
(värit, typografia, tunnelma) tunnistamiseen, ei sisällön lähteenä.
Tarkista silti aina itse lopputulos ennen kuin lähetät mitään asiakkaalle.

## Asennus

### 1. Kloonaa/lataa tämä repositorio ja asenna riippuvuudet

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Luo `.env`-tiedosto

```bash
cp .env.example .env
```

Avaa `.env` ja täytä oma `ANTHROPIC_API_KEY`-arvosi
(saat sen osoitteesta https://console.anthropic.com/settings/keys).

**HUOM:** tämä projekti käyttää Anthropicin web-hakutyökalua (web search
tool), joka on maksullinen ominaisuus API-käytössä. Tarkista
Anthropicin hinnoittelusivulta ajantasaiset hinnat ennen isoja ajoja.

### 3. Testaa ensimmäisellä yrityksellä

Käytä ensimmäisenä testinä esimerkkiyritystä, jonka annoit:

```bash
python main.py add "Koivuranta" https://www.koivuranta.fi/
python main.py research koivuranta
python main.py build koivuranta
python main.py preview koivuranta
```

`preview`-komento avaa rakennetun sivun selaimessasi suoraan
tiedostojärjestelmästä (`output/koivuranta/index.html`).

## Käyttöesimerkkejä (koko työnkulku)

```bash
# 1. Etsi uusia potentiaalisia yrityksiä
python main.py scout --count 10 --industry "putkiliike" --location "Tampere"

# 2. Listaa kaikki tunnetut yritykset ja niiden tila
python main.py list

# 3. Analysoi yksi yritys tarkemmin
python main.py research koivuranta

# 4. Rakenna sille uusi sivu
python main.py build koivuranta

# 5. Katso lopputulos selaimessa
python main.py preview koivuranta

# 6. Pyydä muutoksia luonnollisella kielellä
python main.py revise koivuranta "tee väreistä tummemmat ja ammattimaisemmat"

# 7. Aja automaattinen laatutarkistus
python main.py qa koivuranta

# 8. Kun olet itse tyytyväinen esikatseluun, hyväksy se
python main.py approve koivuranta

# 9. Anna agentin kirjoittaa sähköpostiluonnos (EI lähetä)
python main.py outreach koivuranta

# 10. Kun olet lukenut ja hyväksynyt viestin, merkitse se hyväksytyksi
python main.py approve-outreach koivuranta
```

Kaikki komennot tulostavat myös seuraavan ehdotetun askeleen, joten voit
edetä ohjatusti.

## Kansiorakenne

```
website-builder-agent/
├── README.md
├── requirements.txt
├── .env.example          <- kopioi .env:ksi, älä committaa .env:ää
├── .gitignore
├── config.py              <- kaikki asetukset yhdessä paikassa
├── main.py                <- CLI, josta kaikkia agentteja ajetaan
├── agents/
│   ├── scout.py           <- 1. Yritysten etsintä
│   ├── research.py        <- 2. Yrityksen ja toimialan tutkimus
│   ├── builder.py         <- 3. Sivun suunnittelu ja rakennus (+ revise)
│   ├── qa.py               <- 4. Laadun tarkistus
│   └── outreach.py         <- 5. Sähköpostiluonnos (ei lähetä)
├── utils/
│   ├── claude_client.py    <- Anthropic API -kutsut (myös web-haku)
│   ├── state.py             <- companies.json:in luku/kirjoitus
│   └── fetch.py              <- yritysten omien sivujen haku/puhdistus
├── data/
│   └── companies.json      <- "tietokanta": kaikkien yritysten tila
└── output/
    └── <yritys-slug>/
        └── index.html       <- valmis, ajettava verkkosivu
```

## GitHubiin vieminen

1. Luo uusi repositorio GitHubissa (esim. `website-builder-agent`).
2. Lataa/pushaa tämän kansion sisältö sinne (ÄLÄ lataa `.env`-tiedostoa,
   se on jo `.gitignore`ssa suojattuna).
3. Jos haluat jakaa projektin kollegan kanssa, hän tarvitsee vain oman
   `.env`-tiedostonsa - koodi on identtinen.

Jos et ole ennen käyttänyt GitHubia komentoriviltä, helpoin tapa on:
1. Lataa koko kansio zip-tiedostona koneellesi.
2. Pura zip.
3. GitHubissa: "Create new repository" -> "uploading an existing file"
   -> raahaa kaikki tiedostot (paitsi mahdollinen `.env`) sinne.

## Rajoitukset tässä v1-versiossa (tietoisia päätöksiä)

- **Ei vapaata luonnollisen kielen komentotulkintaa terminaalissa.**
  Komennot ovat selkeitä (`python main.py build koivuranta`) eikä
  "Rakenna Koivurannalle uusi verkkosivu" -tyyppistä vapaata tekstiä
  vielä tulkita automaattisesti. Tämä on helpoin ja luotettavin tapa
  aloittaa; seuraava kehitysaskel (ks. alla) voi lisätä tämän päälle.
- **Sähköpostia ei lähetetä automaattisesti.** `outreach`-komento vain
  kirjoittaa ja tallentaa luonnoksen. Todellinen lähetys (SMTP/SendGrid)
  ja laskutus on tarkoituksella jätetty pois - lisätään myöhemmin, kun
  haluat ottaa ne käyttöön.
- **Scout-agentti ei "seulo koko internetiä"** vaan tekee kohdennettuja
  web-hakuja annetulla toimialalla/sijainnilla. Tarkista aina tulokset
  itse ennen jatkokäsittelyä.
- **Kuvat**: builder käyttää CSS:ää/SVG:tä oikeiden valokuvien sijaan,
  koska agentti ei voi laillisesti käyttää yrityksen tai kilpailijoiden
  oikeita kuvia. Voit myöhemmin lisätä tekoälykuvageneroinnin tai pyytää
  asiakkaalta omia kuvia.

## Seuraavat kehitysaskeleet (ehdotuksia)

- **Luonnollisen kielen ohjaus**: lisää `agent_runner.py`, joka ottaa
  vapaan tekstipyynnön (esim. Telegram-botin tai yksinkertaisen
  web-käyttöliittymän kautta, samaan tapaan kuin arbitraasiscannerin
  Telegram-ilmoitukset), tulkitsee sen Claudella yhdeksi yllä olevista
  komennoista ja ajaa sen.
- **Sähköpostin lähetys**: kun olet valmis, lisää `agents/sender.py`
  joka käyttää esim. SMTP:tä tai SendGridiä, mutta AINA vasta
  `approve-outreach`-tilan jälkeen.
- **Billing-agentti**: laskutuksen automatisointi kun ensimmäiset
  asiakkaat on saatu.
- **Kuvaesikatselu**: lisää mahdollisuus generoida oikea kuvakaappaus
  (esim. Playwright) rakennetusta sivusta, jotta esikatselu ei vaadi
  selaimen avaamista käsin.

## Vianetsintä

- **"ANTHROPIC_API_KEY puuttuu"** -> tarkista että `.env`-tiedosto on
  olemassa (ei vain `.env.example`) ja avain on oikein kopioitu.
- **"Sivun haku epäonnistui"** research-vaiheessa -> tarkista että URL on
  oikein kirjoitettu ja yrityksen sivu on julkisesti saatavilla (ei
  esim. salasanan takana).
- **Rate limit -virheet** -> nosta `.env`-tiedoston `REQUEST_DELAY`-arvoa.
- **Claude ei palauta validia JSONia** -> aja komento uudelleen; tämä on
  harvinainen mutta mahdollinen LLM-kutsujen kanssa. Jos toistuu usein,
  kerro Claudelle (kehittäjänä) täsmällinen virheviesti niin
  system-promptia voidaan tarkentaa.
