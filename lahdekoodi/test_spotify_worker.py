import json
from pathlib import Path
import tempfile
import unittest
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import patch
import spotify_worker as worker


class SpotifyWorkerTests(unittest.TestCase):
    def test_parallel_providers_keep_separate_audio_and_cookie_workspaces(self):
        try:
            from spotdl.providers.audio.base import AudioProvider
        except ImportError: self.skipTest('spotDL worker dependency not installed')
        worker.install_audio_bridge()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); source=root/'cookies.txt'; source.write_text('# Netscape HTTP Cookie File\n')
            providers=[]
            for number in range(2):
                folder=root/str(number);folder.mkdir()
                token=worker.TRACK_WORKSPACE.set(folder)
                try: providers.append(AudioProvider(output_format='flac',cookie_file=str(source)))
                finally: worker.TRACK_WORKSPACE.reset(token)
            gate=threading.Barrier(2); used=[]
            def engine(args,**kwargs):
                cookie=Path(args[args.index('--cookies')+1]);folder=Path(args[args.index('-o')+1]).parent
                used.append((folder,cookie));gate.wait(5)
                cookie.write_text('updated by engine')
                return SimpleNamespace(returncode=0,stdout=json.dumps({'id':'A'*11,'ext':'webm'}))
            with patch.object(worker.subprocess,'run',side_effect=engine):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    list(pool.map(lambda provider:worker.external_metadata(provider,'https://youtu.be/AAAAAAAAAAA',True),providers))
            self.assertEqual(len({folder for folder,cookie in used}),2)
            self.assertEqual(len({cookie for folder,cookie in used}),2)
            self.assertTrue(all(not cookie.exists() for folder,cookie in used))
            self.assertEqual(source.read_text(),'# Netscape HTTP Cookie File\n')
    def test_archive_checkpoint_does_not_destroy_previous_history_if_replace_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            archive=Path(directory)/'archive.txt';archive.write_text('previous\n')
            with patch.object(Path,'replace',side_effect=OSError('simulated locked file')):
                with self.assertRaises(OSError): worker.save_archive({'new'},archive)
            self.assertEqual(archive.read_text(),'previous\n')
            self.assertFalse(list(Path(directory).glob('*.tmp')))
            worker.save_archive({'previous','new'},archive)
            self.assertEqual(set(archive.read_text().splitlines()),{'previous','new'})
    def test_music_match_uses_standard_watch_page_and_same_runtime(self):
        args=worker.audio_command('https://music.youtube.com/watch?v=iIMxq_BUyZs',Path('cache'),'flac','session copy.txt',True)
        self.assertEqual(args[-1],'https://www.youtube.com/watch?v=iIMxq_BUyZs')
        self.assertEqual(Path(args[0]).name,'yt-dlp.exe')
        self.assertIn('--ignore-config',args)
        self.assertEqual(args[args.index('--cookies')+1],'session copy.txt')
        self.assertEqual(args[args.index('--js-runtimes')+1],'deno:'+str(worker.tools_directory()/'deno.exe'))
        self.assertIn('--no-simulate',args)
        self.assertNotIn('--audio-format',args)  # spotDL still converts and tags.
        self.assertEqual(args[-2],'--')
    def test_metadata_mode_does_not_download_audio(self):
        args=worker.audio_command('https://www.youtube.com/watch?v=iIMxq_BUyZs',Path('cache'),'opus')
        self.assertIn('--skip-download',args)
        self.assertNotIn('--no-simulate',args)
        self.assertNotIn('--cookies',args)
        with self.assertRaises(ValueError): worker.watch_url('https://evil.test/song')
    def test_external_result_is_used_without_embedded_extractor(self):
        try:
            from spotdl.providers.audio.base import AudioProvider,AudioProviderError
        except ImportError:
            self.skipTest('spotDL worker dependency not installed')
        with tempfile.TemporaryDirectory() as temporary:
            provider=SimpleNamespace(output_format='flac',cookie_file=None)
            metadata={'id':'iIMxq_BUyZs','ext':'webm','abr':128,'title':'Geburt Einer Nation'}
            with patch('spotdl.utils.config.get_temp_path',return_value=Path(temporary)),patch.object(worker.subprocess,'run') as engine:
                engine.return_value=SimpleNamespace(returncode=0,stdout=json.dumps(metadata))
                self.assertEqual(worker.external_metadata(provider,'https://music.youtube.com/watch?v=iIMxq_BUyZs',True),metadata)
                self.assertNotIn('stderr',engine.call_args.kwargs)  # actual auth errors reach GUI
                engine.return_value=SimpleNamespace(returncode=1,stdout='')
                with self.assertRaises(AudioProviderError): worker.external_metadata(provider,'https://www.youtube.com/watch?v=iIMxq_BUyZs',True)
                engine.return_value=SimpleNamespace(returncode=0,stdout='not JSON')
                with self.assertRaises(AudioProviderError): worker.external_metadata(provider,'https://www.youtube.com/watch?v=iIMxq_BUyZs')
            worker.install_audio_bridge()
            self.assertIs(AudioProvider.get_download_metadata,worker.external_metadata)


if __name__=='__main__': unittest.main()
