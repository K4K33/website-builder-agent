# Kaurivo — tiedon säilymisen ehdoton standardi

Voimassa 2.11.2026 alkaen kaikissa asiakkaan nykyisen verkkosivuston
uudistuksissa, ilman että käyttäjän tarvitsee erikseen muistuttaa.

1. ENNEN DESIGNIA kerää nykyisen verkkosivuston kaikki olennaiset sivut,
   ankkurit, kuvat, PDF:t, palvelulistaukset, hinnat, tuotetiedot, FAQ,
   yhteystiedot, aukioloajat, yritystiedot, referenssit, varaukset, lomakkeet
   ja mahdolliset ajankohtais-/uutissisällöt.
2. Tee sivukohtainen **sisältöinventaario ja lähde-linkki** jokaiselle
   tiedolle. Jaottele: varmistettu, ristiriitainen/vanhentunut, dynaaminen,
   asiakkaan hyväksyntää vaativa tai poistettu perustellusti.
3. Uudessa sivustossa säilytetään KAIKKI nykyisen sivuston olennaiset
   ajantasaiset faktat ja palvelut, ei vain etusivun tärkeimmät kohdat.
   Uusi esitystapa ja tiivistys ovat sallittuja, mutta tiedon katoaminen ei.
   Täysi sisällön vastaavuus varmistetaan erikseen vanhojen ja uusien
   sivujen rivin/kappaleen tasolla ennen asiakkaalle luovutusta.
4. Ajassa muuttuvat menut, hinnat, tarjoukset ja aukioloajat ovat
   lähteistettyjä ajallisia otoksia tai ylläpidettäviä CMS-tietoja.
   Älä näytä tietyn viikon listaa automaattisesti vaihtuvana live-listana.
   Jos vanhat lähteet ovat ristiriidassa, kerro se ja vaadi vahvistus.
5. Väärää veroprosenttia, vanhentuneita lakeja tai turvattomia
   henkilötietolomakkeita EI kopioida. Varmista muuttuneet viranomais-
   tiedot ensisijaisesta lähteestä ja säilytä aiheen näkyvyys oikein.
6. Vanhan sivun kuvat ja brändiomaisuus ovat hyödyllisiä suunnitteluun,
   mutta niiden käyttöoikeus, valokuvattujen henkilöiden lupa ja
   uudelleenjulkaisu tarkistetaan ennen asiakkaille julkaisua. Sisäiset
   ei-indeksoitavat demot säilyttävät selvän konseptimerkinnän.
7. Toimintojen vastaavuus on oma laadunporttinsa. Jos vanhalla sivulla
   on toimiva varaus, kartta, tilaus, editointi tai lomake, toteuta
   vastaava oikeasti toimiva vain kun backend ja tietosuoja ovat valmiina.
   Älä tee kuollutta tai näennäisesti toimivaa nappia.
8. Ennen kuin ensiversio esitellään käyttäjälle, aja ilmaiset
   sisältöpariteetti-, linkki-, mobiili-, selain- ja lomaketestit.
   Lisäksi riippumaton visuaalinen arvio. Aikataulu ei oikeuta
   väittämään saavutetuksi 9/10 tai 9,5/10 ilman todisteita.
9. Asiakkaan omatoiminen muokkaus on luovutusvaatimus: todellinen
   testattu CMS ja opastus, ei staattinen HTML-esikatselu.
10. Asiakkaalle lähetys edellyttää lupaa, brändin omaa HTTPS-domainia
   ja julkaisu-/tekijänoikeusselvitystä. Sisäisiä GitHub Pages -linkkejä
   ei lähetetä kylmäkontaktille.

## Kolmen yrityksen ensimmäinen testi 2.11.2026

TE-Service: https://te-service.fi/
- Alkuperäinen palvelut: määräaikaishuolto, korjaus, erikoisosaaminen,
  ilmastointi, katsastus, pikahuolto, sijaisauto, lasku/osamaksu,
  rengastyöt ja tarjoukset; yrityksen tausta, Tony Eriksson ja kontaktit.
- Omassa uudistuskonseptissa neljä sivua, alkuperäisen palvelusivun
  täysi tekstisisältö tarkistettava vielä ennen ulkoista asiakaskäyttöä.

Rosanne: https://www.ravintolarosanne.fi/
- Lounas, hinnat, kotipulla/kahvila, juhla- ja kokouspalvelut sekä
  kokouspakettien hinnat, historia, grilli, yhteystiedot,
  aukiolojen ristiriidat, vaihtuva viikkolista.
- Lounaslista on nimenomaisesti viikon 2.–6.11.2026 otos, ei live-päivitys.
- Historiallinen Nightclub Rosanne -tieto ja nykyinen aukiolo vaativat
  lisävahvistuksen ennen palvelun markkinointia.

RI-LI: https://www.rakennuspalvelurili.com/
- Omakotitalot, vapaa-ajan asunnot, liiketilat, remontit/huoneistot,
  märkätilat/saunat, laatoitukset, aliurakointi, kohdekuvat,
  yhteystiedot, kysymykset rakentamisen aikatauluista ja luvista.
- Alkuperäisen FAQ:n vanhentunut veroprosentti jätetty pois; tarkista
  Verohallinnolta ennen asiakkaalle luvattua vähennyskelpoisuutta.
- Kuvat ovat alkuperäisillä sivuilla esitettyjä töitä; uudelleenkäytön
  lupa ja kuvien tekijänoikeudet tarkistettava.

Nämä konseptit ovat HTML-pohjaisia, eikä niitä saa väittää
asiakkaan muokattaviksi valmiiksi CMS-tuotannoiksi.
