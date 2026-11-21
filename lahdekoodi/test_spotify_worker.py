import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import spotify_worker as worker


class SpotifyWorkerTests(unittest.TestCase):
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
