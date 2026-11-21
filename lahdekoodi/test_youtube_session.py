import tempfile
from pathlib import Path
import unittest
import threading
from types import SimpleNamespace
from unittest.mock import Mock, patch
import app
from youtube_session import requires_youtube_auth, validate_cookie_file

class YouTubeSessionTests(unittest.TestCase):
    def test_detect_challenge_but_not_metadata_warning(self):
        self.assertTrue(requires_youtube_auth("ERROR: Sign in to confirm you’re not a bot"))
        self.assertTrue(requires_youtube_auth("ERROR: Sign in to confirm you're not a bot"))
        self.assertFalse(requires_youtube_auth('WARNING: No title found in player responses'))
    def test_cookie_path_is_explicit_and_shared_with_both_download_engines(self):
        self.assertEqual(validate_cookie_file(''),'')
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'user chosen cookies.txt'; path.write_text('# Netscape HTTP Cookie File\n',encoding='utf-8')
            yt=app.command('https://www.youtube.com/watch?v=123',Path(temporary),'flac',str(path))
            spotify=app.spot_command('https://open.spotify.com/track/123',Path(temporary),'flac',cookie_file=str(path))
            self.assertEqual(yt[yt.index('--cookies')+1],str(path.resolve()))
            self.assertEqual(spotify[spotify.index('--cookie-file')+1],str(path.resolve()))
            self.assertNotIn('--cookies-from-browser',yt)
            path.write_text('not a cookie file',encoding='utf-8')
            with self.assertRaises(ValueError): validate_cookie_file(str(path))
    def test_cookie_free_default_does_not_read_browser_profiles(self):
        args=app.command('https://www.youtube.com/watch?v=123',Path('music'),'flac')
        self.assertNotIn('--cookies',args); self.assertNotIn('--cookies-from-browser',args)
    def test_engine_is_stopped_at_challenge_and_later_items_are_not_processed(self):
        process=SimpleNamespace(pid=123,stdout=iter(["ERROR: [youtube] Sign in to confirm you're not a bot\n",'SHOULD NOT RUN\n']),wait=lambda:1)
        target=SimpleNamespace(cancel=threading.Event(),emit=Mock())
        with patch.object(app.subprocess,'Popen',return_value=process),patch.object(app.subprocess,'run') as terminate:
            self.assertEqual(app.App.execute(target,['yt-dlp.exe']),1)
        self.assertTrue(target.youtube_auth_required)
        terminate.assert_called_once()
        self.assertIn('/T',terminate.call_args.args[0])
        self.assertFalse(any('SHOULD NOT RUN' in str(call) for call in target.emit.call_args_list))

if __name__=='__main__': unittest.main()
