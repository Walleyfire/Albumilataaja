import unittest
import json
import threading
from types import SimpleNamespace
from unittest.mock import Mock,patch
import app
from download_rows import DownloadRows,ROW_EVENT,parse_row,row_event


class DownloadRowTests(unittest.TestCase):
    def test_youtube_queue_worker_can_checkpoint_concurrent_completion_after_auth_warning(self):
        done={'id':'finished','stage':'done','filename':'Artist - Song.flac'}
        process=SimpleNamespace(pid=123,stdout=iter(['WARNING: [youtube] The provided YouTube account cookies are no longer valid.',ROW_EVENT+json.dumps(done)]),wait=lambda:2)
        target=SimpleNamespace(cancel=threading.Event(),emit=Mock())
        with patch.object(app.subprocess,'Popen',return_value=process),patch.object(app.subprocess,'run') as terminate:
            self.assertEqual(app.App.execute(target,['youtube-parallel.exe']),2)
        terminate.assert_not_called()
        self.assertTrue(target.youtube_auth_required)
        self.assertIn(('download_row',done),[call.args for call in target.emit.call_args_list])
    def test_resume_preserves_completed_rows_and_resets_only_unfinished_rows(self):
        rows=DownloadRows()
        rows.update({'id':'finished','stage':'done','filename':'Artist - Song.flac'})
        rows.update({'id':'pending','stage':'error','percent':80,'error':'expired cookies'})
        rows.resume()
        self.assertEqual(list(rows.rows),['finished','pending'])
        self.assertEqual(rows.rows['finished']['stage'],'done');self.assertEqual(rows.rows['finished']['percent'],100)
        self.assertEqual(rows.rows['pending']['stage'],'queued');self.assertIsNone(rows.rows['pending']['percent'])
        self.assertEqual(rows.rows['pending']['error'],'')
        rows.update({'id':'pending','stage':'downloading','percent':5})
        self.assertEqual(rows.rows['pending']['percent'],5)
    def test_engine_reports_file_error_before_auth_stops_queue(self):
        data={'id':'blocked','stage':'error','error':'YouTube vaatii varmistuksen.'}
        process=SimpleNamespace(pid=123,stdout=iter([ROW_EVENT+json.dumps(data),"ERROR: Sign in to confirm you're not a bot"]),wait=lambda:1)
        target=SimpleNamespace(cancel=threading.Event(),emit=Mock())
        with patch.object(app.subprocess,'Popen',return_value=process),patch.object(app.subprocess,'run'):
            app.App.execute(target,['worker.exe'])
        self.assertEqual(target.emit.call_args_list[0].args,('download_row',data))
        self.assertTrue(target.youtube_auth_required)
        self.assertTrue(target.download_errors)
    def test_parallel_errors_belong_to_their_own_file(self):
        rows=DownloadRows()
        for key in ('one','two'):rows.update({'id':key,'title':key,'stage':'downloading','percent':25})
        rows.update({'id':'two','stage':'error','error':'Video ei ole saatavilla.'})
        rows.update({'id':'one','stage':'done','filename':'D:/Music/one.flac'})
        rows.update({'id':'two','stage':'downloading','percent':80})
        self.assertEqual(rows.rows['two']['stage'],'error')
        self.assertEqual(rows.rows['two']['error'],'Video ei ole saatavilla.')
        self.assertEqual(rows.rows['one']['percent'],100)
        self.assertFalse(rows.rows['one']['error'])
    def test_cancel_keeps_completed_files_and_marks_pending_ones(self):
        rows=DownloadRows();rows.update({'id':'done','stage':'done'});rows.update({'id':'pending','stage':'queued'})
        rows.finish(cancelled=True,error='Jono pysäytetty.')
        self.assertEqual(rows.rows['done']['stage'],'done')
        self.assertEqual(rows.rows['pending']['stage'],'cancelled')
        self.assertEqual(rows.rows['pending']['error'],'Jono pysäytetty.')
    def test_event_roundtrip_and_malformed_records(self):
        lines=[];row_event(lines.append,'song',title='Ääni',stage='downloading',percent=12)
        rows=DownloadRows();rows.update(parse_row(lines[0]))
        self.assertEqual(rows.rows['song']['title'],'Ääni')
        self.assertIsNone(parse_row('ordinary log line'))
        self.assertEqual(parse_row(ROW_EVENT+'not-json'),{})
        rows.update({'id':'song','percent':float('nan')});self.assertEqual(rows.rows['song']['percent'],12)


if __name__=='__main__':unittest.main()
