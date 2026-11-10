# Kaurivo: ensikontaktin toimitettavuus (10.11.2026)

## Mitä korjattiin

- Hallintapaneelin **Kopioi kevyt ensiviesti** -toiminto muodostaa yritys- ja kielikohtaisen (FI/SV/EN) **tekstimuotoisen** otsikon ja viestin. Ensikontaktin luonnos ei sisällä URL-osoitteita, seurantaa, kuvia eikä tiedostoliitteitä. Vastaanottajan pyydettyä esikatselua voidaan toimittaa yksi tarkistettu, suora HTTPS-linkki erillisenä vastauksena.
- Vaatii edelleen vahvistetun yrityksen aktiivisuuden, yksilöllisen havainnon, kielen lähdetiedon ja manuaalisen lainmukaisuustarkistuksen. Estää myös saman yrityksen uuden **ensiviesti**-luonnoksen, jos se on jo merkitty kontaktoiduksi, vastanneeksi, asiakkaaksi tai markkinointikiellon tehneeksi. Manuaalinen Gmail-lähetys ei kuitenkaan ole teknisesti sidottu tähän porttiin.
- Adminiin lisättiin toimitettavuuden diagnostiikkaohje. Se ei näytä "toimitettu Saapuneet-kansioon" ilman vastaanottajan todellista vahvistusta.
- Ei lähetä asiakkaalle sähköposteja, tilaa maksullisia palveluja eikä muuta olemassa olevia kontakteja.

## Miksi Kotifixi-testin Spam-ongelmaa ei voida luvata korjatuksi

Kaurivon lähettäjätilin **Lähetetyt**-kansiossa 3.11.2026 on viisi Kotifixi-viestiä saman päivän sisällä: varsinainen esikatselu, muokkauslinkki, yhteydenottotesti sekä kaksi WordPress ZIP -pakettia. Pelkkä ZIP tai linkki ei selitä ensimmäisen esikatselun mahdollisesti epäonnistunutta luokitusta. Lähettäjän oman postilaatikon MIME-otsakkeet eivät ole vastaanottajan `Authentication-Results` tai Gmailin luokituspäätös. Google ei takaa Saapuneet-kansioon päätymistä.

Ennen myyntiä:
1. Pyydä Kotifixin vastaanottajaa tarkistamaan todellinen kansio (**Spam/Roskaposti** vs **Tarjoukset/Promotions**) ja Gmailin näyttämä syy. Pyydä vain SPF/DKIM/DMARC PASS/FAIL -yhteenveto kohdasta **Näytä alkuperäinen**. Älä kerää/kopioi asiakkaan yksityisiä kokonaisia sähköpostin otsakkeita.
2. Lähetä yksi *luvallinen*, lyhyt tekstimuotoinen testi omiin tai vapaaehtoisiin Gmail- ja Outlook-postilaatikoihin. Testaa mieluiten eri vastaanottajia kuin aiemmin spamista pelastettua lähettäjää. Merkitse aika, palvelu, käytetty lähetysosoite ja vastaanottajan ilmoittama kansio.
3. Jos SPF/DKIM epäonnistuu, selvitä todellinen lähetyspalvelu ja otsakkeet. Nykyinen `hello.kaurivo@gmail.com` käyttää Googlen hallitsemaa gmail.com-verkkotunnusta; **Kaurivo ei voi muuttaa gmail.com:n DNS-tietueita**. Älä yritä julkaista väärennettyjä SPF/DKIM-tietueita omalle sivudomainille, jota ei vielä käytetä lähettämiseen.
4. Jos hankitaan oma lähettävä verkkotunnus, määritä SPF, DKIM ja DMARC postipalvelun ohjeiden mukaisesti, tarkista alignment ja testaa ennen ensimmäisiä asiakasviestejä. Domainin hankinta yksin ei takaa toimitettavuutta.
5. Aloita vain pienestä yksilöllisestä otoksesta, ilman samankaltaisten viestien rykelmää ja ilman ZIP-liitteitä. Pysäytä lähestyminen heti, jos tulee kielto, valituksia tai hylkäyksiä. Vastaanottajan yhteystiedot, laki ja mahdollinen henkilötietojen käsittely on tarkistettava erikseen; tämä koodi ei päättele markkinoinnin laillisuutta.

## Todennettavat rajat

- Ensikontaktin luonnos on pelkkä sähköpostin **Aihe** + viestiteksti. Otsikko on liitettävä Gmailin aihe-kenttään erikseen. **Sitä ei lähetetä Kaurivon administa**.
- ZIP-paketteja ei saa liittää kylmään ensiyhteydenottoon. Henkilökohtaista muokkauslinkkiä, tunnusta tai kirjautumista ei pidä jakaa ensiyhteydenotossa.
- Myyntiesikatseluja ei saa lähettää asiakkaille ennen nykyisiä erillisiä sivuston luovutus-/oikeus-/laatuportteja.
- SPF/DKIM/DMARC-tuloksia ja todellista inbox placement -tulosta ei vielä ole; tätä ei saa esittää korjattuna.
- Lähde: https://support.google.com/mail/answer/81126?hl=fi ja https://support.google.com/mail/answer/1366858?hl=fi.
