import tempfile
from pathlib import Path
import unittest
import threading
from types import SimpleNamespace
from unittest.mock import Mock, patch
import app
from youtube_session import requires_youtube_auth, validate_cookie_file, isolated_cookie_arguments

class YouTubeSessionTests(unittest.TestCase):
    def test_original_cookie_file_survives_engine_writes_success_failure_and_cancel(self):
        with tempfile.TemporaryDirectory() as temporary:
            source=Path(temporary)/'original.txt'
            original=b'# Netscape HTTP Cookie File\n# synthetic test export\n'
            source.write_bytes(original)
            source_time=source.stat().st_mtime_ns
            for flag in ('--cookies','--cookie-file'):
                for outcome in ('success','failure','error_exit','cancel'):
                    with self.subTest(flag=flag,outcome=outcome):
                        target=SimpleNamespace(cancel=threading.Event(),emit=Mock())
                        used=[]
                        def engine(args,**kwargs):
                            cookie=Path(args[args.index(flag)+1]); used.append(cookie)
                            self.assertNotEqual(cookie,source)
                            self.assertEqual(cookie.read_bytes(),original)
                            cookie.write_text('# engine updated cookies\n')
                            if outcome=='failure': raise OSError('synthetic startup failure')
                            if outcome=='cancel': target.cancel.set()
                            return SimpleNamespace(stdout=iter([]),wait=lambda:1 if outcome=='error_exit' else 0,terminate=Mock())
                        arguments=['engine.exe',flag,str(source)]
                        with patch.object(app.subprocess,'Popen',side_effect=engine):
                            if outcome=='failure':
                                with self.assertRaises(OSError): app.App.execute(target,arguments)
                            else: app.App.execute(target,arguments)
                        self.assertEqual(source.read_bytes(),original)
                        self.assertEqual(source.stat().st_mtime_ns,source_time)
                        self.assertFalse(used[0].exists())
                        self.assertEqual(arguments[2],str(source))
    def test_capture_uses_disposable_copy_and_next_process_starts_from_original(self):
        with tempfile.TemporaryDirectory() as temporary:
            source=Path(temporary)/'original.txt'
            source.write_text('# Netscape HTTP Cookie File\n')
            args=['yt-dlp.exe','--cookies',str(source)]
            target=SimpleNamespace(cancel=threading.Event(),emit=Mock())
            def engine(arguments,**kwargs):
                cookie=Path(arguments[2])
                self.assertEqual(cookie.read_bytes(),source.read_bytes())
                cookie.write_text('modified by engine')
                return SimpleNamespace(communicate=lambda:('{}',''),returncode=0)
            with patch.object(app.subprocess,'Popen',side_effect=engine):
                self.assertEqual(app.App.execute(target,args,capture=True),'{}')
                self.assertEqual(app.App.execute(target,args,capture=True),'{}')
    def test_no_cookie_arguments_create_no_temporary_directory(self):
        with patch('youtube_session.tempfile.TemporaryDirectory') as temporary:
            with isolated_cookie_arguments(['engine.exe']) as args:
                self.assertEqual(args,['engine.exe'])
            temporary.assert_not_called()
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
