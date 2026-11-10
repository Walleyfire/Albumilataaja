# Albumilataaja

Suomenkielinen Windows 10/11 x64 -sovellus musiikin lataamiseen. Tavallinen ikkuna, ei konsoli-ikkunaa. Pythonia tai komentorivityökaluja ei tarvitse asentaa käyttäjän koneelle.

## Asentaminen

Lataa GitHub Releasesista **Albumilataaja-Setup.exe** ja suorita se. Asennus tehdään omaan käyttäjäprofiiliin ilman järjestelmänvalvojan oikeuksia. Sovellusta ja asentajaa ei ole allekirjoitettu koodin allekirjoitusvarmenteella.

## Käyttö

1. Valitse **YouTube** tai **Spotify (spotDL)**.
2. YouTube: kirjoita artistin nimi, paina **Hae artisti**, valitse oikea artisti ja **Näytä julkaisut**. Valitse haluamasi julkaisut tai **Valitse kaikki**, sitten **Lataa valitut julkaisut**. Myös singlet ja EP:t voi sisällyttää hakuun. Vaihtoehtoisesti liitä videon tai albumisoittolistan linkki ja paina **Lataa linkistä**.
3. Spotify: kirjoita artistin nimi ja paina **Hae Spotify-julkaisut**. Hakuun voi syöttää myös suoran Spotify-artistilinkin. spotDL hakee parhaaksi osuvan artistin tuotannon; tarkista tuloksesta artistin nimi ja julkaisut ennen lataamista. Voit myös liittää Spotify-artistin, albumin, soittolistan tai kappaleen linkin ja painaa **Lataa linkistä**. Artistin linkki käsittelee spotDL:n löytämän tuotannon.
4. Valitse tallennuskansio ja tiedostomuoto: FLAC, Opus, MP3 tai M4A.

Tiedostot järjestetään **Artisti / 2026 - Albumi / Kappale** -kansioihin. Sovelluksen albumilista ja valittujen albumien latausjono ovat uusimmasta vanhimpaan; tuntemattomat vuodet tulevat viimeiseksi. Resurssienhallinnassa käytä lajittelua **Nimi, laskeva**, niin uusimmat albumikansiot näkyvät ensin. Suoran YouTube-linkin kansiot perustuvat kanavan ja soittolistan nimeen; vuosiluku lisätään, jos julkaisuvuosi on saatavilla. Valmiit lataukset ohitetaan samassa kansiossa ja muodossa. Keskeytetyn työn voi aloittaa uudelleen; valmiit kappaleet säilyvät. Epäonnistuneet lataukset näkyvät ikkunan lokissa.

## Äänenlaatu ja saatavuus

YouTube-ääni on häviöllisesti pakattua. FLAC-muunnos ei tee siitä alkuperäistä häviötöntä ääntä. spotDL käyttää Spotifya kappaletietoihin ja hakee vastaavan äänen yleensä YouTubesta; se ei pura Spotifyn äänitiedostoja. Koko tuotannon löytymistä, versioiden oikeellisuutta tai kaikkien kappaleiden saatavuutta ei voi taata. Käytä sovellusta sisältöön, jonka lataamiseen sinulla on oikeus.

## Päivitykset

Sovellus tarkistaa uusimman vakaan GitHub-julkaisun käynnistyessään. Voit myös painaa **Tarkista päivitykset**. Uusi asentaja ladataan käyttäjän hyväksynnän jälkeen, sen SHA-256 tarkistetaan julkaisun tarkistussummatiedostosta ja asennus käynnistyy. Asentaja päivittää saman sovelluksen paikalleen. Musiikkikansio ja asetukset säilyvät. Tarkistussumma varmistaa tiedoston eheyden; julkaisuja ei ole digitaalisesti allekirjoitettu. Asetukset ovat `%LOCALAPPDATA%\Albumilataaja\settings.json`.

## Kehitys ja julkaiseminen

Lähdekoodi on `lahdekoodi/`-kansiossa. Katso sen `build.ps1`. Työkalut ladataan lukituista julkaisuista ja niiden SHA-256 tarkistetaan. `v1.0.1`-tyyppisen Git-tagin julkaiseminen käynnistää GitHub Actionsin, joka testaa, paketoi ja julkaisee uuden asentajan ja tarkistussummat. Päivitä ensin `VERSION` tiedostossa `app.py`.

Ensimmäisen version varmennetut testit ja rajoitukset ovat GitHub-julkaisun kuvauksessa.

## Palvelukohtaiset rajoitukset

YouTube-artistihaku ja FLAC-lataus sekä spotDL:n Spotify-kappalelinkin FLAC-lataus on testattu. Spotify-artistin nimihaku ei palauttanut testissä tulosta, ja koko artistin metatietojen haku aikakatkaistiin. Ominaisuus näyttää virheen ja sen voi keskeyttää; käytä tarvittaessa albumi- tai kappalelinkkejä. Spotify-palvelun muutokset voivat vaikuttaa spotDL:n toimintaan.
