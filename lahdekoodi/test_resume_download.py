from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import tempfile
import threading
import unittest
import app
from download_rows import DownloadRows


class ResumeDownloadTests(unittest.TestCase):
    def request(self,source='YouTube'):
        return {'source':source,'items':[{'url':'https://youtu.be/AAAAAAAAAAA'}],'artist':None,
                'urls':['https://open.spotify.com/track/123'],'root':str(Path(tempfile.gettempdir())/'original-music'),
                'format':'flac','layout':app.FLAT_LAYOUT,'workers':5}
    def target(self,request=None):
        return SimpleNamespace(busy=False,paused_download=request,download_request=request,
            resume_cookie_selected=False,youtube_auth_required=False,cancel=threading.Event(),download_error='',
            download_rows=DownloadRows(),status=SimpleNamespace(set=Mock()),refresh_resume_button=Mock(),
            choose_youtube_cookies=Mock(),selected_cookies=Mock(return_value='new-cookies.txt'),
            start_download=Mock(),download_spotify=Mock(),log_line=Mock())
    def test_auth_failure_saves_snapshot_and_completed_rows_stay_complete(self):
        request=self.request();target=self.target(request);target.youtube_auth_required=True
        target.download_rows.update({'id':'finished','stage':'done'})
        target.download_rows.update({'id':'pending','stage':'queued'})
        app.App.finish_download(target)
        request['items'].clear()
        self.assertTrue(target.paused_download['items'])
        self.assertEqual(target.download_rows.rows['finished']['stage'],'done')
        self.assertEqual(target.download_rows.rows['pending']['stage'],'cancelled')
        self.assertFalse(target.active_download)
        self.assertFalse(target.resume_cookie_selected)
    def test_resume_uses_original_request_for_both_services(self):
        for source in ('YouTube','Spotify (spotDL)'):
            request=self.request(source);target=self.target(request);target.resume_cookie_selected=True
            for field in ('source','source_display','destination','format','layout','parallel','direct'):setattr(target,field,SimpleNamespace(set=Mock()))
            target.source_changed=Mock()
            app.App.resume_download(target)
            if source=='YouTube':target.start_download.assert_called_once_with(request['items'],None,resume=request)
            else:target.download_spotify.assert_called_once_with(request['urls'],resume=request)
            self.assertEqual(target.paused_download,request)
            target.destination.set.assert_called_once_with(request['root'])
            target.format.set.assert_called_once_with('flac')
            target.source.set.assert_called_once_with(source)
    def test_resume_never_starts_without_new_valid_cookie_selection_or_while_busy(self):
        for busy,ready,cookies in ((True,True,'new.txt'),(False,False,'new.txt'),(False,True,None),(False,True,'')):
            target=self.target(self.request());target.busy=busy;target.resume_cookie_selected=ready
            target.selected_cookies.return_value=cookies
            app.App.resume_download(target)
            target.start_download.assert_not_called();target.download_spotify.assert_not_called()
    def test_selecting_even_same_refreshed_cookie_path_enables_resume_and_cancel_keeps_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'cookies.txt';path.write_text('# Netscape HTTP Cookie File\n# synthetic refreshed session\n')
            target=self.target(self.request());target.cookie_file=SimpleNamespace(set=Mock())
            target.save_settings=Mock();target.refresh_cookie_label=Mock()
            with patch.object(app.filedialog,'askopenfilename',return_value=''):
                app.App.choose_youtube_cookies(target)
            self.assertFalse(target.resume_cookie_selected)
            with patch.object(app.filedialog,'askopenfilename',return_value=str(path)):
                app.App.choose_youtube_cookies(target)
            self.assertTrue(target.resume_cookie_selected)
            target.cookie_file.set.assert_called_once_with(str(path.resolve()))
            self.assertIn('Jatka jonoa',target.status.set.call_args.args[0])
    def test_new_job_replaces_old_resume_snapshot_without_storing_cookies(self):
        target=self.target(self.request());target.youtube_auth_required=True
        request=self.request('Spotify (spotDL)');app.App.remember_download(target,request)
        request['urls'].clear()
        self.assertTrue(target.download_request['urls']);self.assertIsNone(target.paused_download)
        self.assertFalse(target.youtube_auth_required);self.assertFalse(target.resume_cookie_selected)
        self.assertNotIn('cookies',target.download_request)
    def test_regular_completion_or_manual_stop_does_not_offer_cookie_resume(self):
        for cancelled in (True,False):
            target=self.target(self.request())
            if cancelled:target.cancel.set()
            app.App.finish_download(target)
            self.assertIsNone(target.paused_download)


if __name__=='__main__':unittest.main()
