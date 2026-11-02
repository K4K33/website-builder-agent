# Kaurivo — brändiuskollinen, yksilöllinen sivustouudistus: ehdottomat standardit
Päivitetty 2026-11-02 usean täysin eri yrityksen V1-testausten ja 8 videon perusteella.

## Estävä laatupoikkeama: geneerinen sama pohja
- Ei kolmea eri alaa samaan HTML/CSS-korttirunkoon eri väreillä. Jokainen työ aloitetaan nollasta toimialan käyttäjätarpeiden, yrityksen nykybrändin, kilpailijavertailun ja aiotun käyttäjäpolun perusteella.
- Ennen suunnittelua tutkitaan vähintään kolme markkinan johtavaa saman toimialan sivustoa, analysoidaan niiden tietohierarkia, tekstin rytmi, toiminnallisuus, layout, kuvat, motion ja konversiopolut. Inspiraatiota ei kopioida orjallisesti.
- **Visuaalinen DNA** pitää erottua käytännössä: omat näyttökohtaiset layouts, palveluiden esitystapa, grid-rakenne, kuva-asettelu, fontit, värien käyttö, painikkeet, animaatiot, sisältöpolku ja ainutlaatuinen graafinen ratkaisu. Pelkkä theme-luokan vaihto ei riitä. Diffaa sivustojen DOM- ja CSS-rakenne automaattisesti; jos samankaltaisia, estä julkaisu.
- Numerointi vain jos numero on itse tietoa (päivämäärä, hinta, vaihe, julkinen tunnus, yrityksen nimi) tai auttaa käyttäjää todistetusti. **EI automaattisia 01/02/03, sarjanumeroita palvelukorteissa, vieressä olevia kellukemerkkejä tai muita jatkuvia koristeellisia järjestysnumeroita.** Oletus: nolla turhaa numerointia.
- Suunnittelun pitää tuntua ihmisen tekemältä. Ei täytekortteja, AI-sloganeita, pakotettuja vastakohtapareja, toistuvia rakenteita, tönkköä ulkopuolista raporttikieltä tai runsaasti tyhjiä palkkeja.

## Brändin pysyvyys
- Käytä asiakkaan TODELLISTA alkuperäistä logoa aina kun mahdollista. Älä korvaa Fixusta/TE-Serviceä, Rosannen lilaa kirjoitusasua tai RI-LI:n keltaista talotunnusta keksityllä tekstilogolla. Jos logoa ei ole saatu riittävän laadukkaana, merkitse logo-hankinta ja julkaisu estetyksi; älä väitä jäljitelmää alkuperäiseksi.
- Säilytä brändin tarkoituksenmukaiset tunnusvärit ja erottuvat elementit; modernisoi rakenteet niiden ympärillä. Erityisesti Rosanne ei ole mielivaltaisesti ruskea vain siksi, että ravintolaväripohja oli ruskea. RI-LI:n tunnuksen keltainen/musta ja TE-Servicen Fixus sininen/keltainen ovat olemassa.
- Asiakkaan omista sivuista löytyvät kuvat inventoidaan, säilytetään oikeilla attribuutioilla suunnittelussa; omistaja- ja tekijänoikeudet tarkistettava ennen myyntikäyttöä. Ennen/jälkeen -kuvat ensin, jos niitä on todella saatavilla ja ne ovat saman todellisen kohteen pari. Älä merkitse kahta eri tilaa samaksi kohteeksi.

## Sisältö ja kieli
- Tee alkuperäisistä KAIKISTA sivuista rivikohtainen lähteistetty inventaario: palvelut, FAQ, hinta, historia, alue, yhteystiedot, aukioloajat, kuvat, galleriat, varaus ja kaikki toimivat linkit. Sisältö saa järjestyä uusiksi, mutta olennainen tieto ei saa hävitä. Eri vanhoilla sivuilla olevat ristiriidat kirjataan, ei arvata pois.
- Kirjoita sivu käyttäjän luettavaksi hyvällä suomella: ”Huollamme kaikki automerkit”, ”Kysy huoltoaikaa”, ”Lounas arkisin 10.30–14.30”. Ei ”yrityksen sivuilla sanotaan”, ”nykyisellä sivulla kerrotaan”, ”yrityksen mukaan”, ellei epävarmuuden tarkka näyttäminen ole olennaista. Kerää epävarmuus- ja lähdetiedot erilliseen demotarkistuslistaan.
- Tietojen oikeellisuus on silti tärkeää: demo ei oikeuta virheellisiä sopimuksia tai harhaanjohtavia lääke-/ruoka-/turvallisuusväitteitä. Asiakas vahvistaa palvelut, hinnat, henkilöt, palautteet ja valokuvien oikeudet ennen julkaisua.
- Ruokalistalla näytetään **koko voimassaololtaan todennettu viikon lista** tai ajantasainen erillinen CMS-lähde, ei etusivulla mielivaltaisia ma/ke/pe-nostoja. Alkuperäiset G/L/M ja ALLERGEENIT siirretään lähdeuskollisesti annoskohtaisesti; allergiamerkintöjä ei keksitä eikä johdeta G/L/M-lyhenteistä. Jos ajantasainen tarkka listaus ei ole vahvistettavissa, sen tilalle rehellinen peruslounasinfo ja linkki oikeaan listaan, ei turvallisuudesta harhaanjohtava ruokalista.
- Menu, hinnat, aukioloajat ja ajankohtaiset tapahtumat ovat päivättyjä ja helposti muokattavia; älä väitä staattista snapshotia live-listaksi.
- Tarvittaessa käyttäjälle avautuva, selkeä sanasto: G gluteeniton, L laktoositon, M maidoton vain lähteen käyttämän merkityksen mukaan. Allergeenit vahvistetaan henkilökunnalta eikä G/L/M korvaa 14 allergeenin täydellistä selvitystä.
- Esitä aidot asiakkaan referenssit / työt galleriana. Jos on varmasti saman projektin ennen/jälkeen kuvat ja niihin lupa, suunnittele vertailukomponentti; älä keksi tapahtumia tai muokkaa kuvia harhaanjohtavasti.

## Julkaisua estävä QA
- Värit ja kontrastit käytännössä: otsikko, sisällön leipäteksti, linkki, palvelukortti, kuvateksti ja painike kaikissa tiloissa. Tarkista vähintään WCAG AA 4.5:1 normaalille tekstille, 3:1 isolle tekstille sekä kohteen näkyvyys.
- Kaikki 320/390/768/1024/1440/1920px; varmista kuvat, kontrasti, scrollin sujuvuus, nav, toiminnallisuus, jokainen linkki ja keyboard focus.
- Saman pohjan käyttö eri asiakkaille = testin FAIL. Koristeellinen numerointi = FAIL. Asiakkaan alkuperäisen logon korvaaminen ilman hyväksyntää = FAIL. Puuttuvat ajantasaiset keskeiset tiedot = FAIL. Puuttuvat ruokavaliomerkinnät tai väärät allergeenit = FAIL. Kontrastivirheet = FAIL.
- Todellinen CMS-asiakasmuokkaus, oikea lomake, tietosuoja ja oman brändin domain vaaditaan tuotantoluovutuksessa. GitHub Pages sisäiset demot eivät ole sallittuja kylmämyynnissä.
- Vasta monen eri toimialan ensimmäisen arviointiversion itsenäinen >=9/10 arvio osoittaa että Builder on oppinut; pelkkä testien läpäisy ei.

## 2026-11-02 kolmen videon havaitut epäonnistumiset
TE-Service: oma Fixus-logo puuttui, liian vähän syvällistä palvelutekstiä ja kankeaa raporttikieltä, identtinen 01-korttigrid.
Rosanne: alkuperäinen lila script-logo puuttui, ruskea valmis teema ei vastannut brändiä, ma/ke/pe-sekoite ja alkuperäiset G/L/M-merkinnät puuttuivat.
RI-LI: alkuperäinen keltainen hymyilevä talologo vaihdettu, palveluissa sama numerokorttisarja, vaaditaan parempi kohde- ja alkuperäisten ennen/jälkeen-kuvien esittely silloin kun aineisto on saatavilla.
Oppi: aiempi kolmiprojektin testi EI ole todistus 9/10 ensiversiolaadusta. Korjaa Builderin prosessi ensin, sitten tee eri visualisoinnit; älä toista samaa perustetta uudestaan.
