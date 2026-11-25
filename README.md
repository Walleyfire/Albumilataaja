# Albumilataaja

Suomenkielinen Windows 10/11 x64 -sovellus musiikin lataamiseen YouTube- ja Spotify-linkeistä. Sovellus sisältää tarvittavat taustatyökalut. Pythonia tai komentorivityökaluja ei tarvitse asentaa erikseen.

**[Lataa uusin versio](https://github.com/Walleyfire/Albumilataaja/releases/latest)** · **[Ilmoita ongelmasta](https://github.com/Walleyfire/Albumilataaja/issues)**

## Asennus

1. Avaa **Lataa uusin versio** ja julkaisun **Assets**-lista.
2. Lataa **Albumilataaja-Setup.exe** ja käynnistä se.
3. Seuraa asentajan ohjeita. Voit luoda työpöydän pikakuvakkeen.
4. Käynnistä Albumilataaja työpöydältä tai Käynnistä-valikosta.

Asennus tehdään omaan käyttäjäprofiiliin ilman järjestelmänvalvojan oikeuksia. Oletuskansio on `%LOCALAPPDATA%\Programs\Albumilataaja`. Sovellusta ja asentajaa ei ole allekirjoitettu koodin allekirjoitusvarmenteella.

**Portable:** lataa **Albumilataaja-portable.zip**, pura koko paketti omaan kansioon ja avaa **Albumilataaja.exe**. Säilytä **tools**-kansio exe-tiedoston vieressä. Pelkkä exe-tiedoston kopioiminen ei riitä. Portable-versiokin päivittyy asentajan kautta nykyiseen kansioonsa.

## Lataaminen linkeistä

1. Valitse lähteeksi **YouTube** tai **Spotify**.
2. Liitä yksi tai useampi kyseisen palvelun https-linkki kenttään, **yksi linkki riville**.
3. Valitse **Tallennuskansio**, **Muoto**, **Kansiomuoto** ja **Latauksia kerralla**.
4. Paina **Lataa linkit**.
5. Seuraa kappaleita **Lataukset**-taulukosta.

Tyhjät rivit ja täsmälleen samat toistuvat linkit ohitetaan. Virheellisen linkin rivinumero ilmoitetaan ennen latauksen aloitusta.

- **YouTube:** yksittäiset videot sekä albumi- ja muut soittolistat. Myös YouTube Music -linkit käyvät.
- **Spotify:** artistin, albumin, soittolistan tai kappaleen linkit. Artistilinkillä julkaisut haetaan automaattisesti ja jonotetaan uusimmasta vanhimpaan, myös singlet ja EP:t.

**SpotDL käyttää Spotifya kappaletietoihin ja etsii äänen YouTubesta. Se ei lataa Spotifyn alkuperäisiä äänitiedostoja.** Vastaava kappale voi jäädä löytymättä tai löytyä eri versiona. Spotify-kirjautumista ja yksityisiä soittolistoja ei tueta.

## Kappalekohtainen lataustaulukko

Taulukossa näkyvät **kappale ja artisti**, **albumi**, **lähde**, **tila** sekä oikeassa reunassa **virhe**. Kunkin tiedoston tila päivittyy erikseen, myös rinnakkaislatauksissa.

Tilat ovat **Jonossa**, **Etsitään ääntä**, **Ladataan**, **Muunnetaan**, **Valmis**, **Ohitettu**, **Virhe** ja **Keskeytetty**. YouTube-latauksen prosentti näkyy tiedoston rivillä. Spotifyssa näytetään haun, latauksen ja muunnoksen vaiheet. Valmis rivi korostuu vihreänä. Virheen teksti näkyy punaisena oman tiedostonsa oikealla puolella.

**Kaksoisnapsauta riviä** nähdäksesi koko virhetekstin ja valmistuneen tiedoston polun. Listaa vieritetään hiiren rullalla. Taulukko tyhjenee seuraavan latausjonon alkaessa; musiikkitiedostot säilyvät.

**Näytä loki** avaa tarkemman tekstilokin taulukon alapuolelle. **Piilota loki** sulkee sen. Loki kertyy myös piilotettuna, ja näkyvyysasetus muistetaan seuraavalla käynnistyksellä.

## Useita tiedostoja yhtä aikaa

Valitse **Latauksia kerralla → 1, 2, 3, 4, 5, 15 tai 20** ennen latauksen aloitusta. Oletus on **2**, ja valinta tallentuu asetuksiin. **1** lataa peräkkäin. Suurempi arvo lataa useita kappaleita rinnakkain, myös yhden albumin tai soittolistan sisältä sekä usean linkin jonossa.

Raja koskee koko jonoa eikä kertaudu albumien määrällä. YouTube lukee ensin kappalelistat. Kappaleet voivat valmistua eri järjestyksessä. Kaikki kansiomuodot ovat käytettävissä myös rinnakkaislatauksissa.

Latauspalkki seuraa **koko jonoa**. Sen alla näkyvät käsiteltyjen tiedostojen tai julkaisujen määrä, kokonaisprosentti ja likimääräinen jäljellä oleva aika. Arvio perustuu toteutuneeseen etenemiseen, tarkentuu työn edetessä ja sisältää myös jäljellä olevat muunnokset. Alussa näytetään **lasketaan aika-arviota**. Eri kokoiset kappaleet ja verkkoyhteys vaikuttavat arvioon.

**Keskeytä** pysäyttää kaikki käynnissä olevat lataukset ja estää odottavien käynnistymisen. Valmiit tiedostot ja niiden lataushistoria säilyvät. Käynnistä sama lataus myöhemmin uudelleen samalla tallennuskansiolla, kansiomuodolla ja tiedostomuodolla: jo valmistuneet kappaleet ohitetaan. Keskeneräinen kappale voidaan ladata uudelleen.

Kirjautumis- tai varmistuspyyntö pysäyttää koko jonon. Jos palvelu alkaa rajoittaa latauksia, pienennä samanaikaisten latausten määrää.

Pysähtyneen jonon voi jatkaa samassa sovellusistunnossa: valitse uusi **YouTube-evästeet**-tiedosto ja paina **Jatka jonoa**. Jatkaminen palauttaa alkuperäiset linkit, lähteen, tallennuskansion, tiedostomuodon, kansiomuodon ja rinnakkaisten latausten määrän. Jo valmistuneet kappaleet ohitetaan lataushistorian avulla; kesken jääneet kappaleet aloitetaan uudelleen. Tämä toimii sekä YouTube- että Spotify-lähteellä. Painike tulee näkyviin kirjautumispyynnön tai vanhentuneiden evästeiden varoituksen pysäytettyä jonon. Uuden latausjonon aloittaminen korvaa aiemman jatkettavan jonon. Jatkettava jono palautuu vain samassa sovellusistunnossa.

YouTube-jono tallentaa paikalliseen tarkistuspistetiedostoon alkuperäisen kappalelistan ja tiedon valmiista kappaleista. Jatkaminen ei hae soittolistaa uudelleen eikä lataa valmiita kappaleita; kappalerivit ja koko jonon valmistuneiden määrä säilyvät. Tarkistuspisteeseen ei tallenneta evästeitä. Tiedosto poistetaan jonon valmistuttua tai uuden jonon korvatessa sen.

## Kansiomuodot

Kaikki vaihtoehdot toimivat molemmilla latauslähteillä:

```text
Albumi, Vuosi:
Musiikki/
└── Artisti/
    └── Albumin nimi, 2026/
        ├── Artisti - Kappale.flac
        └── Artisti - Toinen kappale.flac

Vuosi - Albumi:
Musiikki/
└── Artisti/
    ├── 2026 - Uusin albumi/
    ├── 2024 - Edellinen albumi/
    └── 2020 - Vanhempi albumi/

Suoraan tallennuskansioon (uuden asennuksen oletus):
Musiikki/
├── Alan Walker - Faded.flac
└── Ava Max - Ghost.flac
```

Valitse **Suoraan tallennuskansioon**, kun haluat kappaleet valitsemaasi kansioon ilman artisti- tai albumialikansioita. Esimerkiksi tallennuskansio `D:\Musiikki` tarkoittaa, että kappaleet tulevat suoraan siihen.

Uudet musiikkitiedostot nimetään **Artisti - Kappale.flac** -muotoon (tai valitun tiedostomuodon päätteellä). Alun kappalenumerot sekä YouTube- ja Spotify-tunnisteet jätetään pois. Nimistä poistetaan esitystapamerkinnät, kuten **Official Video**, **Official Audio** ja **HD**. Remix-, live- ja remaster-version nimi säilytetään, jotta eri versiot erottuvat toisistaan.

Tiedoston metatietoihin tallennetaan vain **kappaleen nimi** ja **artistit**. Albumi-, vuosi-, kappalenumero-, lähdeosoite-, palvelutunniste- ja muut käyttäjätagit sekä kansikuvat poistetaan uusista latauksista. Spotifyn nimi- ja artistitiedot tulevat kappaletiedoista. YouTubessa hyödynnetään musiikkitietoja ja videon **Artisti - Kappale** -nimeä; julkaisukanavaa ei käytetä artistina silloin, kun artisti selviää otsikosta. Äänen sisältöä ei muuteta metatietojen siistimisessä.

Musiikki viimeistellään väliaikaisessa kansiossa ja siirretään tallennuskansioon vasta valmiina. Jos samanniminen tiedosto on jo olemassa, uusi saa esimerkiksi nimen **Artisti - Kappale (2).flac**. Aiemman tiedoston päälle ei kirjoiteta.

**Muutos koskee vain uusia latauksia. Aiemmin ladattuja tiedostoja tai niiden metatietoja ei muuteta.** Lataushistoria säilyy, ja jo ladatut kappaleet ohitetaan kuten ennenkin. Tunnisteita käytetään vain sovelluksen sisäisessä lataushistoriassa.

Kansiomuodon vaihtaminen koskee seuraavia latauksia. Aiemmin ladattuja tiedostoja ei siirretä. YouTube-linkkien albumikansiot perustuvat saatavilla oleviin kanava-, soittolista- ja julkaisutietoihin. **Avaa kansio** näyttää valitun tallennuskansion.

## Tiedostomuoto

Valittavana ovat **FLAC**, **Opus**, **MP3** ja **M4A**. Muoto tallennetaan asetuksiin, ja eri muodoilla on omat lataushistoriansa.

**YouTuben ääni on jo häviöllisesti pakattu. FLAC-muunnos ei palauta menetettyä äänenlaatua.** Sama koskee SpotDL:ää, kun ääni tulee YouTubesta. Käytä sisältöä, jonka lataamiseen sinulla on oikeus.

## Työkalujen päivitykset

1. Paina yläreunasta **Työkalujen päivitykset**.
2. Sovellus tarkistaa viralliset GitHub-julkaisut ja näyttää asennetun sekä saatavilla olevan version.
3. Valitse päivitettävät työkalut ja paina **Päivitä valitut**. Asennus on mahdollista latausten ollessa pysähdyksissä.
4. Odota valmistumisilmoitusta. Päivitetyt työkalut ovat käytössä seuraavassa latauksessa; sovellusta ei tarvitse käynnistää uudelleen.

**yt-dlp**, **Deno** ja **FFmpeg / ffprobe** voidaan päivittää suoraan sovelluksesta. FFmpeg käyttää nimettyä virallista Windows x64 GPL -autobuild-julkaisua. **SpotDL:n** uusin julkaisu tarkistetaan myös, mutta sen mukautettu lataustyökalu päivitetään **Albumilataajan sovelluspäivityksen mukana**. Näin Spotify-puolen yhteinen äänenlataaja ja muut korjaukset säilyvät. Päivitysikkunan **Sovelluspäivitys**-painike tarkistaa Albumilataajan uusimman version.

Paketit ladataan vain työkalujen omista virallisista GitHub-repositorioista. Niiden GitHubin ilmoittama SHA-256 tarkistetaan ja uudet ohjelmat käynnistetään versiotestiä varten ennen asennusta. Ilman tarkistussummaa päivitystä ei asenneta. Jos jokin valittu päivitys epäonnistuu, aiemmat työkalut palautetaan. **Keskeytä** voi perua latausvaiheen ennen asennusta.

## Albumilataajan päivitykset

1. Sovellus tarkistaa uusimman vakaan GitHub-julkaisun käynnistyessään. Voit tarkistaa myös painikkeella **Tarkista päivitykset**.
2. Voit hyväksyä tai kieltäytyä päivityksestä. Kieltäytyessä nykyinen sovellus jää käyttöön; seuraava käynnistys tarkistaa päivitykset uudelleen.
3. Asentajan SHA-256 varmistetaan julkaisun **SHA256SUMS.txt**-tiedostosta ennen avaamista.
4. Hyväksytty päivitys asentuu samaan sovelluskansioon, näyttää asennuksen etenemisen ja käynnistää sovelluksen uudelleen. Musiikkikansio ja asetukset säilyvät.

Päivitys sisältää myös testatut taustatyökalut. Päivityksen jälkeinen käynnistys käyttää omaa uutta Python-ajonaikaista kansiota; tämä korjaa vanhojen versioiden **Failed to load Python DLL** -virheen. Jos vanha versio näyttää virheen ennen päivittämistä, avaa uusin asentaja käsin.

## YouTube-istunto ja kirjautumispyynnöt

**Sign in to confirm you're not a bot** on YouTuben kirjautumis- tai varmistuspyyntö. Pelkkä **No title found** tai SABR-varoitus ei yksin tarkoita latauksen epäonnistumista.

1. Avaa YouTube itse selaimessa ja tee sen pyytämä varmistus itse.
2. Vie tarvittaessa YouTuben evästeet Netscape-muotoiseen `cookies.txt`-tiedostoon. Katso yt-dlp:n [evästeohje](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp) ja [YouTube-kohtainen vientiohje](https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies).
3. Paina **YouTube-evästeet** ja valitse uusi tiedosto koneeltasi. Se koskee sekä YouTube-latauksia että SpotDL:n käyttämää YouTube-ääntä.
4. Paina **Jatka jonoa**, jos kirjautumispyyntö pysäytti jonon tässä sovellusistunnossa. Valmiit kappaleet ohitetaan. Muussa tapauksessa käynnistä lataus linkeistä uudelleen.

Sovellus ei lue selaimen profiilia tai vie evästeitä automaattisesti. Asetuksiin tallennetaan vain valitun tiedoston polku. Jokainen latausprosessi käyttää omaa väliaikaista kopiota: **alkuperäistä cookies.txt-tiedostoa ei muokata**. Kopiot siivotaan toiminnon päätyttyä myös keskeytyksessä. **Poista valinta** lopettaa tiedoston käytön poistamatta alkuperäistä tiedostoa.

**Älä lähetä evästetiedostoa chattiin, GitHubiin tai muille:** se voi sisältää tilillesi pääsyn mahdollistavia tietoja. Evästeet voivat vanhentua eivätkä takaa onnistumista. YouTube voi rajoittaa pyyntöjä myös muista syistä. Käytä kirjautumista vain tarvittaessa.

## Ongelmatilanteet

| Ongelma | Ratkaisu |
|---|---|
| Kappaleen virhe | Lue rivin oikea virhesarake ja kaksoisnapsauta riviä. Tarvittaessa avaa **Näytä loki**. |
| Spotify AudioProviderError | Tarkista työkalupäivitykset ja rivin tarkempi YouTube-virhe. Spotify käyttää samaa yt-dlp-ohjelmaa kuin YouTube-tila. |
| Kirjautumispyyntö | Tee varmistus itse YouTubessa ja katso yllä oleva evästeohje. |
| Virheellinen linkki | Korjaa ilmoitettu rivi. Käytä valitun latauslähteen https-linkkejä. |
| Puuttuva työkalu | Asenna sovellus uudelleen tai pura portable-paketti kokonaan. |
| Työkalupäivitys epäonnistuu | Aiemmat työkalut säilyvät. Tarkista yhteys ja tiedostojen kirjoitusoikeus, odota latausten valmistumista ja yritä uudelleen. |
| Päivitystarkistus epäonnistuu | Tarkista verkkoyhteys ja kokeile myöhemmin. Asentajan voi ladata myös GitHub Releasesista. |
| Albumikansiot uusimmat ensin | Valitse **Vuosi - Albumi** ja Resurssienhallinnan lajittelu **Nimi, laskeva**. |

Ongelmailmoituksessa kerro sovelluksen versio, lähde, vaiheet ja tarvittava osa lokista. Älä lähetä salasanoja, evästeitä tai kirjautumistietoja.

## Asetukset ja poistaminen

Asetukset ovat tiedostossa `%LOCALAPPDATA%\Albumilataaja\settings.json`. Latausmoottoreilla voi olla omia välimuisteja käyttäjäprofiilissa. Työkalujen versiot tallennetaan sovelluksen `tools/tools-versions.json`-tiedostoon.

Poista asennus Windowsin **Asetukset → Sovellukset → Asennetut sovellukset → Albumilataaja → Poista asennus** -toiminnolla. Musiikkikansio ja käyttäjän asetukset säilyvät. Portable-version voi poistaa poistamalla puretun sovelluskansion; säilytä musiikki erillisessä kansiossa.

## Kehitys ja julkaiseminen

Lähdekoodi on `lahdekoodi/`-kansiossa. Rakentaminen vaatii Windowsin, Python 3.14:n ja Inno Setup 6/7:n. Aja projektin juuresta PowerShellissä:

```powershell
./lahdekoodi/build.ps1
# Tarvittaessa kääntäjän polku:
./lahdekoodi/build.ps1 -Iscc 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
```

Skripti asentaa Python-riippuvuudet, ajaa testit, lataa lukitut taustatyökalut ja tarkistaa niiden SHA-256:t. Se rakentaa taustatyökalut, sovelluksen, asentajan, portable-paketin ja tarkistussummat `dist/`-kansioon. Rakennuksessa käytetyt työkalut ovat tiedostossa `lahdekoodi/tools-lock.json`. Kolmansien osapuolten lisenssit ja lähteet on kuvattu tiedostossa [THIRD_PARTY.md](THIRD_PARTY.md).

Uutta versiota varten päivitä `VERSION` tiedostossa `lahdekoodi/app.py` ja julkaise vastaava Git-tagi, esimerkiksi seuraavana korjauspäivityksenä `v1.4.3`. GitHub Actions testaa ja paketoi sovelluksen sekä julkaisee asentajan, portable-paketin ja tarkistussummat. Pysyvä AppId mahdollistaa päivityksen nykyisen asennuksen paikalle.
