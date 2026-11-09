# Kaurivo — Aitoa syvyyttä, 3D-visualisointia ja premium-liikettä (yleinen v1, 9.11.2026)

**Soveltuvuus:** Kaikki uudet tutkimus-, konsepti-, Builder-, revisio-, QA-, staattiset, WordPress-, verkkokauppa- ja manuaaliset projektit. Yrityskohtainen visuaalinen ratkaisu on pakollinen; 3D *ei* ole pakollinen. Tämä standardi täsmentää Mestari-Promptia, eikä muuta asiakkaan todellisia logoja, tuotteita, mediaa tai lupia.

## Oikeista toteutuksista johdetut havainnot

| Toteutus | Todennettu havainto | Kaurivon opetus, ei kopioitava tyyli |
| --- | --- | --- |
| Bruno Simon, https://bruno-simon.com/ | Interaktiivinen Three.js-pohjainen 3D-maailma on itse portfolion navigaatio ja osaamisen näyttö. Käyttäjällä myös laatutason valinta ja mobiiliohjaus. | Kun 3D on *tuote tai osaamisen näyttö*, vahva kokemuksellisuus on perusteltu. Tavallisen pk-yrityksen yhteydenottoa ei tehdä peliksi. |
| Hilo Studio / Tabasco, https://hilostudiolab.com/en/projects/tabasco | Yrityksen oma case kertoo kolmesta tuotetta ja valmistusta havainnollistavasta 3D-objektista; React Three Fiber + Three.js + GSAP ScrollTrigger. | Tarinan järjestys, esine ja eteneminen vastaavat yrityksen oikeaa valmistusta. Näytöstä ei päätellä, että kaikki asiakkaat tarvitsevat pinning-/scrolljacking-kokemuksen. |
| Locomotive / Sundae Creative, https://locomotive.ca/en/work/sundae-creative | Studio kuvaa lähteistetysti editorial-typografiaa, serif/sans-yhdistelmiä, yrityksen omaan identiteettiin kuuluvia värejä sekä hillittyjä siirtymiä ja animaatioita. Awwwards Site of the Day / Developer Award on toimiston ilmoittama tunnustus. | Premium ei edellytä raskasta WebGL:tä: yrityskohtainen typografia, sommittelu ja sivujen välisten siirtymien hallittu rytmi voivat olla yhtä vaikuttavia. |
| Spline, https://spline.design/web | Interaktiivisen 3D-kohtauksen upotus ja export eri web-pinoihin. | Käyttökelpoinen kokeilu vain kun oikea mallinnus, vientioikeudet, latauskustannus, fallback ja muokattavuus on selvitetty. Ei asiakkaan tuotetta muistuttavaa keksittyä 3D-mallia. |
| React Three Fiber, https://r3f.docs.pmnd.rs/advanced/scaling-performance | `frameloop="demand"` ja invalidointi mahdollistavat tarpeenmukaisen renderöinnin. | Interaktiivinen viewer ei saa pyörittää turhaa 60 fps renderöintiä silloin kun sisältö ei muutu. |
| GSAP ScrollTrigger, https://gsap.com/docs/v3/Plugins/ScrollTrigger/ | Tukea scrollin etenemiseen sidotulle aikajanalle, pinningille ja responsiiviselle sovittamiselle. | Hallittu scrollytelling vain, jos se auttaa ymmärtämään yritystä; normaalin skrollauksen ja sisältölinkkien on pysyttävä käytettävinä. |
| Chrome modern motion guidance, https://github.com/GoogleChrome/modern-web-guidance-src/blob/main/guides/ui-behaviors/motion/guide.md | `transform` / `opacity` ovat ensisijaisia sujuvalle animaatiolle; reduced-motion huomioitava. | Toteutus priorisoi luettavuutta, compositing-suorituskykyä ja tarkoitusta eikä efektien määrää. |

Nämä ovat suunnittelureferenssejä, **eivät** asiakkaan faktalähteitä, mallien käyttöoikeusperusteita, kokeellisen 3D:n pakkoa tai todiste 9.5/10-laadusta.

## Valitse toteutustaso ennen ensimmäistä Builder-kutsua

Valinta perustellaan `premium_experience_plan` / `visual_direction_plan` -briefissä jokaiselle sisältöreitille.

- **A — arkkitehtoninen premium:** Vahva sommittelu, aidot laadukkaat tuotekuvat, rytmi, tilat, ilmava/hillitty typografia, oikeat materiaalit, kuvapari, yksi tarkoituksellinen hover/avausefekti. Hyvä oletus palveluyrityksille ja puutteelliselle kuvamateriaalille. Ei 3D-mallia.
- **B — elävä työnäyte:** Yrityksen oma työn/video aineisto, liikkeen maltillinen paljastuminen, syvyyttä tukevat aitoon valokuvaan perustuvat pienet perspektiivimuutokset, before/after silloin kun aineisto on totta, valikoitavat vaihtoehdot ja kuvagalleria. Hyvä puusepille, arkkitehdeille, restauroinnille ja työtä näyttäville yrityksille. Kosketus ja reduced-motion tasavertaiset.
- **C — aito interaktiivinen 3D:** Todellinen tuote/tila/prosessi, oikeudenhaltijan hyväksymä malli tai teknisesti lähteistetty havainne, aidot materiaalit ja mittasuhteet. `<model-viewer>`, Three.js / React Three Fiber tai Spline vain perustellussa tapauksessa; SVG/CSS-tasot ja kevyet kuvasekvenssit silloin kun ne vastaavat tehtävään paremmin. Staattinen posterikuva, HTML-sisältö ja toimiva CTA aina mukana; fallback myös hitailla puhelimilla, verkkovirheessä ja ilman WebGL:ää. Malli ei saa olla tekaistu kuva yrityksen tuotteen tarkasta rakenteesta.

Valitse korkein *todistein perusteltu*, ei teknisesti raskain. Alkuperäisen sivun vahva video/3D/galleria tulee säilyttää tai todella parantaa. Alkuperäisen hillitty ulkoasu ei kiellä hienovaraisesti vahvistettua tilan tuntua.

## Art direction ja materiaalin laatu

1. Käy lähdesivun hero, kohdistus, pintastruktuurit, liikkeet, videot ja avainkuvat läpi myös mobiilissa. Tunnista mikä on brändin tunnistettava piirre; älä korvaa sitä Kaurivo-yleisgradientilla.
2. Valitse yrityksen oman tuotteen havainnollistamiseen käyttötarkoitus: esim. oven rakenne, materiaalin vaihtoehdot, työn vaiheet tai myytävän esineen mittasuhteet. Kirjaa havaittava asiakashyöty ennen 3D-tekniikkaa.
3. Materiaalit ja valaistus: 3D:n uskottavuus syntyy mittakaavasta, silueteista, sopivasta roughness/metalness-asetuksesta, aidosta ympäristöheijastuksesta ja selkeästä suunnatusta valosta — ei valokuvan päällä kulkevasta hohtopallosta. Ei keksittyjä logoja, tuotteita, varastoarvoja tai asiakastyön vaiheita.
4. **Korkean riskin kielletty oletustekniikka** aidon kuvan päällä: `radial-gradient(... at var(--mouse...))`, `mix-blend-mode:screen` + radial glow, `pointermove`-sidottu valokeila, jatkuvasti heilahteleva lasiheijastus. Poikkeus vaatii asiakkaan brändiin liittyvän lähdenäytön ja hyväksynnän. Tavallinen reunoja tasaava staattinen kontrastigradientti, todellinen valokuvan valo tai hillitty värikalvo eivät ole automaattisesti sama asia.
5. 3D-objektille liikeakseli ja kameran kulku eivät saa johtaa epätodenmukaiseen muotoon, skaalavirheeseen tai katkenneeseen perspektiiviin. Käyttäjä saa tauottaa/pysäyttää ylimääräisen liikkeen ja ymmärtää sisällön ilman animaatiota.
6. Hienostunut liike on **ajoitettua ja merkityksellistä**: pääelementit avautuvat hallitusti, galleria reagoi täsmällisesti, navigointi on nopea, kuvat tukevat sisällön järjestystä. Älä lisää useita eri easing-tyylejä, jokaiseen korttiin kallistusta, lumisadetta, cursor trails -efektiä tai sekavia scroll-sidonnaisuuksia.
7. Suunnittele koko sivuston formaatti: etusivu ei ime kaikkea laatua. Eri asiakastehtävien alasivuilla tulee olla oma tarkoituksenmukainen kompositio, media ja interaktio. Ei toistuvaa yritysvaihdolla toimivaa split-hero + suuret otsikot + numeroidut kortit -mallia.

## Toteutustapa ja kustannukset

- Oletus: CSS native transitions, IntersectionObserver vain näkyviin tuleville elementeille, valinnainen scroll-driven CSS kun tuettu, `transform` ja `opacity`, ei pääsäikeen jatkuvaa vierityspollingia. Rajoita `will-change` vain aktivoituihin elementteihin.
- GSAP/ScrollTrigger perustellusti, **ei** pakollisena riippuvuutena eikä scrollin kaappaamiseen. `pin` ei saa peittää CTA:ta tai lukita sisällön lukemista. Testaa takaisin vieritys, ankkurit, resize ja selaimen Back.
- Three.js/R3F vasta todellisen 3D-tarpeen jälkeen. Lataa kohtaus laiskasti, käytä optimoitua glTF/GLB-sisältöä, oikeaa kuvatarkkuutta/texture-kompressiota, `frameloop=demand` tai pysäytä loop kun näkymä ei muutu; karsi tarpeettomat valot, varjot ja jälkikäsittely. `devicePixelRatio` ja quality tier mukautuvat laitteeseen. WebGPU ei ole ainoa sallittu renderöintipolku; tarjoa WebGL/kuvafallback.
- Spline-/kolmannen osapuolen embed on **valinnainen** ja vaatii maksuttomuuden/rajojen, yksityisyyden, offlinen, CMS-editoinnin, vientioikeuksien ja liiketoimintariippuvuuksien tarkastuksen ennen käyttöönottoa. Ei hankita maksullista työkaluja ennen ensimmäistä myyntiä vain vaikutelman vuoksi.
- LCP-kuvan ei pidä odottaa 3D-skeenen latautumista. Näytä merkityksellinen poster/hero heti. Käytä todellisia kuvakokoja, responsiivisia kuvia ja cachea. CSS-teksti ja CTA toimivat ennen kohtauksen käynnistystä.
- Älä käytä luvattomia 3D-malleja, logoja, valokuvia tai upotuksia. Julkisesta alkuperäissivusta haettu kuva on suunnittelun referenssi, ei käyttöoikeuden todistus.

## Automaattinen QA ja itsenäinen kriittinen arviointi

**Ennen rakentamista:** kirjaa reitille `business_purpose`, `source_visual_evidence`, `effect_tier=A|B|C`, `why_this_effect`, `model_and_media_provenance`, `fallback`, `stop_conditions`. Tason C kohdalla mallin aitous, tuoteyhteys ja luvat ovat lisäehdot; jos ne puuttuvat, palaa A/B-tasoon, älä keksi objektia.

**Build/preflight:** käytä yhteistä `audit_visual_motion`-porttia koko HTML/CSS/JS-kokonaisuuteen; tunnista keinotekoinen valokeila oikean kuvan päällä, reduced-motion-vaatimukset ja ulkoisten resurssien tutkimattomuus. Pakolliset puutteet estävät hyväksynnän; tarkistus ei väitä mittaavansa kauneutta. Havainnon tarvitsema ulkoinen CSS/JS ei saa muuttaa `pending`-tilaa hyväksynnäksi.

**Browser QA:** oikeat 320/390/768/1440-kuvat kaikilta reiteiltä; 3D/CTA ennen latausta, kuvien rajaus, alt ja gallery-dialog; hover/pointerleave, touch/keyboard, normal/reduced-motion, JS-disabled fallback, slow-loading fallback, normaali scroll-ankkurikäytös. Kriittisessä interaktiossa testaa myös 3D zoom/rotate, state reset, kaksi erilaista laitetasoa ja mahdollinen canvas context loss. Todennettava aikataulu ja mittari tarvitaan ennen kuin väitetään laitteessa sulavaksi.

**Riippumaton renderöity arvio:** lähde vs uusi, 3 aivan erilaista aiempaa asiakastoteutusta, kaikki keskeiset alasivut ja mobiili. Kysy samalla **onko tämä oikean asiakkaan tuote vai koristeltu demopohja**. Kirjaa huomioiden sisältö, typografia, kuvan valintojen laatu, tyhjä tila, pintamateriaalit, valaistus, navigointi, myynnillinen polku ja suorituskyky. Visuaalinen testiarvio ei saa olla sama agentti, joka teki sivun. Ei todistettua arviota → `PENDING`.

**Yksi arvosana:** Sivustolla vain **kokonaisarvio x/10**, jonka sisällä premium-vaikutelma on mukana. Älä julkaise rinnakkaista `premium x/10` -lukua; osa-alueiden havainnot jäävät korjausdiagnostiikaksi. Nykyinen ulkoinen vähintään 9,5/10-vaatimus, erilliset toiminnalliset portit, CMS, oikeudet ja oikean asiakkaan hyväksyntä pysyvät.

**Oppiminen:** tallenna ensimmäisen uuden yrityksen muuttumaton tulos, juurisyy, yleinen sääntö, fixture-testi ja seuraavan eri toimialan sokkotesti. Sama asiakas korjattuna ei todista, että koko rakentaja parani.
