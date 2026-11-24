import unittest
import json
import threading
from types import SimpleNamespace
from unittest.mock import Mock,patch
import app
from download_rows import DownloadRows,ROW_EVENT,parse_row,row_event


class DownloadRowTests(unittest.TestCase):
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
