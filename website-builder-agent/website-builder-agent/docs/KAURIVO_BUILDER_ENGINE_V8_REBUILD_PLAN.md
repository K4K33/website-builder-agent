# Kaurivo Builder Engine V8 — toteutettava arkkitehtuurin korjaussuunnitelma

**19.11.2026 / tila: toteutussuunnitelma, ei vielä toteutettu ominaisuus.**

V8 EI ole uusi Master Prompt eikä uusien visuaalisten kieltosääntöjen kokoelma. V8 tarkoittaa muutoksia työjonoon, tietolähteiden arviointiin, suunnittelun mallien työnjakoon, visuaaliseen korjaussilmukkaan, koesarjaan ja julkaisuputkeen.

## Todettu lähtötilanne

Kaurivon Supabase-rakennusjono: 28 työtä, 25 `hold`, 3 `failed`, 0 `queued` / hyväksyttyä automaattista previewta tarkistushetkellä. Erotellut estot: 11 `source_research_incomplete`, 4 `researching_failed`, 2 `comparison_free_sources_insufficient`, 1 `concept_browser_validation_blocked`, 1 `design_handoff_incomplete`, 1 `free_ai_access_rejected`, 1 `free_ai_capacity_unavailable`, 4 `paused_for_new_demo` (tarkoituksella) ja 3 `unexpected_worker_error`.

Jo olemassa:
- `scripts/run_kaurivo_demo_queue.py` research → 3 concept → choose → build → QA → enintään 2 revise → publish → public verify; private checkpointit ja OIDC.
- `utils/creative_directions.py` kolme tekstuaalista designsuuntaa, SequenceMatcher-rakennetarkistus.
- `utils/concept_workflow.py`, `utils/kaurivo_staged_visual_review.py`: konseptiscreenshotit ja riippumaton toinen QA-malli, mutta arvioiden kalibrointia ja systeemin rakenteellista oppimista ei ole todistettu.
- `utils/quality_v7.py` staattiset pattern riskit, ei luotettavaa visuaalisen premium-laadun mittaamista.
- `agents/qa.py`: V7:n route-kohtaisessa arviossa minimi 0; muita tarkistuksia säilyy. Mallin arviota EI voi rinnastaa ulkoiseen 9,5/10-arvioon.
- `utils/global_craft_experience.py`: Lando/Dropbox/Igloo on FINAL QA -vertailu; ei asiakkaan värimalli tai lupa kopioida kuvia.

19.11. Oskar Haglund -omistajakonsepti on **manuaalisesti rakennettu**, eikä todista automaattisen Rakenna demo -painikkeen onnistumista. Rekisterin rahtitoimiala ja historiallinen bussitoiminta eivät todista nykyistä palvelutarjontaa. Väripaletin tummanvihreä/lime yrityskohtainen perustelu puuttui. Ei pidä väittää, että värit olisi teknisesti kopioitu Lando Norris -sivustolta; voidaan osoittaa, että suunnittelussa EI ollut riittävää brändiperustelua.

## Arkkitehtuuri

```text
PRH + yrityksen virallinen sivusto + lähteet
             |
      Prospect readiness (P0)
       READY / DEFER / REJECT
             |
 Source Passport + Claim Ledger (P0)
 + Brand Identity Contract (P1)
             |
 Evidence-bounded Creative Director (P1)
 3 oikeasti erilaista renderöityä suuntaa
             |
 Browser first-fold + subpage comparison
        Blind calibrated Critic (P2)
             |
        Selected concept
             |
 Modular site Composer + shared design tokens (P2)
             |
 Technical QA + independent screenshot Critic
             |
 Classified Repair Planner → bounded revision
             |                  |
             +← changed component + new render
             |
 Exact-build artifact + public HTTP/browser verification
             |
 OWNER_PREVIEW / QUALITY_PENDING / SOURCE_BLOCKED
             |
 separate factual rights/owner review and customer/CMS release
```

## P0. Suodata rakennuskelpoiset yritykset ENNEN aloittamista

Uusi `utils/prospect_build_readiness.py`. Lähdedata tulee nykyisestä `kaurivo_crm_prospects`-taulusta ja olemassa olevista browser/source-intake-funktioista; EI rinnakkaista tekaistua tietokantaa.

Sisääntulo: yrityksen id, virallinen URL, tarkistettu yritysnimi/Y-tunnus, palvelulähteet, alkuperäisen sivuston reachability, logo-/valokuvahavainnot, kieli, asiakasmaineen todiste, markkinointikielto, source conflicts. Ulostulo:
- `READY_EXISTING_SITE`: saavutettava alkuperäinen sivu + vähintään yksi todennettu nykyinen palvelu + lähteeseen sidotut brändi- ja sisältöhavainnot + teknisesti tarkastettavat kontaktit
- `READY_VERIFIED_NO_SITE`: yrityksen toiminta vahvistettu riippumattomista lähteistä; identiteetin säilyttäminen ja rights-aukot näkyvästi käsiteltävissä. Erityisen varovainen konseptin tila; EI väitetä lähteetöntä brändiä viralliseksi.
- `RESEARCH_DEFERRED`: saavutettava data ei riitä tai palveluista ristiriita; anna konkreettiset vaadittavat lähteet, älä aloita kalliita kolmea konseptia.
- `INELIGIBLE`: yksityinen/ei julkinen sivusto, markkinoinnista kieltäytynyt, väärä/epäaktiivinen yritys tai muut riippumattomasti todistetut hylkäysperusteet.

Aamun myyntilista ei saa käyttää käsittelemättömiä PRH-rivejä “hyvämaineisina”. Säilytä nykyinen vaatimus vähintään 4/5 ja vähintään 10 varmennettua asiakasarviota; älä keksi yrityksen mainetta. Esitutkimusjono pysyy erillään.

Nimenomaisesti valitun yrityksen painike EI saa hiljaa vaihtaa toiseen yritykseen. Aamun automaattinen demopriorisointi voi valita **seuraavan tutkitun** yrityksen, jos edellinen ei ole rakennuskelpoinen. Käyttöliittymä näyttää suoraan miksi.

Testit: ei julkaistua tai “valmista” työtä `DEFERRED`-tilasta; historiallinen palvelu ei muutu nykyiseksi palveluksi; Google-arvion puuttuminen ei muutu negatiiviseksi tai positiiviseksi arvioksi.

## P0. Lähdeväiteloki ja brändin alkuperäpakko

Uusi `utils/company_claim_ledger.py`:
```json
{
  "claim_id": "current_primary_service_1",
  "text": "...",
  "type": "current_service",
  "source_url": "https://verified-company.example/services",
  "exact_quote": "source excerpt",
  "observed_at": "ISO-8601",
  "confidence": "direct_verified",
  "contradictions": [],
  "publishable": true
}
```
`registered_industry` on eri tyyppi kuin `current_service`. Vain nykyinen suora palvelulähde saa todistaa nykyisen palvelun, ja `contradictions != []` estää väitteen palveluna. Lähteen edellyttämää tekstiä ei päätellä generatiivisesti. `brand_tokens` tallentaa alkuperäisen logon, tekstilogon, värit (computed style sekä kuvahavainto), keskeiset kuvat, lähde-URL:n sekä käyttöoikeustilan. Jokainen generoidun brändin valinta sidotaan lähteeseen tai merkitään tarkistettavaksi konseptiratkaisuksi, ei yrityksen brändiksi.

Toteutus: käytä nykyisiä `utils/brand_design_blueprint.py`, `utils/service_quality.py`, `utils/source_identity.py`; älä korvaa tai höllennä nykyisiä source/rights-estoja.

## P1. Erota Design Director mallista, joka kirjoittaa HTML:n

Uudet `agents/art_director.py`, `utils/design_decision_record.py` ja `utils/design_tokens_from_source.py`.

Art Director saa:
1. lähdepassin, aidot screenshotit ja niiden elementti/typografia/kuva-jakauman;
2. tarkistetut palvelu- ja käyttäjätehtävät;
3. referenssien havainnot **periaatteina**, EI tyylitokeneina tai kopioitavana moodboardina.

Tuottaa versionhallittavan `Design Decision Record` -olion: jokaiselle paletille, fontille, hero-kuvalle, otsikolle, navigaatiolle, motionille ja CTA:lle päätös, liiketoiminnallinen syy, lähdekenttä/asset, sekä `source_verified | proposed_for_review`. Väärä tai puuttuva perustelu pitää päätöksen laatutarkistuksessa.

Ammattilaistason toteutus vaatii kolme rakenteellisesti erilaista ensimmäistä näkymää + vähintään palvelusivun mallia. `utils/creative_directions.py`-tekstin erottelu ei enää yksin riitä: renderöi konseptit, kerää DOM-elementtien ja sisältölohkojen samankaltaisuus, ensikuvan kuvapaikat, värivalinnat, typografiahierarkia ja reittisommittelu. Kolme pelkkää väri-/fonttivarianttia hylätään.

**Vertailujen taiderajaus**: globaalit Lando Norris, Dropbox Brand ja Igloo ovat viimeistelyn, liikkeen ja hierarkian kalibraattoreita. Palettia, fontteja, kuvakieltä, valikoita, otsikoita tai trade dressia ei voi siirtää asiakkaalle tästä syystä. Esimerkiksi dark + lime tulee sallia vain, jos alkuperäinen brändi tai erikseen hyväksytty konsepti perustelee sen. Samat toimialakohtaiset referenssit eivät saa ratkaista asiakkaan brändiä.

## P1. Vakioitu mallien todellinen A/B-koe

Uusi `scripts/benchmark_builder_models.py` + `data/builder_benchmark_cases/` (vain julkiset, oikeudet tarkistetut testitiedot). Käytä 8–12 erilaista yritysprofiilia: autokorjaamo, ravintola, rakentaminen, kauneus, huolto, B2B sekä FI/SV; sisältää 19.11. “Oskar freight vs historic bus” -ristiriitatestin. Lukitse sama source passport, budjetti, renderöintikoko ja tehtävä jokaiselle mallille.

Mittaa erikseen:
- JSON ja art-direction päätösten validius
- ensimmäisellä kerralla läpäisty sisältö-/oikeustarkistus
- täsmälliset sovellettavat kuvat/assetit
- HTML/CSS/JS-komponentin toimivuus
- aidosti erilaisten konseptien osuus
- pakotettu fyysinen 320/390/768/1440 browser test
- sokkoarvioitu visuaalinen uskottavuus, AI-look ja hyödyllisyys, EI oman mallin piste

Käytä vain **livenä vahvistettuja täsmälleen maksuttomia** malleja ja todistettavaa quota-budjettia. A/B-kokeen perusteella valitaan rooleihin Research, Art Director, Builder ja Critic. Älä muuta mallia pelkän benchmarkin maineen perusteella. Ei Ollamaa käyttäjän heikolle PC:lle, ei maksullista fallbackia ilman erillistä käyttäjän hyväksyntää.

## P2. Rakentaminen on kompositiota, ei yksi HTML-automaatti

Uusi `utils/site_composer.py` (soveltaa nykyistä `utils/demo_page_drafts.py`-osiotuotantoa). Tiedostot:
- `design_decisions.json`: lukitut source/approved värit, kuvat, otsikkohierarkia
- `route_specs.json`: joka reitin oma käyttäjätehtävä, sisältö ja toimituskriteeri
- `components/`: luotettavat navigaatio-, lomake-, karuselli-, saavutettavuus- ja mobiilitekniikat
- sivukohtainen vapaa sommittelu: KÄYTETTÄVYYS pysyy yhtenäisenä, visuaalisesta ulkoasusta EI tehdä samaa templaatin värivaihtoa.

Koko sivun rakentaminen vasta, kun kaksi eri viewportia + keskeinen alisivu ovat läpäisseet konseptigaten. Älä generoi kolmea täyttä monisivuista sivustoa, jos kevyemmillä konseptinäytteillä saadaan sama valintatieto. Se säästää ilmaismallien harvoja pyyntöjä.

## P2. Kalibroitu ulkopuolinen Critic ja selittävä korjausmoottori

`agents/qa.py` + `utils/visual_revision.py`:
- browser tekee aidot 320/390/768/1440 kuvat myös kaikki tärkeät alisivut; mitataan overflow, fontin renderöity koko, tekstin leikkaus, interaktiot, contrast, CLS ja assetit.
- toinen riippumaton vision-malli tarkistaa kuvat ilman tekijämallin laatupistemääriä ja katsoo lähteen ja uuden rinnakkain. Se ei saa "perustella" yrityksen puuttuvaa logoa uudella brändillä.
- vertailijoiden arvio `visual_risks`-taso ei riitä: testaa inline-SVG, keksitty kartta, liian pieni navigaatio, geneerinen neutraali/limenvihreä, oikeiden kuvien häviäminen ja otsikon suhde todelliseen sisältöön.
- Critic tuottaa **virhekortit**: `category, severity, route, viewport, screenshot, selector, evidence, business_impact, repair_scope, acceptance_test`.
- korjaus on luokkapohjainen eikä koko sivuston kirjoittamista uudelleen: `color_brand` korjaa tokenin ja kaikki sivut, `hero_content` korjaa lähteen ja rakenteen, `mobile_overflow` korjaa DOM-CSS:n, `source_missing` käynnistää lähdetutkimuksen eikä salli tekstin keksimistä.
- uudelleenrenderöi, testaa täsmällisen vian häviämisen ja tarkistaa regressiot. Laske luotettavat korjausyritykset enintään rajatusti; jos sama vika toistuu, **vaihda suunnittelustrategiaa tai mallia, älä pyöritä samaa promptia**.

Erota koneelliset varmistukset, mallin subjektiivinen arvio ja oikea riippumaton arvio. Mallin “95/100” ei ole todistus 9,5/10 laadusta. V7:n route-min=0-vaikutus tulee tarkistaa erikseen ja estää huonoiksi pisteytetyt sivut ilman ihmisarvion teeskentelyä.

## P0 + P2. Luotettava automaattinen työnkulku

`scripts/run_kaurivo_demo_queue.py` ja `.github/workflows/kaurivo-demo-worker.yml`:
1. Esitutkimuksen kelpoisuus tarkistetaan ennen kalliita mallikutsuja, mielellään ennen aktiivisen työjonopaikan luontia.
2. Työ on **idempotentti**, sisältää stable job id + source SHA + design SHA + build SHA; täsmälleen saman vaiheen toisto ei tuhlaa prompttia/pyyntöä.
3. Persistoi pieniä checkpointteja kunkin onnistuneen vaiheen jälkeen, myös design decision + HTML section + visual-review output. GitHub-runnerin 55 min aikaraja ei saa hävittää jo tehtyä työtä.
4. Erottele `provider_quota_exhausted`, `provider_vision_rejected`, `research_source_unavailable`, `factual_conflict`, `visual_unacceptable`, `render_bug`, `publish_failed`; jokaiselle oma korjauspolku ja rajattu retry.
5. `Rakenna demo` -painikkeen dispatch-ACK ei tarkoita buildin käynnistymistä. Näytä `queued / claimed / researching / designing / building / reviewing / repairing / live_owner_preview` vain palvelimen vahvistamin todistein.
6. Cloud GitHub Actions on todellinen työntekijä. Käyttäjän vähätehoista konetta ei käytetä. Jos toimittajan **ilmainen** malli on pois käytöstä, jatka samaa työtä uudella sallitulla hetkellä; älä lupaa mahdotonta heti-valmiutta tai vaihda maksulliseen.
7. Automaattinen ajastettu listarakentaminen voi hylätä kelvottoman yrityksen ja hakea seuraavan kelvollisen, mutta yksittäinen manuaalinen pyyntö ei saa hiljaa vaihtaa kohdetta.
8. Lähetysten, julkaisun ja arvioinnin tilat erilleen. Puolivalmista ei koskaan merkitä asiakkaalle lähetettäväksi.

## V8-koepatteri (regressiot)

Uudet `tests/test_builder_readiness_v8.py`, `tests/test_design_decisions_v8.py`, `tests/test_visual_repair_v8.py`, `tests/test_builder_qa_calibration_v8.py`, `tests/test_button_to_public_preview_v8.py`.

Pakolliset tapaukset:
- Uudelleenrakentaminen Oskar Haglund -tiedoilla havaitsee tavarankuljetus/bussi-ristiriidan; ei väitä kumpaakaan nykyiseksi palveluksi, ei tekaistua kalustoa; ei markkinoida valmista asiakassivua.
- Sama idea tummanvihreällä/limellä, jossa alkuperäinen lähde ei vahvista värejä, hylätään todellisen brändifideliteetin osalta. Referenssien värien samankaltaisuus ilman brand-evidencea ei ole hyväksymisperuste.
- Kolme tekstuaalisesti erilaista mutta visuaalisesti identtistä konseptia eivät läpäise diversity-valintaa.
- Ensimmäinen konsepti arvioidaan kriittisesti: ei koskaan valita automaattisesti A:ta, eikä hyväksytä yhtäkään huonoa.
- Intro-/logo-/video-/galleria-/allergia-/sponsoriosioita ei saa poistaa lähteen etusivulta tai alisivuilta hiljaa.
- Rakenna demo → juuri saman kirjautuneen adminin yksilöity job → alkuperäiseen yritykseen sidottu live URL → exact-build public smoke → Demot-näkymän oikea linkki.
- Provider rate-limit, runner kill, checkpoint restore, duplicate click, stale SHA ja artifact-mismatch; työtä ei saa kadottaa eikä väärää versiota julkaista.
- Mobiili 320/390/768, desktop 1440; kaikki näkyvät navigoinnit, kielenvaihdot, CTAt, lomakkeet, media ja pienet ikonit.
- Client editability: erillinen todellinen CMS-luovutuksen näyttö, ei staattisen demon kutsumista WordPressiksi.

## Tulokset, joilla kehitystä mitataan

Ensimmäinen hyväksyntäkoe: **5 peräkkäistä rakennuskelpoista yritystä suoraan adminin Rakenna demo -painikkeesta**, eri toimialoja, ilman käsin koodattua demo-sivua tai merkkausta “approved” ulkopuolelta. Kullakin oltava oikein nimetty monisivuinen HTTPS-omistajademo, oikea company id, live HTTP/Chromium-todiste, 0 vakavaa faktavirhettä, 0 rikkinäistä reittiä ja rehellinen käyttölupatila.

Toinen luotettavuuskoe: 20 peräkkäistä kelvollista työpyyntöä, kun ilmaista mallikapasiteettia on saatavilla. Tavoite: vähintään 90 % valmistuu automaattiseksi omistajaesikatseluksi; kaikki poikkeukset luokiteltu toistettaviksi, ei generisiä `unexpected_worker_error`-salaisuuksia. Tulos ei sisällä puutteellisten lähteiden syöttämistä kelvollisina.

Visuaalinen sokkotesti: samoilla 8–12 lähdepaketilla V7 vs V8, **vähintään kolme ihmisen arvioimaa arvioijaa, sokkoarviona**, kriteerit brändin uskollisuus, sisältö, ulkoasun uskottavuus, AI-look, responsiivisuus ja liiketoiminnallinen käytettävyys. V8:n tavoite vähintään +2 pistettä V7:n mediaaniin, AI-look enintään 3/10 ja vakavat lähdeuskollisuusvirheet 0. Pitkän aikavälin 9,5/10 laatutavoite jää ulkoiseksi tavoitteeksi, ei mallin itse julistamaksi luvuksi.

Kustannukset: kaikki benchmark-testin laskurit dokumentoitu; `FREE_ONLY=1` säilyy; ei uutta palvelu-/laitehankintaa ennen ensimmäisen asiakkaan todellista tarvetta ja hyväksyntää.

## Etenemisjärjestys ja PR-jako

| PR | Sisältö | Läpäisy |
|---|---|---|
| V8-01 | `prospect_build_readiness.py`, tri-state + reason | Epävarma Oskar estyy tuotantorakennuksesta; hyvä asiakas jatkaa |
| V8-02 | `company_claim_ledger.py` ja brand token provenance | 100 % palvelu- ja brändiväitteistä lähteistetty tai merkitty konseptiksi |
| V8-03 | stage models A/B benchmark + result JSON | Pystytään vertaamaan roolimalleja samoilla testeillä |
| V8-04 | art director, design decisions + render-first three directions | Tekstuaalinen 3x ero ei kelpaa, oikea ero mitataan |
| V8-05 | compositional builder, reusable engineering components | Kaikki sivut itsenäisiä, mutta yhteinen identiteetti ja toimivat toiminnot |
| V8-06 | independent critic → structured defect cards → targeted repair | Tunnistettu heikko ulkoasu EI pääse läpi; vian korjaus ei riko muuta |
| V8-07 | durable queue/dispatch/heartbeat/checkpoint + owner preview contract | Ei mysteeri-HOLDeja eikä ACK:ta pidetä rakennuksena |
| V8-08 | 5/5 actual admin builds + 20-job test + blind reviewer A/B | Ulkoinen hyväksyntä vasta tosiasiallisesta työn laadusta |

PR:t tehdään **riippuvuusjärjestyksessä**, mutta P0-kelpoisuus ja jonon korjaukset kannattaa aloittaa rinnakkaisina pieninä muutoksina. Jokaisella PR:llä oma epäonnistuva regressiotesti, tuotantokoodin korjaus ja vihreä selaintesti. Yksi vanha jo olemassa oleva kriteeri EI saa poistua siksi, että uusi malli ei sitä läpäise.

## Ei kuulu tähän PR:ään

Tämä tiedosto on vasta koodin toteutusjärjestys. Se EI tarkoita, että yhtään V8-moottoria, mallivertailua tai Rakenna demo -painikkeen päästä-päähän rakennusta olisi tehty. Ei uusia laatupisteitä, ei keksittyä 9,5/10 hyväksyntää eikä yhtään asiakkaalle lähetettyä demoa.
