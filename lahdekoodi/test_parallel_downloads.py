import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import app
import youtube_parallel as parallel
from queue_progress import QueueProgress,PROGRESS,PARALLEL_PROGRESS
from download_rows import DownloadRows,parse_row


class ParallelDownloadTests(unittest.TestCase):
    def test_failed_metadata_cleanup_never_records_download_as_finished(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);tasks=self.tasks(root,1);archive=Path(tasks[0]['archive'])
            archive.write_text('youtube previous\n')
            class Process:
                def __init__(self,args,**kwargs):self.args=args;self.stdout=iter([])
                def wait(self):
                    Path(self.args[self.args.index('--download-archive')+1]).write_text('youtube AAAAAAAAAAA\n')
                    return 0
            with patch.object(parallel.subprocess,'Popen',side_effect=Process),patch.object(parallel,'finalize_download',side_effect=ValueError('tag cleanup failed')):
                self.assertEqual(parallel.Batch(tasks,1,'',root,lambda line:None).run(),1)
            self.assertEqual(archive.read_text(),'youtube previous\n')
    def test_larger_selected_limits_really_run_simultaneously(self):
        for count in (5,15,20):
            with self.subTest(workers=count),tempfile.TemporaryDirectory() as directory:
                root=Path(directory); gate=threading.Barrier(count);lock=threading.Lock()
                counts={'running':0,'peak':0}
                args=app.command('https://www.youtube.com/playlist?list=test',root,'flac')
                tasks=[{'id':f'{i:011d}','command':args,'archive':str(root/'archive.txt'),'index':i+1} for i in range(count)]
                class Process:
                    def __init__(self,args,**kwargs): self.stdout=self.lines()
                    def lines(self):
                        with lock:
                            counts['running']+=1;counts['peak']=max(counts['peak'],counts['running'])
                        gate.wait(timeout=10)
                        yield PROGRESS+'{"downloaded":1,"total":1}'
                    def wait(self):
                        with lock:counts['running']-=1
                        return 0
                with patch.object(parallel.subprocess,'Popen',side_effect=Process),patch.object(parallel,'finalize_download',return_value=''):
                    self.assertEqual(parallel.Batch(tasks,count,'',root,lambda line:None).run(),0)
                self.assertEqual(counts['peak'],count)
                spotify=app.spot_command('https://open.spotify.com/album/123',root,'flac',workers=count)
                self.assertEqual(spotify[spotify.index('--threads')+1],str(count))
    def tasks(self,root,count=4):
        args=app.command('https://www.youtube.com/playlist?list=example',root,'flac')
        return [{'id':letter*11,'command':args,'archive':str(root/'.archive-flac.txt'),'index':i+1}
                for i,letter in enumerate('ABCD'[:count])]

    def test_two_files_really_overlap_and_archive_keeps_successes_after_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); tasks=self.tasks(root)
            archive=Path(tasks[0]['archive']); archive.write_text('youtube previous\n')
            gate=threading.Barrier(2); lock=threading.Lock(); counts={'running':0,'peak':0}; records=[]
            class Process:
                def __init__(self,args,**kwargs):
                    self.args=args
                    self.id=args[-1].split('=')[-1]
                    self.returncode=None
                    self.stdout=self.lines()
                def lines(self):
                    with lock:
                        counts['running']+=1; counts['peak']=max(counts['peak'],counts['running'])
                    gate.wait(timeout=5)
                    yield PROGRESS+'{"downloaded":100,"total":100}'
                def wait(self):
                    with lock: counts['running']-=1
                    self.returncode=1 if self.id=='B'*11 else 0
                    if not self.returncode: Path(self.args[self.args.index('--download-archive')+1]).write_text('youtube '+self.id+'\n')
                    return self.returncode
            with patch.object(parallel.subprocess,'Popen',side_effect=Process),patch.object(parallel,'finalize_download',return_value=''):
                self.assertEqual(parallel.Batch(tasks,2,'',root,records.append).run(),1)
            self.assertEqual(counts['peak'],2)
            self.assertEqual(set(archive.read_text().splitlines()),{'youtube previous','youtube '+'A'*11,'youtube '+'C'*11,'youtube '+'D'*11})
            progress=[json.loads(line[len(PARALLEL_PROGRESS):]) for line in records if line.startswith(PARALLEL_PROGRESS)]
            self.assertEqual(progress[-1]['completed'],4); self.assertEqual(progress[-1]['failed'],1)
            self.assertEqual(progress[-1]['running'],0)
            table=DownloadRows()
            for line in records:
                event=parse_row(line)
                if event:table.update(event)
            self.assertEqual([row['title'] for row in table.rows.values() if row['stage']=='error'],['B'*11])
            self.assertTrue(all(row['stage']=='done' for row in table.rows.values() if row['title']!='B'*11))

    def test_auth_stops_other_processes_and_does_not_start_pending_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); tasks=self.tasks(root,3)
            gate=threading.Barrier(2); killed=threading.Event(); processes=[]; records=[]
            class Process:
                def __init__(self,args,**kwargs):
                    self.id=args[-1].split('=')[-1]; self.pid=100+len(processes); self.returncode=None
                    processes.append(self); self.stdout=self.lines()
                def lines(self):
                    gate.wait(timeout=5)
                    if self.id=='A'*11: yield "ERROR: Sign in to confirm you're not a bot"
                    else: self.assert_killed()
                def assert_killed(self):
                    if not killed.wait(5): raise AssertionError('Other process was not stopped')
                def poll(self): return self.returncode
                def wait(self): return 1
            def terminate(args,**kwargs):
                pid=int(args[args.index('/PID')+1])
                next(p for p in processes if p.pid==pid).returncode=1
                killed.set()
            with patch.object(parallel.subprocess,'Popen',side_effect=Process),patch.object(parallel.subprocess,'run',side_effect=terminate):
                self.assertEqual(parallel.Batch(tasks,2,'',root,records.append).run(),2)
            self.assertEqual(len(processes),2)
            self.assertLess(json.loads(records[-1][len(PARALLEL_PROGRESS):])['completed'],len(tasks))

    def test_cookie_copies_are_independent_and_original_is_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); source=root/'original.txt'; original='# Netscape HTTP Cookie File\n'
            source.write_text(original); before=source.stat().st_mtime_ns; used=[]
            class Process:
                def __init__(self,args,**kwargs):
                    cookie=Path(args[args.index('--cookies')+1]); used.append(cookie)
                    if cookie.read_text()!=original: raise AssertionError('Session copied from another download')
                    cookie.write_text('engine modifications'); self.stdout=iter([])
                def wait(self): return 0
            with patch.object(parallel.subprocess,'Popen',side_effect=Process),patch.object(parallel,'finalize_download',return_value=''):
                self.assertEqual(parallel.Batch(self.tasks(root,2),2,str(source),root,lambda line:None).run(),0)
            self.assertEqual(source.read_text(),original); self.assertEqual(source.stat().st_mtime_ns,before)
            self.assertEqual(len(set(used)),2); self.assertTrue(all(not file.exists() for file in used))

    def test_whole_playlist_is_expanded_and_duplicate_video_is_not_scheduled_twice(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); args=app.command('https://www.youtube.com/playlist?list=test',root,'flac')
            response=SimpleNamespace(returncode=0,stderr='',stdout=json.dumps({'entries':[{'id':'A'*11},{'id':'B'*11}]}))
            with patch.object(parallel.subprocess,'run',return_value=response) as engine:
                tasks=parallel.prepare_tasks([{'command':args},{'command':args}],'',root,lambda line:None)
            self.assertEqual([task['id'] for task in tasks],['A'*11,'B'*11])
            self.assertNotIn('--playlist-items',engine.call_args.args[0])

    def test_progress_aggregates_out_of_order_completions(self):
        tracker=QueueProgress(clock=lambda:10.); tracker.begin(1)
        tracker.consume(PARALLEL_PROGRESS+json.dumps({'total':4,'completed':1,'partial':1.5,'failed':0,'running':2}))
        self.assertAlmostEqual(tracker.snapshot()['fraction'],.625)
        self.assertIn('1/4 tiedostoa',tracker.snapshot()['text'])
        self.assertIn('2 käynnissä',tracker.snapshot()['text'])
        tracker.consume('2/4 complete')
        self.assertAlmostEqual(tracker.snapshot()['fraction'],.625)
        tracker.stop(cancelled=True)
        self.assertLess(tracker.snapshot()['percent'],100)
        self.assertIn('keskeytetty',tracker.snapshot()['text'])

    def test_spotify_uses_one_shared_limit_across_all_input_links(self):
        urls=['https://open.spotify.com/track/123','https://open.spotify.com/track/456']
        args=app.spot_command(urls,Path('music'),'flac',workers=3)
        self.assertEqual(args[2:4],urls)
        self.assertEqual(args[args.index('--threads')+1],'3')
        self.assertEqual(app.download_workers(100),20)
        self.assertEqual(app.download_workers('invalid'),2)


if __name__=='__main__': unittest.main()
