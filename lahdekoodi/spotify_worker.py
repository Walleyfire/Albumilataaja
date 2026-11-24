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
from download_rows import row_event
from music_files import spotify_identity,publish_music

TRACK_WORKSPACE=ContextVar('spotify_track_workspace',default=None)
TRACK_ROW=ContextVar('spotify_track_row',default=None)
TRACK_OUTPUT=ContextVar('spotify_track_output',default=None)
PROGRESS_LOCK=threading.RLock()


def song_row(song):
    title,artists=spotify_identity(song)
    return {'id':'spotify:'+str(song.song_id or song.url),'title':title,
            'artist':', '.join(artists),'album':song.album_name or '', 'source':'Spotify','error':''}


def emit_row(record,**changes):
    if record is None: return
    with PROGRESS_LOCK:
        record.update(changes)
        row_event(lambda line:print(line,flush=True),record['id'],**{key:value for key,value in record.items() if key!='id'})


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
    record=getattr(provider,'_track_row',None)
    emit_row(record,stage='downloading' if download else 'searching')
    args=audio_command(url,folder,provider.output_format,provider.cookie_file,download)
    # Each concurrent external process owns its own session copy.
    with isolated_cookie_arguments(args,os.environ.get('ALBUMILATAAJA_WORKSPACE')) as args:
        result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace',
                              creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),
                              timeout=None if download else 180)
    errors=getattr(result,'stderr','') or ''
    if result.returncode:
        lines=errors.splitlines()
        message=next((line.removeprefix('ERROR:').strip() for line in reversed(lines) if line.startswith('ERROR:')),None)
        emit_row(record,stage='error',error=message or 'YouTube-äänen lataus epäonnistui. Katso tarkempi loki.')
    for line in errors.splitlines(): print(line,file=sys.stderr,flush=True)
    if result.returncode:
        raise AudioProviderError('YouTube-äänen lataus epäonnistui. Tarkka virhe näkyy yllä lokissa.')
    try:
        metadata=json.loads(result.stdout)
        if not isinstance(metadata,dict) or not metadata.get('id') or not metadata.get('ext'): raise ValueError()
    except (ValueError,TypeError):
        emit_row(record,stage='error',error='Äänenlataaja palautti virheellisen metatietovastauksen.')
        raise AudioProviderError('Äänenlataaja palautti virheellisen metatietovastauksen.') from None
    if download: emit_row(record,stage='converting')
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
    original_multiple=Downloader.download_multiple_songs
    original_filename=download_module.create_file_name
    original_count=ProgressHandler.set_song_count
    def provider_init(self,*args,**kwargs):
        original_init(self,*args,**kwargs)
        self._track_workspace=TRACK_WORKSPACE.get()
        self._track_row=TRACK_ROW.get()
    def track_temp(): return TRACK_WORKSPACE.get() or original_temp()
    def staged_filename(*args,**kwargs):
        destination=original_filename(*args,**kwargs)
        context=TRACK_OUTPUT.get()
        if context is None:return destination
        context['folder']=destination.parent
        return context['workspace']/('result'+destination.suffix)
    def song_count(self,count):
        self._albumilataaja_progress={'completed':0,'failed':0,'running':0}
        return original_count(self,count)
    def report(handler):
        state=handler._albumilataaja_progress
        print(PARALLEL_PROGRESS+json.dumps({'total':handler.song_count,'completed':state['completed'],
              'failed':state['failed'],'partial':0,'running':state['running']}),flush=True)
    async def download(self,song):
        record=song_row(song); emit_row(record,stage='searching')
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
                row_token=TRACK_ROW.set(record)
                context={'workspace':Path(temporary),'folder':None}
                output_token=TRACK_OUTPUT.set(context)
                try:
                    result=await original_download(self,song)
                    failed=not result[1]
                    if not failed:
                        try:
                            source=Path(result[1]).resolve()
                            if not source.is_relative_to(Path(temporary).resolve()) or context['folder'] is None:
                                raise ValueError('Latauksen väliaikaista tiedostoa ei voitu vahvistaa.')
                            title,artists=spotify_identity(result[0])
                            destination=publish_music(source,context['folder'],title,artists)
                            result=(result[0],destination)
                        except Exception as error:
                            failed=True;emit_row(record,stage='error',error=str(error))
                            self.errors.append(f'{song.url} - MusicMetadataError: {error}')
                            return result[0],None
                    if not failed and self.settings['archive']:
                        with PROGRESS_LOCK:
                            self.url_archive.add(result[0].url)
                            self.url_archive.save(self.settings['archive'])
                    if not failed:
                        emit_row(record,stage='skipped' if record.get('stage')=='searching' else 'done',percent=100,filename=str(result[1]))
                    return result
                finally: TRACK_WORKSPACE.reset(token); TRACK_ROW.reset(row_token);TRACK_OUTPUT.reset(output_token)
        finally:
            if failed: emit_row(record,stage='error',error=record.get('error') or 'Kappaleen lataus epäonnistui. Katso tarkempi loki.')
            if parallel:
                with PROGRESS_LOCK:
                    state=handler._albumilataaja_progress
                    state['running']-=1; state['completed']+=1; state['failed']+=int(failed)
                    report(handler)
    def multiple(self,songs):
        for song in songs:
            emit_row(song_row(song),stage='skipped' if self.settings['archive'] and song.url in self.url_archive else 'queued')
        return original_multiple(self,songs)
    AudioProvider.__init__=provider_init
    AudioProvider.get_download_metadata=external_metadata
    AudioProvider._albumilataaja_bridge=True
    download_module.get_temp_path=track_temp
    download_module.create_file_name=staged_filename
    Downloader.async_search_and_download=download
    Downloader.download_multiple_songs=multiple
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
