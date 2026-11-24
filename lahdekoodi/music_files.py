"""Readable music filenames and title/artist-only tags for new downloads."""
import os
import errno
from pathlib import Path
import re
import shutil
import tempfile
import threading

PUBLISH_LOCK=threading.RLock()
PROMO=re.compile(r'(?i)\b(?:official\s+(?:(?:music|lyric)\s+)?(?:video|audio|visuali[sz]er)|official|(?:music|lyrics?)\s+video|visuali[sz]er|lyrics?|full\s*hd|hd|hq|[48]k|(?:720|1080|1440|2160)p|full)\b')


def clean_title(value):
    text=' '.join(str(value or '').split())
    def group(match):
        content=match.group(1) or match.group(2)
        # Remove presentation labels, preserving actual versions and remixes.
        remainder=PROMO.sub('',content)
        remainder=re.sub(r'(?i)\b(?:remastered|version|on|screen|video|audio)\b','',remainder)
        return '' if PROMO.search(content) and not re.sub(r'[\W_]+','',remainder) else match.group(0)
    text=re.sub(r'\(([^()]*)\)|\[([^\[\]]*)\]',group,text)
    text=re.sub(r'(?i)\s*[-–—|:]?\s*official\s+(?:(?:music|lyric)\s+)?(?:video|audio)\s*$','',text)
    return re.sub(r'\s+',' ',text).strip(' \t-|–—').strip('"') or 'Tuntematon kappale'


def clean_artist(value):
    text=' '.join(str(value or '').split())
    text=re.sub(r'(?i)\s*-\s*topic\s*$','',text)
    text=re.sub(r'(?i)VEVO$','',text)
    return text.strip()


def youtube_identity(info,fallback_artist='',fallback_title=''):
    title=info.get('track') or info.get('title') or fallback_title
    if info.get('id'):title=str(title).replace('['+str(info['id'])+']','')
    title=re.sub(r'^\d{1,3}\s*[-.]\s+','',str(title or ''))
    supplied=info.get('artists') or info.get('artist') or []
    artists=[clean_artist(value) for value in (supplied if isinstance(supplied,list) else [supplied]) if value]
    parts=re.split(r'\s+[-–—]\s+',title,maxsplit=1)
    prefix=clean_artist(parts[0]) if len(parts)==2 else ''
    if len(parts)==2 and (not info.get('track') or prefix.casefold()==', '.join(artists).casefold()):
        if prefix:
            if not artists:artists=[prefix]
            elif not any(prefix.casefold()==artist.casefold() for artist in artists) and not all(artist.casefold() in prefix.casefold() for artist in artists):artists=[prefix,*artists]
            title=parts[1]
    if not artists:artists=[clean_artist(fallback_artist or info.get('uploader') or info.get('channel')) or 'Tuntematon artisti']
    return clean_title(title),artists


def spotify_identity(song):
    return clean_title(song.name),[' '.join(str(value).split()) for value in (song.artists or []) if value] or ['Tuntematon artisti']


def write_music_tags(path,title,artists):
    from mutagen import File
    from mutagen.id3 import ID3,TIT2,TPE1
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    audio=File(path)
    if audio is None:raise ValueError('Äänitiedostoa ei voitu avata metatietojen siistimistä varten.')
    if audio.tags is None:audio.add_tags()
    audio.tags.clear()
    if isinstance(audio.tags,ID3):
        audio.tags.add(TIT2(encoding=3,text=title));audio.tags.add(TPE1(encoding=3,text=artists))
    elif isinstance(audio,MP4):
        audio.tags['\xa9nam']=[title];audio.tags['\xa9ART']=artists
    else:
        audio.tags['title']=[title];audio.tags['artist']=artists
    if isinstance(audio,FLAC):audio.clear_pictures()
    audio.save()


def filename_base(artist,title,limit=170):
    text=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',artist+' - '+title).strip(' .')
    return text[:limit].rstrip(' .') or 'Tuntematon artisti - Tuntematon kappale'


def publish_music(source,folder,title,artists):
    """Tag privately, then publish a complete file without replacing existing music."""
    source=Path(source);folder=Path(folder).resolve();folder.mkdir(parents=True,exist_ok=True)
    write_music_tags(source,title,artists)
    base=filename_base(', '.join(artists),title)
    with tempfile.NamedTemporaryFile(prefix='.albumilataaja-',suffix='.part',dir=folder,delete=False) as output:
        temporary=Path(output.name)
    try:
        try:os.replace(source,temporary)
        except OSError as error:
            if error.errno!=errno.EXDEV and getattr(error,'winerror',None)!=17:raise
            shutil.copyfile(source,temporary);source.unlink()
        with PUBLISH_LOCK:
            number=1
            while True:
                suffix='' if number==1 else f' ({number})'
                target=folder/(base[:170-len(suffix)]+suffix+source.suffix.lower())
                if target.exists():number+=1;continue
                try:
                    if os.name=='nt':os.rename(temporary,target)
                    else:os.link(temporary,target);temporary.unlink()
                    return target
                except FileExistsError:number+=1
    finally:temporary.unlink(missing_ok=True)
