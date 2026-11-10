import tempfile
import unittest
from pathlib import Path
import app
import hashlib
import threading
from types import SimpleNamespace
from unittest.mock import patch

class AppTests(unittest.TestCase):
    def test_album_folders_and_order(self):
        self.assertEqual(app.album_folder('Albumi','2026-11-10'),'2026 - Albumi')
        self.assertEqual(app.album_folder('Albumi',None),'Albumi')
        data=[{'title':'Old','year':1999},{'title':'Unknown'},{'title':'New','year':'2026'}]
        self.assertEqual([a['title'] for a in app.newest_first(data)],['New','Old','Unknown'])
    def test_output_stays_below_destination(self):
        for value in ['../../elsewhere','CON','a/b\\c','NUL.txt','..','album: name']:
            name=app.safe_name(value)
            self.assertNotIn('/',name); self.assertNotIn('\\',name)
            self.assertTrue(name); self.assertNotEqual(name,'..')
        self.assertEqual(app.safe_name('CON'),'_CON')

    def test_external_and_option_injection_rejected(self):
        for value in ['--exec=calc','file:///tmp/a','https://youtube.com.evil.test/watch?v=x','http://youtube.com/watch?v=x']:
            with self.assertRaises(ValueError): app.youtube_url(value)
        for value in ['https://open.spotify.com.evil.test/artist/123','--user-auth','https://open.spotify.com/user/123']:
            with self.assertRaises(ValueError): app.spotify_url(value)
        app.spotify_url('https://open.spotify.com/intl-fi/artist/123?si=test')

    def test_versions_are_numeric(self):
        self.assertGreater(app.version_tuple('v1.10.0'),app.version_tuple('1.9.0'))
        with self.assertRaises(ValueError): app.version_tuple('v1.0.0/../../evil')

    def test_format_archives_are_separate(self):
        root=Path(tempfile.gettempdir())/'artist name'/'album name'
        url='https://www.youtube.com/watch?v=123'
        one=app.command(url,root,'flac'); two=app.command(url,root,'opus')
        self.assertNotEqual(one[one.index('--download-archive')+1],two[two.index('--download-archive')+1])
        self.assertEqual(one[-2:],[ '--',url])
        self.assertEqual(one[one.index('-P')+1],str(root))
        spotify=app.spot_command('https://open.spotify.com/artist/123',root,'flac')
        self.assertIn('--headless',spotify); self.assertIn('{album}',spotify[spotify.index('--output')+1])

    def test_update_integrity_before_install(self):
        payload=b'installer test bytes'
        prefix='https://github.com/'+app.REPOSITORY+'/releases/download/v1.1.0/'
        release={'tag_name':'v1.1.0','assets':[{'name':name,'browser_download_url':prefix+name} for name in ['Albumilataaja-Setup.exe','SHA256SUMS.txt']]}
        class Response:
            def __init__(self,text=''): self.text=text
            def raise_for_status(self): pass
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def iter_content(self,size): yield payload
        fake=SimpleNamespace(busy=False,cancel=threading.Event(),emit=lambda *args:None,run_job=lambda fn:fn())
        for valid in [True,False]:
            with tempfile.TemporaryDirectory() as tmp:
                digest=hashlib.sha256(payload).hexdigest() if valid else '0'*64
                responses=[Response(digest+'  Albumilataaja-Setup.exe'),Response()]
                with patch.object(app.messagebox,'askyesno',return_value=True),patch.object(app.requests,'get',side_effect=responses),patch.object(app.tempfile,'mkdtemp',return_value=tmp),patch.object(app.os,'startfile') as launch:
                    if valid:
                        app.App.offer_update(fake,release)
                        launch.assert_called_once()
                        self.assertEqual(Path(launch.call_args.args[0]).read_bytes(),payload)
                    else:
                        with self.assertRaises(ValueError): app.App.offer_update(fake,release)
                        launch.assert_not_called()
                        self.assertFalse((Path(tmp)/'Albumilataaja-Setup.exe').exists())

if __name__=='__main__': unittest.main()
