"""Bounded parallel YouTube file downloads, behind the desktop UI."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import hashlib
import os
from pathlib import Path
import re
import subprocess
import tempfile
import threading
from queue_progress import PROGRESS, TRACK_DONE, PARALLEL_PROGRESS
from youtube_session import isolated_cookie_arguments, requires_youtube_auth
from download_rows import row_event
from music_files import youtube_identity,publish_music

NO_WINDOW=getattr(subprocess,'CREATE_NO_WINDOW',0)
OUTPUT_LOCK=threading.Lock()


def output(line):
    with OUTPUT_LOCK: print(line,flush=True)


def finalize_download(temporary,task,filename):
    root=Path(temporary).resolve();fmt=task['command'][task['command'].index('--audio-format')+1]
    source=Path(filename).resolve() if filename else root/(task['id']+'.'+fmt)
    if not source.is_relative_to(root) or not source.is_file():raise ValueError('Valmistunutta äänitiedostoa ei löytynyt.')
    metadata=root/(task['id']+'.info.json')
    info=json.loads(metadata.read_text(encoding='utf-8')) if metadata.exists() else {}
    title,artists=youtube_identity(info,task.get('artist',''),task.get('title',''))
    task['title']=title;task['artist']=', '.join(artists)
    destination=Path(task['command'][task['command'].index('-P')+1])
    return str(publish_music(source,destination,title,artists))


class Batch:
    def __init__(self,tasks,workers,cookies,workspace,emit=output):
        self.tasks=tasks; self.workers=max(1,min(20,int(workers)))
        self.cookies=cookies; self.workspace=Path(workspace); self.emit=emit
        self.lock=threading.RLock(); self.archives_lock=threading.Lock()
        self.stopped=threading.Event(); self.authentication=False
        self.processes=set(); self.partial={}; self.completed=set(); self.failed=set()

    def report(self):
        # Called under the lock so progress records cannot arrive out of order.
        self.emit(PARALLEL_PROGRESS+json.dumps({'total':len(self.tasks),'completed':len(self.completed),
            'partial':sum(self.partial.values()),'failed':len(self.failed),'running':len(self.partial)}))

    def row(self,number,task,**values):
        key='youtube:'+hashlib.sha256((str(task.get('archive',''))+'|'+str(task.get('id',number))).encode()).hexdigest()
        row_event(self.emit,key,title=task.get('title') or task.get('id') or 'Kappale',
                  artist=task.get('artist',''),album=task.get('album',''),source='YouTube',**values)

    def halt(self):
        with self.lock:
            self.authentication=True; self.stopped.set()
            for process in list(self.processes):
                if process.poll() is None:
                    subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,creationflags=NO_WINDOW)

    def merge_archive(self,source,destination):
        if not source.exists(): return
        with self.archives_lock:
            previous=set(destination.read_text(encoding='utf-8').splitlines()) if destination.exists() else set()
            added=set(source.read_text(encoding='utf-8').splitlines())-previous
            if added:
                destination.parent.mkdir(parents=True,exist_ok=True)
                with destination.open('a',encoding='utf-8') as archive:
                    for line in sorted(added): archive.write(line+'\n')

    def download(self,number,task):
        if self.stopped.is_set(): return
        with self.lock:
            self.partial[number]=0.; self.report()
        failed=False; process=None; skipped=False; last_error=''; filename='';published=False
        try:
            if task.get('error'): raise ValueError(task['error'])
            archive=Path(task['archive'])
            with self.archives_lock:
                archived=set(archive.read_text(encoding='utf-8').splitlines()) if archive.exists() else set()
            if 'youtube '+task['id'] in archived:
                skipped=True
                self.emit(f"[{number+1}/{len(self.tasks)}] Ohitetaan jo ladattu kappale: {task['id']}")
                return
            self.row(number,task,stage='downloading',percent=0)
            with tempfile.TemporaryDirectory(prefix='track-',dir=self.workspace) as temporary:
                private_archive=Path(temporary)/'archive.txt'
                args=list(task['command'])
                args[args.index('--download-archive')+1]=str(private_archive)
                args[args.index('-o')+1]='%(id)s.%(ext)s'
                args[args.index('-P')+1]=temporary
                args[1:1]=['--write-info-json']
                args[-1]='https://www.youtube.com/watch?v='+task['id']
                args[args.index('--yes-playlist')]='--no-playlist'
                if self.cookies: args[1:1]=['--cookies',self.cookies]
                with isolated_cookie_arguments(args,self.workspace) as args:
                    with self.lock:
                        if self.stopped.is_set(): return
                        process=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                            text=True,encoding='utf-8',errors='replace',creationflags=NO_WINDOW)
                        self.processes.add(process)
                    try:
                        for raw in process.stdout:
                            line=raw.strip()
                            if line.startswith((PROGRESS,TRACK_DONE)):
                                try:
                                    if line.startswith(TRACK_DONE):
                                        fraction=.99
                                        done=json.loads(line[len(TRACK_DONE):]);filename=done.get('filename','')
                                    else:
                                        data=json.loads(line[len(PROGRESS):]); total=float(data.get('total') or 0)
                                        fraction=min(.9,.9*float(data.get('downloaded') or 0)/total) if total>0 else 0.
                                    self.row(number,task,stage='converting' if line.startswith(TRACK_DONE) else 'downloading',percent=fraction*100,filename=filename)
                                    with self.lock:
                                        self.partial[number]=max(self.partial[number],fraction); self.report()
                                except (ValueError,TypeError,ZeroDivisionError): pass
                            elif line:
                                if line.startswith('ERROR:') or requires_youtube_auth(line):
                                    last_error=line.removeprefix('ERROR:').strip()
                                    self.row(number,task,stage='error',error=last_error)
                                elif line.startswith(('[ExtractAudio]','[Metadata]')):
                                    self.row(number,task,stage='converting',percent=90)
                                self.emit(f'[{number+1}/{len(self.tasks)}] {line}')
                                if requires_youtube_auth(line): self.halt(); break
                        failed=bool(process.wait())
                        if not failed and not self.stopped.is_set():
                            filename=finalize_download(temporary,task,filename);published=True
                    finally:
                        # A completed file's history is retained even if another
                        # concurrent download fails or requests authentication.
                        if published:self.merge_archive(private_archive,archive)
                        with self.lock: self.processes.discard(process)
        except Exception as error:
            failed=True; last_error=str(error)
            self.row(number,task,stage='error',error=last_error)
            self.emit(f'ERROR: [{number+1}/{len(self.tasks)}] {error}')
        finally:
            with self.lock:
                self.partial.pop(number,None)
                stage='error' if failed or last_error else ('cancelled' if self.stopped.is_set() else ('skipped' if skipped else 'done'))
                self.row(number,task,stage=stage,error=last_error or ('Lataus epäonnistui. Katso tarkempi loki.' if failed else ''),filename=filename)
                if not self.stopped.is_set():
                    self.completed.add(number)
                    if failed: self.failed.add(number)
                self.report()

    def run(self):
        for number,task in enumerate(self.tasks): self.row(number,task,stage='queued')
        with self.lock: self.report()
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            # Workers check the stop event before creating another process.
            list(pool.map(lambda item:self.download(*item),enumerate(self.tasks)))
        return 2 if self.authentication else int(bool(self.failed))


def prepare_tasks(jobs,cookies,workspace,emit=output):
    tasks=[]; seen=set()
    for number,job in enumerate(jobs,1):
        emit(f'Luetaan kappalelista {number}/{len(jobs)}…')
        args=job['command']
        metadata=[args[0],'--ignore-config','--flat-playlist','--dump-single-json','--socket-timeout','25',
                  '--retries','3','--js-runtimes',args[args.index('--js-runtimes')+1],
                  *(['--cookies',cookies] if cookies else []),'--',args[-1]]
        try:
            with isolated_cookie_arguments(metadata,workspace) as metadata:
                result=subprocess.run(metadata,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                    encoding='utf-8',errors='replace',creationflags=NO_WINDOW,timeout=180)
            for line in result.stderr.splitlines():
                if line.strip(): emit(line)
            if requires_youtube_auth(result.stderr): return None
            if result.returncode: raise ValueError('Kappalelistan lukeminen epäonnistui.')
            info=json.loads(result.stdout)
            entries=info.get('entries') if 'entries' in info else [info]
            if not entries: raise ValueError('Soittolistasta ei löytynyt ladattavia kappaleita.')
            archive=args[args.index('--download-archive')+1]
            for index,entry in enumerate(entries,1):
                video=str((entry or {}).get('id') or '')
                if not re.fullmatch(r'[A-Za-z0-9_-]{11}',video):
                    tasks.append({'error':f'Julkaisun {number} kappaleen {index} YouTube-tunniste puuttuu.'}); continue
                key=(os.path.normcase(str(Path(archive).resolve())),video)
                if key in seen: continue
                seen.add(key)
                title,artists=youtube_identity(entry,job.get('artist') or entry.get('channel') or '',entry.get('title') or video)
                tasks.append({'command':args,'id':video,'index':index,'archive':archive,
                              'title':title,'artist':', '.join(artists),
                              'album':job.get('album','')})
        except Exception as error:
            tasks.append({'error':str(error)})
    return tasks


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('manifest',nargs='?',type=Path); parser.add_argument('--workers',type=int,choices=range(1,21),default=2)
    parser.add_argument('--cookies',default=''); parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test: print('Parallel YouTube worker dependencies OK'); return 0
    if args.manifest is None: parser.error('manifest required')
    jobs=json.loads(args.manifest.read_text(encoding='utf-8'))
    with tempfile.TemporaryDirectory(prefix='youtube-',dir=os.environ.get('ALBUMILATAAJA_WORKSPACE')) as workspace:
        tasks=prepare_tasks(jobs,args.cookies,workspace)
        if tasks is None: return 2
        if not tasks: output('ERROR: Latausjono on tyhjä.'); return 1
        return Batch(tasks,args.workers,args.cookies,workspace).run()


if __name__=='__main__': raise SystemExit(main())
