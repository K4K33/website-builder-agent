# Kaurivo — yrityshaun laatu ja verkkosivujen tutkiminen

Päivitetty 31.10.2026. Koodi on GitHub mainissa. Haku ei käynnistä
automaattista markkinointia, myyntiviestejä tai demojen julkaisemista.

## Miten yritykset valitaan?

1. Valtion PRH/YTJ:n avoin data on yritysten **rekisteritietojen**
   lähde. Päähaku saa yhden valtakunnallisen ZIP-arkiston; varahaku saa
   enintään kuusi aluehakua/käynnistys, enintään kolme käynnistystä/päivä
   25 min välein.
2. Poistetaan selvästi asunto-, kiinteistöomistus- ja holdingyhtiöihin
   liittyvät yritykset sekä PRH:n mukaan parhaillaan konkurssissa,
   selvitystilassa tai saneerauksessa olevat.
3. Suositaan sellaisia palvelu- ja asiakashankintaa hyödyntäviä toimialoja
   kuin rakennus-, huolto-, auto-, ravintola-, kauppa-, hyvinvointi- ja
   paikalliset asiantuntijapalvelut. Useita toimialoja pyritään
   tasapainottamaan. Ei keksittyä maksukyky- tai aktiivisuusluokitusta.
4. Sekä yritykset joilla on PRH:n ilmoittama sivusto että ilman
   rekisterilinkkiä olevat ovat mahdollisia liidejä. PRH:n puuttuva URL
   EI tarkoita, ettei yrityksellä olisi oikeaa sivustoa.
5. Y-tunnukseen perustuva deduplikointi ei syrjäytä jo käsin tehtyä
   tutkimusta, rekisteristä löydettyjä sivuja tai merkintöjä.

## Automaattinen verkkosivututkimus: valmius, mutta ei automaattisesti päällä

Yöajossa on erillinen **valinnainen Tavily-hakuvaihe**. Käytössä on
Tavily Searchin virallinen HTTP-API; ei Google/Bing-HTML-scrapingia,
kuvien latausta tai yritysten sähköpostiosoitteiden keräämistä.

Käyttöönotto (vapaaehtoinen; ÄLÄ syötä avainta keskusteluun):

1. Luo ilmainen Tavily Researcher -tili. Heidän 31.10.2026 ilmoittamansa
   ilmaisraja: 1 000 API-krediittiä kuukaudessa, ei maksukorttia.
2. Tarkista palvelun käyttöehdot; tämä työkalu käyttää hakua yritysten
   omien verkkosivujen tunnistamiseen sisäistä, manuaalisesti
   tarkistettavaa yrityslistaa varten.
3. GitHub > K4K33/website-builder-agent > Settings > Secrets and
   variables > Actions > New repository secret.
4. Secretin nimi: **KAURIVO_TAVILY_API_KEY**.
5. Yöajo havaitsee avaimen automaattisesti. Muussa tapauksessa
   palveluntarjoajalle ei tehdä **yhtään** hakupyyntöä.

Kiintiö: yksi **basic**-haku yritystä kohden, **enintään 12
hakua per ajo**. Pääajon ja vara-ajon toteutuessa samana päivänä
enimmäinen ilman manuaalisia uudelleenajoja on 24 hakua/päivä;
31 päivän kuukautena enintään 744 hakua. Mahdolliset ylimääräiset
rerun-ajot voivat nostaa kulutusta, joten tämä ei ole globaalisti
atominen kuukausilukko; käytä Tavily-tilin ilmaistasoa/kovaa rajaa
maksullisen laskutuksen estämiseksi. Päättele ilmaiskiintiö toimittajan
voimassa olevasta tilauksesta. Älä kytke maksullista PAYG-tiliä
automaattisesti.

Hakutulos tallennetaan **ehdotuksena**, ei vahvistettuna yrityksen
sivuna: \`website_candidate_url\`, \`website_candidate_source\`,
\`website_candidate_confidence\`. Vain riittävän selkeään yrityksen
nimeen ja tuloksen otsikkoon perustuva osuma hyväksytään ehdotukseksi.
Ei-hyväksytyt osumat hylätään eikä kotisivun puuttumista väitetä.

Mobiiliadminissa näkyvät erikseen:
- **Tallennettu URL** (ihmisen lisäämä), käsin tutkiminen yhä tarpeen
- **PRH:n ilmoittama URL**, voi olla vanhentunut
- **Hakukoneen URL-ehdotus**, EI vahvistettu
- **PRH ei ilmoita sivua**, ei todiste ettei sivua ole

Joka kortin **Etsi verkkosivu** avaa erillisen hakunäkymän ja
**Tarkista ja tallenna sivu** antaa lisätä löydetyn URL:n sekä
muistiinpanot. Pelkkä URL:n tallentaminen ei merkitse
\`website_verified=true\`.

## Mitä ei voi vielä todeta?

- Yrityksen **todellinen** aktiivinen liiketoiminta, koko, maksukyky
  tai tarve verkkosivu-uudistukselle eivät ole suoraan todistettavissa
  PRH:n peruslistasta.
- Hakukoneen ehdotus ei ole todistettu, ennen kuin sivun omistajuus
  sekä sisältö varmistetaan oikealta sivulta.
- Tämänhetkinen työ ei rakenna eikä julkaise asiakkaan puolesta demoja,
  eikä lähetä yhteydenottoja automaattisesti.
- Automaattinen verkkosivututkimus ei ole käytössä ennen kuin
  erillinen API-avain lisätään GitHubiin. Ensimmäinen oikea
  end-to-end yöajo ja push-ilmoitus pitää varmistaa tuotannon
  ajo- ja tietokantalokeista.

## Viralliset lähteet

- PRH/YTJ API: https://avoindata.prh.fi/fi/ytj/swagger-ui
- Tavily-hinnan ja hakukrediittien tiedot: https://www.tavily.com/pricing
- Tavily API: https://docs.tavily.com/documentation/api-reference/endpoint/search
- Tavily käyttöehdot: https://www.tavily.com/terms
- Yhteydenoton laki-/GDPR-portit: \`docs/KAURIVO_LEGAL_COMPLIANCE.md\`
