"""spotDL metadata/tagging with Albumilataaja's shared external audio engine.

Keep this in a separate process: spotDL still owns matching, album paths,
conversion, tags and archives. Only its embedded yt-dlp is replaced.
"""
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse, parse_qs


def tools_directory():
    return Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]/'tools'


def watch_url(value):
    """Use the standard YouTube watch page for a YouTube Music match."""
    parsed=urlparse(value)
    if parsed.scheme!='https' or parsed.hostname not in ('youtube.com','www.youtube.com','music.youtube.com','youtu.be'):
        raise ValueError('Spotify-äänen lähteen pitää olla YouTube-linkki.')
    if parsed.hostname=='music.youtube.com' and parsed.path=='/watch':
        video=parse_qs(parsed.query).get('v',[''])[0]
        if video: return 'https://www.youtube.com/watch?v='+video
    return value


def audio_command(url,folder,fmt,cookie_file=None,download=False):
    tools=tools_directory()
    selection={'m4a':'bestaudio[ext=m4a]/bestaudio/best','opus':'bestaudio[ext=webm]/bestaudio/best'}.get(fmt,'bestaudio/best')
    return [str(tools/'yt-dlp.exe'),'--ignore-config','--no-color','--no-playlist',
            *(['--cookies',str(cookie_file)] if cookie_file else []),
            '--js-runtimes','deno:'+str(tools/'deno.exe'),'--ffmpeg-location',str(tools),
            '--sleep-interval','5','--max-sleep-interval','10','--socket-timeout','25','--retries','3',
            '-f',selection,'--dump-single-json','--no-progress',
            '--no-simulate' if download else '--skip-download',
            '-o',str(Path(folder)/'%(id)s.%(ext)s'),'--',watch_url(url)]


def external_metadata(provider,url,download=False):
    from spotdl.providers.audio.base import AudioProviderError
    from spotdl.utils.config import get_temp_path
    # Inherit stderr so the UI sees actual YouTube errors, including auth
    # challenges, rather than spotDL's generic AudioProviderError alone.
    result=subprocess.run(audio_command(url,get_temp_path(),provider.output_format,provider.cookie_file,download),
                          stdout=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',
                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),
                          timeout=None if download else 180)
    if result.returncode:
        raise AudioProviderError('YouTube-äänen lataus epäonnistui. Tarkka virhe näkyy yllä lokissa.')
    try:
        metadata=json.loads(result.stdout)
        if not isinstance(metadata,dict) or not metadata.get('id') or not metadata.get('ext'): raise ValueError()
    except (ValueError,TypeError):
        raise AudioProviderError('Äänenlataaja palautti virheellisen metatietovastauksen.') from None
    return metadata


def install_audio_bridge():
    from spotdl.providers.audio.base import AudioProvider
    AudioProvider.get_download_metadata=external_metadata


def main():
    install_audio_bridge()
    if sys.argv[1:]==['--self-test']:
        from spotdl.download.downloader import Downloader
        from spotdl import console_entry_point
        from ytmusicapi import YTMusic
        assert Downloader and console_entry_point
        assert YTMusic(language='de')  # Verify bundled translations as well.
        assert all((tools_directory()/name).is_file() for name in ('yt-dlp.exe','deno.exe','ffmpeg.exe'))
        print('Spotify audio bridge dependencies OK')
        return
    from spotdl import console_entry_point
    console_entry_point()


if __name__=='__main__': main()
