# Kaurivon Codex-pilotti Windowsilla

Codex käyttää kirjautuneen käyttäjän ChatGPT-tilauksen käyttörajaa. Ollamaa tai paikallisia tekoälymalleja ei tarvita. Windows-kone ajaa edelleen sivun rakentamiseen liittyvät paikalliset työkalut ja Chromium-testit.

## Asenna ja yhdistä kerran

1. Varmista PowerShellissä, että `git --version`, `py -3.11 --version` ja `codex --version` toimivat. [Codex CLI:n asennusohje](https://developers.openai.com/codex/cli).
2. Avaa tämän repon `website-builder-agent/website-builder-agent/scripts`-hakemisto PowerShellissä.
3. Aja `powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_kaurivo_windows.ps1 -Codex`. Kirjaudu Codexiin selaimessa samalla ChatGPT-tilillä, jolla käytät tilaustasi.
4. Kun asennus pyytää Kaurivo-avainta, avaa hallinnan Demot-välilehti ja valitse **Luo Windows-rakentajan avain**. Liitä avain PowerShellin piilotettuun kenttään ja paina Enter.
5. Aja `powershell -NoProfile -ExecutionPolicy Bypass -File .\start_kaurivo_worker.ps1`. Pidä PowerShell auki ja kone hereillä. Jos Git Credential Manager pyytää kirjautumista esikatselun julkaisussa, käytä GitHub-tiliä, jolla on kirjoitusoikeus repoon.

Kun Demot-välilehdellä näkyy, että Windows-rakentaja on käytettävissä, jo jonossa oleva työ voidaan poimia automaattisesti. Uuden yrityksen työ käynnistetään **Rakenna demo** -painikkeella. Sisäinen esikatselulinkki tulee Demot-välilehdelle hyväksytyn laaduntarkistuksen ja julkaistun version selaintestin jälkeen.

Codex-pilotti vaatii kaksi erillistä kuvia ymmärtävää mallia, jotta rakentaja ja visuaalinen arviointi käyttävät eri mallia. Asennus tarkistaa tilin ja malliluettelon ennen kuin työntekijä voi ottaa töitä jonosta.
