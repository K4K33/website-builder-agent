# Kaurivo — yhden painalluksen sisäinen demojono (2026-11-10)

## Käyttö

Kirjaudu Kaurivon hallintaan osoitteessa https://k4k33.github.io/website-builder-agent/kaurivo/admin/ . Avaa **Aamun yritykset**, etsi yritys ja paina **Rakenna demo**. Pyyntö tallentuu Supabasen yksityiseen työjonoon. Avaa **Demot**-näkymä tai iPhonen alavalikon Demot-painike. Tilat ovat Jonossa, Taustatutkimus, Rakenteilla, Laatutarkistus, Julkaisutarkistus, Sisäinen esikatselu, Odottaa korjausta ja Virhe.

Työn valmistuttua näkyvät **Vanha sivu** ja **Avaa uusi demo** suorina HTTPS-osoitteina. Uusi linkki osoittaa yrityksen omaan Render-esikatselukansioon, ei GitHubin lähdekoodiin, zip-tiedostoon tai chat-tiedostoon. Lisäksi näytetään kyseisen GitHub Actions -ajon loki ja tarkistusraportti. Edellinen versio säilytetään; ei ylikirjoiteta vanhoja asiakkaan tarkistamia demoja.

## Toteutus ja tietoturva

- **UI**: `docs/kaurivo/admin/index.html`, `assets/crm.js`, `assets/demo-jobs.js`, `assets/crm.css`.
- **DB**: Kaurivon erillinen Supabase-projekti `xhsfbcwpwbgdbatrcyuk`. Taulu `public.kaurivo_demo_build_jobs` on RLS-suojattu, ja kirjoitusoikeudet on poistettu selaimelta. Todetun ylläpitäjän `kaurivo_request_demo_build(uuid)` RPC vastaanottaa VAIN prospect-UUID:n ja hakee yritystiedot itse luotetusta kannasta. 5 pyyntöä / Helsingin kalenteripäivä; yksi aktiivinen työ per yritys.
- **Worker endpoint**: `kaurivo-demo-worker` Edge Function, todentaa RS256 GitHub OIDC:n issuerin, yleisön, repo-/owner-ID:t, main-refin, workflow-refin ja eventin. **Ei tarvitse GitHubiin Supabasen salaisuuksia**. Supabase service-role pysyy vain Supabasen palvelinympäristössä.
- **Scheduled worker**: `.github/workflows/kaurivo-demo-worker.yml`, enintään yksi työ rinnakkain, aikataulutettu viiden minuutin välein (GitHub voi viivästyttää tai jättää cron-ajon väliin). Kirjoittaa varsinaisen `auto/kaurivo-demos` esikatseluhaaran.
- **Render-host**: `https://kaurivo-auto-demos-2026.onrender.com/`, auto-deploy branch `auto/kaurivo-demos`, palvelu `srv-dbpcpkbm8hqs73di4shg`. Jokaisella demolla oma pysyvä katalogi, kuten `/kaurivo-esimerkki-<jobid>/index.html`. Tämä on **julkisesti avattava, noindex-merkitty sisäinen suunnitteluesikatselu**, ei kirjautumissuojattu asiakastietojen säilytyspaikka.
- **Real pipeline**: nykyinen `main.py research`, `concept-previews`, `choose-concept`, `build`, `qa` viimeisimmästä main-koodista. Vaatii kolme aidosti renderöityä yrityskohtaista konseptia, alkuperäisen visuaalisen kokemuksen inventaarion, lähdesisällön säilyttämisen, uusimman Mestari-Promptin, riippumattoman laadun osoituksen ja liiketoimintafunktiot. Eteneminen on fail-closed.
- **Automaattinen korjaus**: epäonnistunut QA tuottaa rajatun konkreettisten havaintojen korjausbriefin. Rakennin ajaa enintään kaksi yrityskohtaista Revisio→QA-uusintakierrosta. Viimeisen rakennusversion on läpäistävä uusintatestit; muuten tilaksi tulee HOLD. AI-vaiheilla on yhteinen 2 200 sekunnin työkulubudjetti, yksittäinen vaihe enintään 480 sekuntia. Tämä ei lupaa 100 % onnistumista, mutta estää loputtomat korjaussilmukat ja virheellisen asiakasesikatselun hyväksynnän.
- **Technical publish proof**: Render-osoitteen oma HTML release-marker, CSS, JS, ulkoisten resurssien ja reittien todellinen Chromium-tarkistus 390/768/1440 px. Vain tämä voi tuottaa `internal_preview`-tilan. Oikeudet, 9,5/10 riippumaton tarkistus, kaupallinen tila ja CMS-luovutus pysyvät erillisinä.

## Ilmaisen AI:n pakollinen käyttöönotto

GitHubin Actionsia ajavassa repositoryssä pitää olla **salaisuus** `OPENROUTER_API_KEY` (aiemmin käytetty projektin omassa agentissa) sekä GitHub Actions repository **Variables** `KAURIVO_BUILDER_MODEL_FREE` ja `KAURIVO_QA_MODEL_FREE`, täsmälliset oikeasti saatavilla olevat `:free`-mallit; valinnainen `KAURIVO_RESEARCH_MODEL_FREE`. Älä kirjoita salasanoja tähän dokumenttiin tai GitHub-koodiin. `FREE_ONLY=1`, ulkoinen Tavily ja maksullisten mallien käyttäminen on estetty. Jos asetuksia ei ole tai malli ei täytä laatutavoitetta, työ jää HOLD-tilaan. **Painikkeen ilmestyminen ei itsessään todista, että ilmaista mallia on määritetty tai että generointi saavuttaa 9,5/10.** Ilmaispalvelun käyttörajat voivat vaihdella.

Yritykset, joilla ei ole varmennettua verkkosivua tai todennettua palvelukuvausta, jäävät `source_website_needs_verification`-HOLD-tilaan. Tällaisten yritysten automaattinen rakentaminen vaatii ensin `utils/verified_profile.py`-portin mukaisen erillisen, luotettavan faktaprofiilin. Nimeä ja toimialaluokitusta ei saa täydentää keksityillä palveluilla.

## Todellinen laadun tila

- Uusi UI / queue / Edge Function / Render-hakemisto voi olla rakennettu ja yksikkötestattu ilman, että ensimmäinen asiakaskohtainen automaattinen generointi on tehty. Ensimmäisen läpimenon todentaminen edellyttää kirjautuneen ylläpitäjän tekemää rakennuspyyntöä, GitHubin oikeasti käynnistynyttä työnkulkua ja onnistunutta Renderin ulkoista selainkoetta.
- Mitään automaattisia markkinointiviestejä, asiakkaan kuvia ilman oikeuksia, näennäisiä 3D-tuotteita tai maksullisia tekoälymalleja ei sallita. Etusivun 18/18 testit eivät ole itsenäinen premium-arvio.
- Katkenneen workerin yli 70 min vanha tila vaihdetaan seuraavassa ajoittaisessa claimissa HOLD:ksi; sen täytyy läpäistä kaikki portit uuden pyynnön yhteydessä.
- GitHubin `workflow_dispatch` soveltuu turvalliseen no-work yhteystestiin; odotettavissa `no work` -tulos, kun yksityinen jono on tyhjä. Täysi build- ja review-testidemo on vielä erillinen tarkistus.
