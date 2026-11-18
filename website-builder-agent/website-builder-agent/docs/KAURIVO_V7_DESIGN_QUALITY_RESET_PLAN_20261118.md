# Kaurivo V7 — Rakentajan laatujärjestelmän uusiminen

**Päätöspohja:** 18.11.2026 käyttäjän noin 73,57 sekunnin näyttötallenne S. Räsäsen Autohuolto Oy:n nelisivuisesta demosta, verrattuna alkuperäisen yrityssivuston kuvakaappaukseen sekä GitHubin `main`-haaran Research-, Builder-, QA- ja julkaisutarkistuksiin. Tämä dokumentti on **toteutussuunnitelma, ei toteutettu laatukorjaus**.

**Ensimmäinen asiantuntijan kokonaisarvio:** 4,0/10. **AI-tyylin vaikutelma:** 8,5/10 (diagnostinen, 10 = hyvin AI-generoidun oloinen, ei väite alkuperästä). Korjattu 70px palvelupalsta ei nosta alkuperäistä arvosanaa jälkikäteen.

## A. Diagnostiikka: mitä tämä näyte paljasti

Alkuperäisessä S. Räsäsen sivussa on punavalkomusta identiteetti, nimi ja todennäköisesti oikean mekaanikon työtilanteen valokuvallinen kuva, vahva korjaamoyhteys ja käytännön palvelusisältö. Uusi Kaurivon demo käytti geneeristä massiivista teknistä rengashavainnetta ja SVG-moottoria, ylimitoitettuja otsikoita (Arial Narrow + negatiivinen tracking), 01/02-kortteja, 20+-jättilukua, keinotekoista karttaa ja samanlaisia tumma–harmaa–punainen-palkkeja. Palvelusivun CSS-grid `70px 1fr 180px` sisälsi vain kaksi välitöntä lasta; pääsisältö sijoittui 70px palstaan. Aiemmat HTTP, mobile no-overflow, favicon ja perus-QA läpäisivät silti. Jälkeenpäin korjattu grid ratkaisee konkreettisen bugiluokan mutta ei todista premium-laatua.

**Koodin todetut rakenteelliset syyt:**
- `docs/KAURIVO_MESTARI_PROMPT.md` sisältää noin 63k merkkiä ja historiallisia lisäyksiä. `utils/service_quality.py` injektoi aktiivisen osan, `agents/builder.py` kokoaa sen lisäksi laajan perintöpromptin ja `agents/qa.py` omat arvio-ohjeet. Historiallisia kieltoja on jo paljon. Lisäkirjaus ei varmista noudattamista.
- `utils/creative_directions.py` validoi kolme erilaista TEKSTINÄ kuvattua suuntaa ja `utils/concept_previews.py` teknisiä esikatselutodisteita. Kolme näytettä eivät kuitenkaan automaattisesti tarkoita kolmea laadukasta sommitelmaa; valinnan pitää perustua renderöityyn käytännön vaikutelmaan.
- `utils/premium_experience_gate.py` ilmoittaa visuaaliset puutteet arvioitaviksi eikä osaa päätellä kuvien tai typografian todellista esteettistä laatua. `utils/universal_quality.py` ilmoittaa saman useissa pending-tiloissa. Silti tekninen vihreys koettiin ja raportoitiin liian helposti valmiutena.
- `agents/qa.py` pystyy pyytämään saman järjestelmän käytössä olevalta mallipalvelulta pisteytystä. Sellaista ei saa nimetä riippumattomaksi arvioijaksi ilman todellista erillistä arviointia. Tarkistuskutsujen läsnäolo ei ole näyttö siitä, että luonnoksen laatu paranee.
- `scripts/audit_changed_owner_previews.py` ja `scripts/smoke_live_owner_previews.py` vahvistavat alkuperäisyyttä, tiedostojen latautumista ja teknistä toimivuutta; kuvankauneus ja todellinen yritysuskottavuus tarvitsevat uuden erillisen arviointiprotokollan.

## B. V7:n arkkitehtuuri: yksi lyhyt ydin, erilliset pakolliset päätökset

Luo `docs/KAURIVO_MASTER_V7.md` noin 2–4 sivun ajonaikaiseksi ytimeksi ja koneellisesti versioitu `config/kaurivo_quality_v7.json` (vain havaittavat kriittiset ehdot). Historiallinen V6 siirretään viitetiedostoksi, jossa yksittäisiä havaintoja ei enää automaattisesti kopioida jokaiseen mallipyyntöön. `utils/service_quality.py` lataa ja tarkistaa V7:n allekirjoitetun ajonaikaisen tekstin; `agents/research.py`, `agents/builder.py`, `agents/qa.py` ja `agents/builder.py::revise_site` kuluttavat samat versioidut, vaihekohtaiset osat. Jatkuva append-only-promptikasvu poistetaan: jokainen uusi havainto näkyy erikseen `rules -> implementation -> test -> blind_validation`.

Ytimen pakolliset osat:
1. **Faktat ja identiteetti:** ei keksittyjä väitteitä, nimiä, henkilöstöä, logoja, kokemuksia, aukioloaikoja, hintoja, sertifikaatteja tai osoitteita; oikea kieli.
2. **Aineistohierarkia:** yrityksen oikea valokuva/video ja logo, kun käyttöoikeudet on vahvistettu; sitten oikea lisensoitu liiketoimintaa kuvaava valokuva; viimeisenä todelliseen opetus-/tuote-/palvelutarpeeseen perusteltu graafinen havainne. Kuvaoikeuden puute on oma tiedollinen tila, EI automaattinen lupa generoida kuvitteellinen asiakas.
3. **Yrityksen tunnistettavuus:** ensi vilkaisulla käy ilmi oikea ala, yrityksen erityinen luonne, paikka/tarjonta ja asiakastehtävä myös piilotetulla nimellä.
4. **Luova valinta ennen toteutusta:** kolme tarkoituksellisesti erilaista, oikealla medialla ja copylla renderöityä konseptia; yhden valinta on perusteltu lähdemateriaaliin ja työn tehtävään, ei mallin omaan itsekehuun.
5. **Anti-templaten oletus:** ei koristenumerointia, jättilukuja, matalamielisiä ympyrä/paneeli/SVG-kuvioita, valheellisia karttoja, geneeristä kolmen kortin katalogia, retorisia vastakohtapareja, järjettömiä nuolia, yleispäteviä slogan-lauseita. Poikkeus vain, jos lähde tai yrityksen toiminta antaa niille selkeän tarkoituksen.
6. **Typografia:** enintään 1–2 aidosti tarkoituksenmukaista kirjasinperhettä, tarkistettu lisenssi/latautuminen ja font-fallback; ei `scaleX`-puristuksia, mielivaltaista erittäin tiukkaa trackingia, mahdottomia kirjainvälejä tai suurten otsikoiden rivittymisiä; liiketoiminnan sisältö ennen typografista show'ta.
7. **Sivukohtainen työ:** etusivu kertoo pääasiallisen tarjonnan, palvelusivu auttaa ratkaisemaan oikean tarpeen, yhteyssivu löytämään oikean sijainnin ja yhteydenoton; sisällön määrä ohjaa tilankäyttöä, ei päinvastoin.
8. **Taidollinen laatu:** animaation, SVG:n tai 3D:n olemassaolo ei tuo pisteitä; ilman todennettua hyödyllistä kokemusta se poistetaan. Tyylin tulee olla omaperäinen, ei saman agenttimallin toisto.
9. **Täydellinen toteutus:** mobiili, 768 ja työpöytä, saavutettavat ohjaimet, CTA:t, faktat, yhteystiedot, hakutuloksen otsikot, favicon, metat, footer, käyttöoikeudet ja asiakkaan oikeat toiminnot.
10. **Aito julkaisu:** automaattinen valmis, suoraan avautuva HTTPS-esikatselu, vanha+uusi linkki, todellisen selaimen julkaisuversio ja CSS/JS/media-testit. Erota omistajan esikatselu, asiakkaalle hyväksytty myyntidemo ja CMS-luovutus.

## C. Uusi Research → Design → Build → QA -putki

**1. Source Passport / lähdepassi.** `agents/research.py`, `utils/source_identity.py`, `utils/brand_lock.py`. Kerää jokaisen tärkeän alkuperäisen sivun mobiili- ja desktop-kuva, logo-ehdokkaat/niiden todelliset oikeudet, hallitseva valokuvallinen tyyli, tärkeät visuaaliset erikoisuudet, palveluiden tarkat rajaukset ja copy. Tuota `source_passport.json`: company_identity, site_signature, media_inventory [{source,subject,route,rights,resolution,relevance}], essential_content_map, visitor_tasks, visual_floor, missing_evidence. Onko yrityksellä jo hyvä video/3D/vertailu? Sen poistamiseen vaaditaan perustelu. "Ei verkkosivua" ei tarkoita "ei brändiä" — tarkista vahvistetut sosiaaliset/asiakasmateriaalit erikseen.

**2. Creative Brief / oikea taidesuuntapäätös.** Uusi `utils/design_quality_brief.py` tuottaa yhden objektiivisesti arvioitavan `design_brief.json`: kohdeasiakas, luottamuksen perustelu, ensisilmäyksellä ymmärrettävä palvelu, image_first_choice + oikeus, värit ja typografian rooli, 2–3 näkyvää omaperäistä ratkaisua, kielletyt tyyliyhdistelmät (AI-look), palvelusivun tietohierarkia, mobiiliratkaisu. Käyttäjälle ei näytetä yliopistomaista tekstiä tai reittien kirjoittamista pelkäksi viraston raportiksi.

**3. Rendered creative competition.** Kolme erilaista suuntaa `utils/concept_previews.py`: ne eivät saa olla sama rakenne toisella värillä. Jokaisesta vähintään etusivun yläosa ja yksi aito palvelusivu 390/1440px todellisella tekstillä, käytettävissä olevilla kuvilla, yhtenäisillä navigaatio- ja CTA-ehdotuksilla. Arvioija vertaa jokaisen lähteen VISUAALISEEN pohjaan ja vähintään kolmeen erilaiseen Kaurivon aiempaan projektiin. Hylkää kolme heikkoa suuntaa eikä valitse "vähiten huonoa"; kaksi lisäyritystä on sallittu rajatusti, mutta avoin data-/oikeuspuute tuottaa selkeän aineistopyynnön.

**4. Build with explicit component contract.** `agents/builder.py` ja `utils/site_build_pipeline.py` toteuttavat ensin yhtenäisen nav/header/footer, varsinaisen typografian, kuvien rajaukset, sitten sivukohtaiset osiot. Eivät generoi kaikkia loppusivuja yhdellä sokealla itsearvion varassa. Palvelun selittävän tekstin leveys ja yläpuolen kuva säädetään DOM-sisällön mukaan. Yhteyssivu ei saa esittää piirrettyä katuverkkoa todellisena karttana. Jos yrityksellä on oikea liiketoimintakuvasto, sen on oltava uuden sivun ensisijainen suunnittelun lähtökohta.

**5. Visual linter with real pixels.** Uusi `utils/rendered_visual_audit.py` ja `scripts/smoke_live_owner_previews.py`:
- 320/390/768/1024/1440 ja tarvittaessa 1920px; jokainen reitti, FI/SV, vakaa CSS/JS/media ja mobiiliavaukset.
- CSS `getBoundingClientRect`, `scrollWidth`, `getComputedStyle` sekä tekstirivien todellinen leveys; ylivuodot, päällekkäisyydet, alle 280px vakavat desktop-tekstipalstat, yksittäisten sanojen pystyjonot, näkyvä otsikko leikattuna/peitettynä, yhteydenottopainikkeet.
- Faviconin ja `<title>` todellinen näkyminen, fontin latautuminen/fallback; kuvien luonnollinen tarkkuus, rikkinäiset kuvat ja asianmukaiset alt-tekstit; tarkista myös kuvan sisältö silmällä.
- Silmänvaraiset löydökset kirjataan erillisenä arvioijan työnä; automatisoitua heuristiikkaa ei nimetä "premium-passiksi".

**6. Visual red-team / riippumaton arvio.** Älä anna rakentajalle omaa lopullista arvosanaansa. Erillinen mallipalvelun arviointi tai oikea ihminen tarkastelee kaikkien sivujen renderöintejä ja alkuperäistä sivua. Ulkoinen arvio on riippumaton VAIN jos eri arvioija/toimija ja todelliset kuvakaappaukset on todistettu. Puuttuessa status on `VISUAL_REVIEW_PENDING`, ei keksitty 9,5. Pyydä nimenomaan: "mitkä kolme asiaa paljastavat AI-templaattimaisuuden?" ja "mikä yritykselle kuuluva kuvallinen tai toiminnallinen elementti puuttuu?" Verrataan koko sisältöpolkua, ei vain hero-kuvaa.

**7. Targeted revision / kohdennettu korjaus.** Korjaa vakavat virheet juurisyystä. Muuttuneista osista oikeat uudet kuvat, testit, hash-sidottu arvio. Jos järjestelmä voi tehdä laadukkaan valokuvapohjaisen hero-vaihdon, se EI saa tehdä samanlaisia isoja numeroituja kortteja takaisin. Enintään määritelty määrä automaattisia design-kierroksia, sen jälkeen dokumentoitu pull request / omistajan aineistopyyntö, ei ääretöntä HOLD-silmukkaa. Uusi kriittinen bugi -> regression test -> toisen yrityksen testi.

**8. Release/handover.** Varmistettu HTTPS `Avaa demo` on owner-review-lopputulos, ei GitHub/ZIP. Myyntiin tarvitaan lisäksi käyttäjän hyväksyntä, erillinen faktakatselmus ja oikeudet; asiakastoimitukseen editoitava CMS ja toimiva siirto. **9,5 on lopullinen laadun kehitystavoite, EI aloittavan myynnin ehdoton numeroraja.**

## D. Yksi laatukortti, mitattavat kovat portit

Luo koneellisesti tallennettava scorecard, jonka painot ovat suositeltu V7 *arviointimalli*, eivät automaattisen laatulaskennan totuuksia.

| Arvioitava kohta | Osuus /100 | Mitä arvioidaan oikeista kuvista |
| --- | ---: | --- |
| Yrityksen identiteetti ja aitous | 20 | Säilytetty erottuva brändi ja oikea ammatin visuaalinen näyttö |
| Sommittelu, visuaalinen rytmi ja hierarkia | 20 | Uskottava tasapaino, kuvan ja tekstin suhde, vaihtelevat tarkoitukselliset osiot |
| Typografian taso | 15 | Fontin muoto, luettavuus, otsikon koko, tracking, rivit, optinen viimeistely |
| Valokuvien/kuvitusten/motion laatu | 15 | Aiheet, oikeudet, materiaali, aitous, tarkoituksenmukaisuus, ei halpaa pseudo-3D:tä |
| Käytettävyys ja mobiili | 10 | Oikean vierailijan tehtävät toimivat kaikilla laitteilla |
| Tekstin luonnollisuus ja informaatio | 10 | Yritys puhuu omalla äänellä, tieto oikeaa, ei tekoälykliseitä |
| Mikroviimeistely | 10 | Favicon, title, header, puhelin, navigointi, CTA, focus/hover, footer |

**AI-vaikutelma 0..10** raportoidaan erillisenä diagnostisena riskilukuna; se ei ole toinen laatuarvosana eikä 100p-arvosanan aritmeettinen vähennys. Rinnalle konkreettiset vähintään kolme havaintoa ja kuvakaappauskohtainen näyttö. Suunnittelutavoitteeksi `AI-look <= 2/10` vain arvioijan havaintoihin sidottuna, ei absoluuttisena tai tieteenä myytävänä AI-ilmaisimena. Eri toimialojen tyylilajien täytyy saada näyttää erilaisilta.

**Kovat esteet, jotka estävät myyntihyväksynnän pisteistä riippumatta:** virheelliset yritystiedot, keksityt palvelut tai arvostelut; lisensoimaton/muokattu logo ilman hyväksyntää; puuttuva tärkeä lähdesisältö; rikkinäinen kuva/favikon tai 404; teksti joka on mahdoton lukea; puhelimen rikkinäinen navigaatio; toimimaton pää-CTA; väärennetty 3D/aito työnäyte; asiakkaan oikeus- ja hyväksyntäpuute. Puuttuva kuva-aineisto voi sallia omistajan selvästi rajatun konseptiesikatselun mutta ei valehdeltua asiakkaalle lähetettävää tuotantoa.

**Myyntikelpoisuus nyt:** vakavia virheitä 0, kaikki oleelliset tiedot ja toiminnot oikein, riittävä *todellinen* design-laatu, omistajan hyväksyntä ja laillinen viestintä. Mitään mekanistista "pakko 8,5" tai "pakko 9,5" estettä ei synny.

## E. Tavoitteen todentaminen vain uusilla yrityksillä

| Mittari | Lähtötaso | Ensimmäinen V7-kokeen tavoite | Lopullinen tavoite |
| --- | --- | --- | --- |
| Ammattisuunnittelijan kokonaisarvio | Räsänen 4,0/10 (vain yksi näyte) | Viidestä aiemmin testaamattomasta yrityksestä väh. 4 selvästi nykyistä parempaa, todennettu | Useiden eri toimialojen aidosti riippumattomat arviot >=9,5/10 |
| AI-tyylisyyden vaikutelma | Räsänen 8,5/10 | Jokaisesta testistä rehelliset perusteet, aleneminen suhteessa valvottuun lähtöversioon | Tavoitetaso <=2/10, ei tarkkuudella varmuutta todellisesta tekijästä |
| Kriittinen selain/DOM-vika | Räsänen: pitkä kappale 70px | 0 kaikissa rakennetuissa demoissa | 0 jatkuvasti |
| Brändin ja lähdesisällön säilytys | Räsäsellä punamusta säilyi, oikean työn kuva korvautui huonosti | Jokaisesta kuvasta käyttötarkoitus ja hakukelpoisuus; kaikille alkuperäisille kriittisille faktoille jäljitys | Ei todistettuja omissions eikä tahattomia brand droppeja |
| Valmis julkaistu esikatselu | Räsänen tarvitsi monta käsikorjausta | Joka hyväksytylle oikea versionmukainen URL ja live-testi | Prosessi toimii automaattisesti |
| Ensimmäisen rakentamiskerran onnistuminen | Ei luotettavaa vertailupopulaatiota | Mittaa läpäisy ensimmäisellä yrityksellä erikseen | Paranee todennetusti myös sokkotesteillä |

Testijoukko: vähintään viisi uutta yritystä eri aloilta; mieluiten mukana 1) kuva-/portfolioalan yritys, 2) palveluyritys, 3) ravintola tai kauppa erikoistietoineen, 4) yritys jossa vahva alkuperäinen video/3D, 5) sivuton yritys jolla varmennettu brändi. Älä käytä viittä saman demon versiota näyttönä yleistettävyydestä. Talleta V6 vs V7 ensimmäisen yrityksen ensiversiot erikseen, samalla aineistolla ja verrannollisella budjetilla, pisteytä sokkona ja pidä alkuperäiset videot/screenshotit. Jos V7 ei ole tilastollisesti uskottavasti parempi, älä julista menestystä.

## F. Tarkka PR-järjestys ja toteutustodisteet

**PR-A – Canonical Master V7 and contracts.**
Luo `docs/KAURIVO_MASTER_V7.md`, `config/kaurivo_quality_v7.json`, `utils/quality_contract.py`, siirrä historiallinen teksti arkistoon, päivitä `utils/service_quality.py` ja prompt-hash-kuluttajat. Vaatimus: jokainen Research/Builder/QA/Revision lukee saman aktiivisen version ja sen testit läpäisevät; sovittuja oikeus/fakta/release-ehtoja ei poisteta.

**PR-B – Source Passport + media-first.**
`agents/research.py`, `utils/source_identity.py`, `utils/brand_lock.py`, uusi passport data. Vaatimus: alkuperäisen aidon kuva-/videoelementin käyttökelpoisuus havaitaan ja kirjataan; käyttöoikeuspuute johtaa nimettyyn aineistopyyntöön, ei generointiin hiljaa. Erityinen sokkotesti sivuttomalle yritykselle.

**PR-C – Three genuinely visual alternatives.**
`utils/creative_directions.py`, `utils/concept_previews.py`, `utils/design_quality_brief.py`. Jokaisesta oikeasti renderöidyt desktop/mobiili-konseptit lähdemedian ja copy/CTA:n kanssa. Validointi estää samoja asetteluja ja heikosti perusteltuja koristesuuntia, edellyttää laadullista vertailua.

**PR-D – Generator and design tokens.**
`agents/builder.py`, `utils/site_build_pipeline.py`, mahdolliset yhteiskomponentit. Erota yrityskohtaisten tyylipäätösten tuottaminen varsinaisen monisivuisen koodin generoinnista. Älä johda yrityksen ulkoasua yleispohjasta. Lisää kuvan rajausten/fontti-fit/luettavuuden konkreettiset toleranssit.

**PR-E – Visual layout / copy / AI-look red team.**
`utils/rendered_visual_audit.py`, `agents/qa.py`, `utils/visual_originality.py`, `utils/premium_experience_gate.py`, yleiset selaintestit. Räsäsen 70px-palsta, venytetty display-type, turhat numerot, halpa kuvankäsittely ja pseudokartta toimivat *negatiivisina regressiofixtureinä*. Testin tulee HYLÄTÄ huono lähtöversio, vaikka HTTP 200 ja no-overflow olisivat vihreät. Ei muuteta makutestiä naiiviksi regex-kieltojen listaksi.

**PR-F – Real hosting + owner/sales status.**
`scripts/smoke_live_owner_previews.py`, demo job status ja admin-UI. Päätepiste palauttaa uuden suoran HTTPS-linkin vasta real live -tarkistuksen jälkeen; ennen sitä tila kertoo syyn ja mitä korjataan. Omistaja näkee suoraan Vanha sivu/Avaa demo. Älä odota käyttäjältä erillistä linkkipyyntöä. Ei lähetysautomaatiota ilman nimenomaista yksittäisen viestin hyväksyntää.

**PR-G – Five-client blind benchmark and rollout.**
Pidä testi- ja suositustiedostot erillään laatusäännöistä; mittaa alusta tehdyt projektit, alkuperäinen lähde, ensiversio, täydellinen arvio, AI-look, kriittiset virheet, syyt, korjaus, julkaistu lopputulos, kustannus, kesto. Etusivu yksin ei riitä. Aktivoi V7 oletukseksi vasta kun uuden putken läpimeno ja parempi todellinen laatu on osoitettu. Säilytä rollback V6:een teknisiä häiriöitä varten; älä käytä sitä laatuesteiden kiertämiseen.

## G. Pysyvät toimintaperiaatteet

- Kaurivon oma ensimmäinen myynti voi alkaa **ennen** portfolion 9,5-pisteen lopputavoitetta, mutta heikkoa tai virheellistä sivua ei esitetä asiakkaalle valmiina.
- Käyttäjän tietokoneelta ei edellytetä raskasta paikallista AI-palvelinta; käytä pilvessä olevia GitHub Actions -selaintestejä ja olemassa olevia, maksukattojen sisällä toimivia AI-palveluita. Maksullisia malleja tai kuvia ei kytketä ilman käyttäjän lupaa.
- Kaikki reitit ja mobiilileveydet tarkistetaan uudelleen jokaisen muutoksen jälkeen. PR/CI=PASS ei koskaan yksin ole visuaalinen laatumerkintä.
- Virheiden oppimissykli on aina: havaittu video/kuva → juurisyy → yleinen uusi sääntö → ohjelmallinen testi/visuaalinen arvio → uuteen asiakkaaseen kohdistuva sokkotesti → julkaistu palautettu tulos.
- Kun riippumattomat 9,5/10-tulokset toistuvat eri toimialoilla, suuret jatkuvat laatumuutokset voivat vaihtua tavalliseen ylläpitoon, turvallisuuteen ja palautteesta johtuviin kohennuksiin. Siten 9,5 ei ole myynnin lähtöruutu eikä lupaus sataprosenttisesta virheettömyydestä.
