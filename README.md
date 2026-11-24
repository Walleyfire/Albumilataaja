# Albumilataaja

Suomenkielinen Windows 10/11 x64 -sovellus musiikin lataamiseen. Tavallinen sovellusikkuna, ei konsolia. Pythonia tai erillisiä komentorivityökaluja ei tarvitse asentaa.

**[Lataa uusin versio](https://github.com/Walleyfire/Albumilataaja/releases/latest)** · **[Ilmoita ongelmasta](https://github.com/Walleyfire/Albumilataaja/issues)**

Uusi tumma ulkoasu ja koko latausjonon aika-arvio ovat mukana [julkaisussa 1.1.0](https://github.com/Walleyfire/Albumilataaja/releases/tag/v1.1.0).

## Asennus

1. Avaa **Lataa uusin versio** ja julkaisun **Assets**-lista.
2. Lataa **Albumilataaja-Setup.exe** ja käynnistä se.
3. Valitse suomi ja seuraa asentajan ohjeita. Voit luoda työpöydän pikakuvakkeen.
4. Käynnistä **Albumilataaja** työpöydältä tai Käynnistä-valikosta.

Asennus tapahtuu omaan käyttäjäprofiiliin ilman järjestelmänvalvojan oikeuksia. Oletuskansio on `%LOCALAPPDATA%\Programs\Albumilataaja`. Asentaja sisältää tarvittavat lataus- ja äänenkäsittelytyökalut. Sovelluksella ja asentajalla ei ole koodin allekirjoitusvarmennetta.

**Ilman asennusta:** lataa **Albumilataaja-portable.zip**, pura ZIP kokonaan omaan kansioon ja käynnistä sen sisältä **Albumilataaja.exe**. Säilytä **tools**-kansio exe-tiedoston vieressä. Pelkkä exe-tiedoston kopioiminen ei riitä. Portable-version päivityspainike avaa tavallisen asentajan.

## Artistin albumit YouTubesta

1. Valitse **Lähde → YouTube**.
2. Kirjoita artistin nimi ylimpään hakukenttään ja paina **Hae artisti**.
3. Valitse hakukentän alapuolisesta listasta oikea artisti.
4. Valitse, otetaanko mukaan **Singlet ja EP:t**.
5. Paina **Näytä julkaisut**. Julkaisut näkyvät uusimmasta vanhimpaan.
6. Valitse haluamasi albumit: **Ctrl** valitsee erillisiä rivejä, **Shift** rivivälin ja **Valitse kaikki** koko listan.
7. Valitse **Tallennuskansio**, **Muoto** ja **Kansiomuoto**.
8. Paina **Lataa valitut julkaisut**. Edistyminen ja virheet näkyvät ikkunan alareunassa.

**Suorat linkit:** liitä albumilistan alla olevaan moniriviseen kenttään yksi tai useampi YouTube-videon tai albumisoittolistan https-linkki, **yksi linkki riville**, ja paina **Lataa linkit**. Kaikki linkit käsitellään samassa jonossa syöttämässäsi järjestyksessä. Tyhjät rivit ja täsmälleen samat toistuvat linkit ohitetaan. Jos jokin rivi on virheellinen, korjaa ilmoitettu rivi ennen latauksen aloitusta.

Linkit ladataan peräkkäin; jokaisen albumin tai videon musiikki tallennetaan valitun kansiomuodon mukaisesti. Latauspalkki ja aika-arvio koskevat koko linkkijonoa. Myös Spotify-tilassa voit liittää useita sen palvelun linkkejä yksi riville.

## Spotify ja spotDL

Valitse **Lähde → Spotify**.

### Lataaminen linkistä

1. Avaa Spotifyssa artisti, albumi, soittolista tai kappale.
2. Valitse sen valikosta **Jaa → Kopioi linkki**.
3. Liitä `https://open.spotify.com/...`-linkki sovelluksen linkkikenttään.
4. Valitse tallennuskansio, tiedostomuoto ja kansiomuoto.
5. Paina **Lataa linkit**.

Artistin linkki pyytää spotDL:ää käsittelemään löytämänsä tuotannon. Albumin linkki käsittelee yhden albumin. Tämä versio ei sisällä Spotify-kirjautumista eikä yksityisten soittolistojen tai käyttäjän tallennettujen kappaleiden lataamista.

### Julkaisujen esikatselu

Kirjoita ylimpään hakukenttään artistin nimi tai Spotify-artistilinkki ja paina **Hae artisti**. Valitse hakutuloksista oikea artisti ja paina **Näytä julkaisut**. Valitse albumit listasta ja paina **Lataa valitut julkaisut**. Artistihaku ja koko albumilista haetaan erillisellä katalogityökalulla; spotDL lataa vasta valitut albumit.

Spotify-artistihaku on korjattu: testissä **Eppu Normaali** löytyi nimellä ja listaan haettiin **53 julkaisua** sivutuksen kautta. Julkaisutietojen haku ei lataa kappaleita eikä käy ensin läpi jokaisen kappaleen metatietoja. Jos palvelu ei vastaa, haku aikakatkaistaan kolmen minuutin jälkeen. Haun voi myös keskeyttää.

**spotDL käyttää Spotifya kappaletietoihin ja etsii äänen yleensä YouTubesta. Se ei lataa Spotifyn alkuperäisiä äänitiedostoja.** Vastaava kappale voi jäädä löytymättä tai löytyä eri versiona.

## Kansiot ja albumien järjestys

**Kansiomuoto**-valitsimella on kolme vaihtoehtoa, jotka toimivat molemmilla latauslähteillä:

```text
Albumi, Vuosi (oletus):
Musiikki/
└── Artisti/
    └── Albumin nimi, 2026/
        ├── 01 - Kappale.flac
        └── 02 - Toinen kappale.flac

Suoraan tallennuskansioon:
Musiikki/
├── Kappale [tunniste].flac
└── Toinen kappale [tunniste].flac

Vuosi - Albumi:
Musiikki/
└── Artisti/
    ├── 2026 - Uusin albumi/
    ├── 2024 - Edellinen albumi/
    └── 2020 - Vanhempi albumi/
```

Valitse **Suoraan tallennuskansioon**, kun haluat kappaleet suoraan valitsemaasi kansioon ilman artisti- ja albumialikansioita. Tämä toimii molemmilla latauslähteillä, myös usean linkin jonossa. Esimerkiksi tallennuskansio `D:\Musiikki` tarkoittaa, että kappaleet tulevat suoraan siihen. Valinta tallentuu asetuksiin.

Kappaletiedostojen tarkka nimi riippuu latauslähteestä. YouTube-nimissä on mukana videon tunniste. Spotify-nimissä on tavallisesti levy- ja kappalenumero; suorassa tallennuksessa nimi on **[Spotify-tunniste] Artisti - Kappale**, jotta samannimiset kappaleet eivät korvaa toisiaan.

Valinta ei siirrä aiemmin ladattuja tiedostoja. Spotify käyttää suorassa tallennuksessa erillistä lataushistoriaa, joten aiemmat albumikansioihin tehdyt lataukset eivät estä saman kappaleen lataamista suoraan tallennuskansioon.

- Albumilista ja valittujen julkaisujen latausjono ovat **uusimmasta vanhimpaan julkaisuvuoden perusteella**, kansiomuodosta riippumatta. Saman vuoden julkaisut ovat nimen mukaan. Tuntemattomat vuodet tulevat viimeiseksi.
- Jos haluat myös Resurssienhallinnan albumikansiot uusimmasta vanhimpaan, valitse **Vuosi - Albumi** ja Resurssienhallinnassa lajittelu **Nimi, laskeva**. Sovellus ei muuta Resurssienhallinnan asetuksia.
- Albumikansioita käytettäessä suoran YouTube-linkin kansiot perustuvat kanavan ja soittolistan nimeen. Vuosiluku lisätään, jos julkaisuvuosi löytyy tiedoista.
- Paina **Avaa kansio** nähdäksesi tallennetut kappaleet.
- Kansiomuodon vaihtaminen koskee seuraavia latauksia. Se ei nimeä jo ladattuja kansioita uudelleen. Eri muoto voi siksi luoda samasta albumista toisen kansion.

## Tiedostomuoto ja äänenlaatu

| Muoto | Käyttö |
|---|---|
| FLAC | Häviötön tallennusmuoto, suuret tiedostot. |
| Opus | Pienemmät tiedostot, sopii hyvin YouTube-lähteeseen. |
| MP3 | Laaja soitinyhteensopivuus. |
| M4A | Yleinen äänen tallennusmuoto. |

**YouTuben ääni on jo häviöllisesti pakattu. FLAC-muunnos ei palauta menetettyä äänenlaatua.** Sama koskee spotDL:ää, kun ääni tulee YouTubesta. Koko tuotannon, oikean kappaleversion tai kaikkien metatietojen löytymistä ei taata. Käytä sisältöä, jonka lataamiseen sinulla on oikeus.

## Keskeytys ja jatkaminen

Latausloki näkyy ikkunan alareunassa aiempaa suurempana. Siinä on vierityspalkki ja pitkät rivit rivittyvät. **Piilota console** piilottaa lokin ja **Näytä console** palauttaa sen näkyviin. Lokitietoja kertyy myös piilotettuna. Näkyvyysasetus muistetaan seuraavalla käynnistyksellä.

Paina **Keskeytä** pysäyttääksesi toiminnon. Valmiit kappaleet säilyvät. Käynnistä sama lataus myöhemmin uudelleen samalla tallennuskansiolla, kansiomuodolla ja tiedostomuodolla: jo ladatut kappaleet ohitetaan. Keskeneräinen kappale voidaan ladata uudelleen. Latausarkistotiedostot säilyttävät tiedon valmiista latauksista.

## Tumma käyttöliittymä ja koko latausjonon aika-arvio

Sovelluksen tausta on musta/tumma, painikkeet ovat pyöristettyjä ja Windowsin ikkunapalkki käyttää samaa tummaa teemaa. **YouTube** käyttää punaisia ja **Spotify** vihreitä korostuksia. Julkaisulista mukautuu teemaan. Näkyviä vierityspalkkeja ei ole; listaa ja lokia voi vierittää hiiren rullalla.

Latauspalkki seuraa **koko valittua jonoa**, ei pelkästään yhtä kappaletta. Sen alla näkyvät käsitellyt julkaisut, kokonaisprosentti ja likimääräinen jäljellä oleva aika, esimerkiksi **Koko jono · 25 % · 2/8 julkaisua · noin 18 min jäljellä**. Aika-arvio perustuu toteutuneeseen nopeuteen ja julkaisujen edistymiseen. Se tarkentuu työn edetessä; eri kokoiset albumit, verkkoyhteys ja äänen muuntaminen voivat muuttaa arviota. Alussa näytetään **lasketaan aika-arviota**. Keskeytettyä jonoa ei näytetä valmiina.

## Päivitykset

1. Sovellus tarkistaa uusimman vakaan GitHub-julkaisun käynnistyessään. Voit tarkistaa myös painikkeella **Tarkista päivitykset**.
2. Jos uusi versio löytyy, sovellus kysyy, päivitetäänkö nyt. Voit hyväksyä tai kieltäytyä. Kieltäytyessä nykyinen sovellus jää käyttöön ja seuraava käynnistys tarkistaa päivitykset uudelleen.
3. Asentajan SHA-256 tarkistetaan julkaisun **SHA256SUMS.txt**-tiedostosta. Virheellistä latausta ei avata.
4. Hyväksytty päivitys asentuu automaattisesti, näyttää asennuksen edistymisen ja käynnistää sovelluksen uudelleen. Asennus tehdään samaan sovelluskansioon. Musiikkikansio ja asetukset säilyvät.

Päivityksen jälkeinen uudelleenkäynnistys käyttää omaa uutta ajonaikaista kansiota. Tämä korjaa aiempien versioiden **Failed to load Python DLL** -virheen. Korjaus on myös asentajassa, joten päivitys vanhasta versiosta toimii. Jos vanha versio näyttää virheen ennen päivittämistä, sulje virheilmoitus ja avaa sovellus uudelleen pikakuvakkeesta tai käynnistä uusin asentaja käsin. Pythonia ei tarvitse asentaa erikseen.

Päivitys asennetaan hyväksynnän jälkeen ilman asennusvelhon läpikäyntiä. Tarkistussumma varmistaa tiedoston eheyden; julkaisuja ei ole digitaalisesti allekirjoitettu. Päivitys sisältää myös mukana toimitetut latausmoottorit, joita ei päivitetä erikseen sovelluksesta. Portable-versiokin päivittyy nykyiseen kansioonsa asentajan kautta ja rekisteröityy Windowsiin asennetuksi sovellukseksi.

## Ongelmatilanteet

### Spotify: AudioProviderError / YT-DLP download error

Päivitä sovellus vähintään versioon 1.1.3. Spotify käyttää spotDL:ää kappaleiden kohdistamiseen, metatietoihin ja albumikansioihin, mutta hakee äänen samalla mukana toimitetulla yt-dlp-ohjelmalla ja Deno-asetuksilla kuin YouTube-puoli. YouTube Musicin löytämä video avataan tavallisena YouTube-videona. Tarkka latausvirhe näkyy nyt lokissa; kirjautumispyyntö pysäyttää jonon myös Spotify-tilassa. Pelkkä SABR-varoitus ei tarkoita latauksen epäonnistumista, jos toinen saatavilla oleva äänimuoto toimii.

### YouTube: Sign in to confirm you're not a bot

Tämä on YouTuben kirjautumis- tai varmistuspyyntö. Pelkkä **No title found** on metatietovaroitus; varsinainen latauksen estävä virhe on kirjautumis-/bottivarmistuspyyntö.

1. Avaa YouTube itse selaimessa. Kirjaudu tarvittaessa ja tee YouTuben pyytämä varmistus itse.
2. Jos lataus tarvitsee kirjautumisistunnon, vie itse selaimesta YouTuben evästeet Netscape-muotoiseen `cookies.txt`-tiedostoon. Katso yt-dlp:n [evästeohje](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp) ja [YouTube-kohtainen vientiohje](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies).
3. Paina sovelluksessa **YouTube-evästeet** ja valitse tiedosto omalta koneeltasi. Valinta koskee sekä YouTube-latauksia että spotDL:n YouTubesta hakemaa ääntä.
4. Käynnistä sama latausjono uudelleen. Valmiit kappaleet säilyvät ja ne ohitetaan lataushistorian perusteella.

Sovellus ei lue selaimen profiilia tai vie evästeitä automaattisesti. Asetuksiin tallennetaan vain valitun tiedoston polku; latausmoottori käyttää sen evästeitä verkkopalvelun kirjautumispyynnöissä. Jokainen YouTube- ja Spotify-taustaprosessi saa oman väliaikaisen työskentelykopion: latausmoottorin tekemät evästemuutokset eivät tallennu valitsemaasi alkuperäiseen tiedostoon. Kopio poistetaan prosessin päätyttyä myös virheessä tai keskeytyksessä. Lähteen vaihtaminen ei muuta alkuperäistä tiedostoa. **Älä lähetä evästetiedostoa chattiin, GitHubiin tai muille ihmisille:** se voi sisältää tilillesi pääsyn mahdollistavia tietoja. **Poista valinta** lopettaa tiedoston käytön poistamatta alkuperäistä tiedostoa.

Evästeet voivat vanhentua eivätkä ne takaa latauksen onnistumista. YouTube voi rajoittaa pyyntöjä myös muista syistä. Latausjono pysähtyy varmistuspyyntöön, ja latausten välissä käytetään lyhyttä taukoa. Käytä kirjautumista vain tarvittaessa; yt-dlp:n ohje varoittaa tilin käyttöön liittyvistä rajoituksista.

| Ongelma | Ratkaisu |
|---|---|
| Artisti ei löydy | Tarkista kirjoitusasu tai käytä suoraa albumilinkkiä. |
| Spotify-artistihaku epäonnistuu | Tarkista päivitykset, kokeile uudelleen tai käytä artistin tai albumin suoraa linkkiä. |
| Kappale jää lataamatta | Katso loki. Sisältö voi olla poistettu, alueella estetty tai vaatia kirjautumisen, jota tämä versio ei tue. |
| Puuttuva työkalu | Asenna sovellus uudelleen tai pura portable-paketti kokonaan. |
| Päivitystarkistus epäonnistuu | Tarkista verkkoyhteys ja kokeile myöhemmin. Asentajan voi ladata myös GitHub Releasesista. |
| Julkaisuja puuttuu | Tarkista **Singlet ja EP:t** ja hae uudelleen. Palvelun valikoima voi silti olla puutteellinen. |
| Kansiot eivät näy uusimmat ensin | Käytä kansiomuotoa **Vuosi - Albumi** ja Resurssienhallinnan lajittelua **Nimi, laskeva**. |

Ongelmailmoituksessa kerro sovelluksen versio, valittu lähde, ongelmaan johtaneet vaiheet ja tarvittava osa lokista. Älä lähetä salasanoja, evästeitä tai kirjautumistietoja.

## Asetukset ja poistaminen

Asetukset ovat tiedostossa `%LOCALAPPDATA%\Albumilataaja\settings.json`. Latausmoottorit voivat käyttää myös omia välimuistejaan käyttäjäprofiilissa.

Poista asennus Windowsin **Asetukset → Sovellukset → Asennetut sovellukset → Albumilataaja → Poista asennus** -toiminnolla. Musiikkikansio ja käyttäjän asetukset säilyvät. Portable-version voi poistaa poistamalla puretun sovelluskansion; säilytä musiikki erillisessä kansiossa.

## Kehitys ja julkaiseminen

Lähdekoodi on `lahdekoodi/`-kansiossa. Rakentaminen vaatii Windowsin, Python 3.14:n ja Inno Setup 6/7:n. Aja projektin juuresta PowerShellissä:

```powershell
./lahdekoodi/build.ps1
# Tarvittaessa kääntäjän polku:
./lahdekoodi/build.ps1 -Iscc 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
```

Skripti asentaa Python-riippuvuudet, ajaa testit, lataa lukitut taustatyökalut ja tarkistaa niiden SHA-256:t sekä rakentaa `dist/`-kansioon asentajan, portable-paketin ja tarkistussummat. Versiot ja latausosoitteet ovat tiedostossa `lahdekoodi/tools-lock.json`. Kolmansien osapuolten lisenssit ja lähteet on kuvattu tiedostossa [THIRD_PARTY.md](THIRD_PARTY.md).

Uutta versiota varten päivitä `VERSION` tiedostossa `lahdekoodi/app.py` ja julkaise vastaava Git-tagi, esimerkiksi seuraavana korjauspäivityksenä `v1.1.6`. GitHub Actions testaa ja paketoi sovelluksen sekä julkaisee asentajan, portable-paketin ja tarkistussummat. Pysyvä AppId mahdollistaa päivityksen nykyisen asennuksen paikalle. Sovelluksen päivitystarkistus käyttää uusinta vakaata GitHub-julkaisua.
