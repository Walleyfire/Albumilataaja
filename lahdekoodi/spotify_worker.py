"""spotDL metadata/tagging with Albumilataaja's shared external audio engine.

Keep this in a separate process: spotDL still owns matching, album paths,
conversion, tags and archives. Only its embedded yt-dlp is replaced.
"""
import json
from contextvars import ContextVar
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from urllib.parse import urlparse, parse_qs
from youtube_session import isolated_cookie_arguments
from queue_progress import PARALLEL_PROGRESS

TRACK_WORKSPACE=ContextVar('spotify_track_workspace',default=None)
PROGRESS_LOCK=threading.RLock()


def save_archive(archive,file):
    destination=Path(file)
    destination.parent.mkdir(parents=True,exist_ok=True)
    with PROGRESS_LOCK:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=destination.parent,prefix='.spotdl-history-',suffix='.tmp',delete=False) as output:
            temporary=Path(output.name)
            for url in sorted(archive): output.write(url+'\n')
        try: temporary.replace(destination)
        finally: temporary.unlink(missing_ok=True)
    return True


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
    folder=getattr(provider,'_track_workspace',None) or get_temp_path()
    args=audio_command(url,folder,provider.output_format,provider.cookie_file,download)
    # Each concurrent external process owns its own session copy.
    with isolated_cookie_arguments(args,os.environ.get('ALBUMILATAAJA_WORKSPACE')) as args:
        result=subprocess.run(args,stdout=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',
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
    if getattr(AudioProvider,'_albumilataaja_bridge',False): return
    from spotdl.download.downloader import Downloader
    from spotdl.download.progress_handler import ProgressHandler
    from spotdl.utils.archive import Archive
    import spotdl.download.downloader as download_module
    original_init=AudioProvider.__init__
    original_temp=download_module.get_temp_path
    original_download=Downloader.async_search_and_download
    original_count=ProgressHandler.set_song_count
    def provider_init(self,*args,**kwargs):
        original_init(self,*args,**kwargs)
        self._track_workspace=TRACK_WORKSPACE.get()
    def track_temp(): return TRACK_WORKSPACE.get() or original_temp()
    def song_count(self,count):
        self._albumilataaja_progress={'completed':0,'failed':0,'running':0}
        return original_count(self,count)
    def report(handler):
        state=handler._albumilataaja_progress
        print(PARALLEL_PROGRESS+json.dumps({'total':handler.song_count,'completed':state['completed'],
              'failed':state['failed'],'partial':0,'running':state['running']}),flush=True)
    async def download(self,song):
        parallel=self.settings['threads']>1 and self.progress_handler.song_count>0
        handler=self.progress_handler
        if parallel:
            with PROGRESS_LOCK:
                if not hasattr(handler,'_albumilataaja_progress'):
                    handler._albumilataaja_progress={'completed':0,'failed':0,'running':0}
                handler._albumilataaja_progress['running']+=1
                report(handler)
        failed=True
        try:
            # The coroutine and its audio provider share this directory. Two
            # songs matched to the same video can never overwrite temp audio.
            with tempfile.TemporaryDirectory(prefix='spotify-track-',dir=os.environ.get('ALBUMILATAAJA_WORKSPACE')) as temporary:
                token=TRACK_WORKSPACE.set(Path(temporary))
                try:
                    result=await original_download(self,song)
                    failed=not result[1]
                    if not failed and self.settings['archive']:
                        with PROGRESS_LOCK:
                            self.url_archive.add(result[0].url)
                            self.url_archive.save(self.settings['archive'])
                    return result
                finally: TRACK_WORKSPACE.reset(token)
        finally:
            if parallel:
                with PROGRESS_LOCK:
                    state=handler._albumilataaja_progress
                    state['running']-=1; state['completed']+=1; state['failed']+=int(failed)
                    report(handler)
    AudioProvider.__init__=provider_init
    AudioProvider.get_download_metadata=external_metadata
    AudioProvider._albumilataaja_bridge=True
    download_module.get_temp_path=track_temp
    Downloader.async_search_and_download=download
    ProgressHandler.set_song_count=song_count
    Archive.save=save_archive


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
