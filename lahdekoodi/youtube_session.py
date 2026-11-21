"""Explicit, user-selected YouTube session files; no browser credential access."""
from pathlib import Path

def validate_cookie_file(value):
    if not value: return ''
    path=Path(value).expanduser().resolve()
    if not path.is_file(): raise ValueError('Valittua YouTube-evästetiedostoa ei löydy. Valitse se uudelleen tai poista valinta.')
    try:
        with path.open('r',encoding='utf-8-sig') as file: header=file.readline(256).strip()
    except (OSError,UnicodeError): raise ValueError('Evästetiedostoa ei voitu avata. Valitse Netscape-muotoinen cookies.txt-tiedosto.') from None
    if header not in ['# Netscape HTTP Cookie File','# HTTP Cookie File']:
        raise ValueError('Evästetiedoston pitää olla Netscape-muotoinen cookies.txt-tiedosto.')
    return str(path)

def requires_youtube_auth(line):
    text=line.casefold().replace('’',"'")
    return any(message in text for message in ["sign in to confirm you're not a bot",'sign in to confirm you are not a bot','login required','use --cookies-from-browser or --cookies for the authentication'])

AUTH_HELP=('YouTube pyytää kirjautumista tai manuaalista varmistusta. Latausjono pysäytettiin.\n\n'
           'Avaa YouTube itse selaimessa ja tee sen pyytämä varmistus. Jos lataus tarvitsee kirjautumisistunnon, '
           'valitse sovelluksen YouTube-evästeet-painikkeella itse viemäsi cookies.txt-tiedosto ja aloita lataus uudelleen.\n\n'
           'Jo valmistuneet kappaleet säilyvät. Evästeet eivät takaa latauksen onnistumista. Älä lähetä evästetiedostoa muille.')
