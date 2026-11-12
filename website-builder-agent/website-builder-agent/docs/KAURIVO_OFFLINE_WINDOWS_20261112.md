# Kaurivon Windows-rakentaja ilman Codex-kiintiötä

Tämä on **paikallinen Ollama-vaihtoehto**, ei ChatGPT Workin automaattinen
käyttöliittymä eikä lupaus saman mallin laadusta. Käytössä on edelleen Kaurivon
alkuperäinen lähdetutkimus, kolme todellista vertailuyritystä, kolme konseptia,
brändisäännöt, sisältö- ja verkkokauppapariteetti, kuvia ymmärtävä riippumaton
QA ja todellinen julkisen esikatselun selainkoe. Laatuportteja ei madalleta.

## Vanhan Codex-asennuksen vaihtaminen

Sulje Kaurivon aiemman PowerShell-ikkunan rakentaja painamalla **Ctrl+C**.
Siirry Kaurivon `scripts`-kansioon ja suorita (vain komennot, ei
`PS C:\...`-kehotteita):

```powershell
git pull --ff-only
powershell -NoProfile -ExecutionPolicy Bypass -File .\switch_kaurivo_to_offline.ps1
```

Jos Ollama puuttuu, asenna se ensin osoitteesta
https://ollama.com/download/windows. Vaihto tarkistaa ensin kaksi paikallista
mallia: `qwen2.5-coder:7b` (tutkimus/rakennus) ja `llava:7b`
(kuvallinen riippumaton QA). Jos mallit puuttuvat, lataus kysyy lupaa
ja vaatii noin 9–12 GB levytilaa sekä tietokoneelta riittävästi muistia.
Asennus käyttää Internetiä vain mallien lataamiseen. **AI-päättely on
paikallista**, eikä se käytä Codex- tai OpenRouter-kiintiötä.

Kun vaihto on hyväksytty, aloita:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_kaurivo_worker.ps1
```

Vaihtoskripti **ei luo uutta laiteavainta, muuta valmiita demoja,
nollaa työjonoa tai poista yksityisiä tarkistuspisteitä**. Jos käyttäjä
kieltäytyy mallien latauksesta tai visuaalinen QA-malli puuttuu, se ei
vaihda asetusta. Windows-rakentaja estää Codex-taustamallin uudessa
käynnistyksessä.

## Todelliset rajoitukset

* Tämä on ilman erikseen laskutettavaa AI-rajapintaa, ei ilmainen
  rajaton pilvilaskentapalvelu. Sähkö, laitteisto, Internet ja mahdollinen
  hosting voivat maksaa.
* Paikallinen 7B-malli voi olla merkittävästi heikompi ja hitaampi kuin
  ChatGPT Workissa käytetty malli. **Samaa 9,5/10-laatua ei ole
  todennettu**. Ensimmäinen todellinen loppuun asti valmistunut
  vertailudemo on välttämätön.
* Rakentaminen vaatii Windows-koneen, paikallisen Ollaman ja
  riittävät resurssit. Ilman niitä automaattinen worker ei ota työtä
  vastaan. Mallin ajo ei vaadi Codexin viiden tunnin kiintiötä.
* Työjonon oma päivittäinen yritysraja sekä laatuun liittyvä HOLD
  ovat edelleen käytössä. Ne eivät ole Codexin käyttörajoja.
* Huonolaatuista tai rikkinäistä sivustoa ei merkitä valmiiksi:
  hyväksyntä edellyttää riippumatonta QA:ta ja julkaistun sivun
  mobiili/desktop-selainkoetta.

Käyttöönoton loppuhyväksyntä: testaa Koxmaticin aito rakennuspolku,
tarkista kaikki vanhan/uuden sivun linkit ja vertaa valmis demo
alkuperäiseen. Älä ilmoita `internal_preview`-tilaa onnistuneeksi,
ennen kuin tekninen ja visuaalinen todistus on oikeasti olemassa.
