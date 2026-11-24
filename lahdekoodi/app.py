import hashlib
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from appearance import build_interface, apply_theme, dark_titlebar
from queue_progress import QueueProgress, PROGRESS, TRACK_DONE
from download_rows import DownloadRows,parse_row
from tool_updates import check_updates as check_tool_releases,install_updates as install_tool_releases,newer
from tool_dialog import ToolDialog
from youtube_session import validate_cookie_file, requires_youtube_auth, AUTH_HELP, isolated_cookie_arguments
from urllib.parse import urlparse
import webbrowser
import requests

VERSION = '1.3.0'
FLAT_LAYOUT = 'Suoraan tallennuskansioon'
REPOSITORY = 'Walleyfire/Albumilataaja'
BASE = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
TOOLS = BASE / 'tools'
STATE = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'Albumilataaja'
STATE.mkdir(parents=True, exist_ok=True)
PREVIEW = os.environ.get('ALBUMILATAAJA_PREVIEW') == '1'
CONFIG = STATE / ('preview-settings.json' if PREVIEW else 'settings.json')
NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

def safe_name(value):
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', str(value)).strip(' .')[:100] or 'Tuntematon'
    if value.upper().split('.')[0] in {'CON','PRN','AUX','NUL', *('COM'+str(i) for i in range(1,10)), *('LPT'+str(i) for i in range(1,10))}:
        value = '_' + value
    return value

def release_year(value):
    match=re.search(r'\b((?:19|20)\d{2})\b',str(value or ''))
    return match.group(1) if match else ''

def album_folder(title,year,layout='Vuosi - Albumi'):
    year=release_year(year)
    if layout=='Albumi, Vuosi': return safe_name(title+(', '+year if year else ''))
    return safe_name((year+' - ' if year else '')+title)

def download_folder(root,artist,title,year,layout):
    if layout==FLAT_LAYOUT: return Path(root)
    return Path(root)/safe_name(artist)/album_folder(title,year,layout)

def download_workers(value):
    try: return max(1,min(20,int(value)))
    except (ValueError,TypeError): return 2

def newest_first(albums):
    return sorted(albums,key=lambda a:(-(int(release_year(a.get('year'))) if release_year(a.get('year')) else 0),a.get('title','').casefold()))

def youtube_url(value):
    p = urlparse(value)
    if p.scheme != 'https' or p.hostname not in ('youtube.com','www.youtube.com','music.youtube.com','youtu.be') or any(c.isspace() for c in value):
        raise ValueError('Liitä https-alkuinen YouTube-linkki.')
    return value

def download_links(value,validator):
    links=[]
    for number,line in enumerate(value.splitlines(),1):
        line=line.strip()
        if not line: continue
        try: url=validator(line)
        except ValueError as error: raise ValueError(f'Rivi {number}: {error}') from None
        if url not in links: links.append(url)
    if not links: raise ValueError('Liitä vähintään yksi latauslinkki, yksi linkki riville.')
    return links

def version_tuple(value):
    if not re.fullmatch(r'v?\d+\.\d+\.\d+', value):
        raise ValueError('Virheellinen versionumero')
    return tuple(map(int, value.lstrip('v').split('.')))

def spotify_url(value):
    p = urlparse(value)
    if p.scheme != 'https' or p.hostname != 'open.spotify.com' or not re.fullmatch(r'/(?:intl-[a-z]+/)?(?:artist|album|playlist|track)/[A-Za-z0-9]+', p.path.rstrip('/')):
        raise ValueError('Liitä Spotify-artistin, albumin, soittolistan tai kappaleen https://open.spotify.com/…-linkki.')
    return value

def spot_command(url, root, fmt,layout='Vuosi - Albumi',cookie_file='',workers=1):
    album='{album}, {year}' if layout=='Albumi, Vuosi' else '{year} - {album}'
    flat=layout==FLAT_LAYOUT
    output=root/'[{track-id}] {artist} - {title}.{output-ext}' if flat else root/'{album-artist}'/album/'{disc-number}-{track-number} - {title}.{output-ext}'
    archive=root/(('.spotdl-archive-direct-' if flat else '.spotdl-archive-')+fmt+'.txt')
    urls=[spotify_url(value) for value in url] if isinstance(url,(list,tuple)) else [spotify_url(url)]
    return [str(TOOLS/'spotdl.exe'), 'download', *urls, '--headless',
            *(['--cookie-file',validate_cookie_file(cookie_file)] if cookie_file else []),
            '--ffmpeg', str(TOOLS/'ffmpeg.exe'), '--format', fmt, '--threads', str(download_workers(workers)),
            '--output', str(output),
            '--overwrite', 'skip', '--archive', str(archive),
            '--simple-tui', '--print-errors', '--max-retries', '3',
            '--max-filename-length', '170']

def command(url, folder, fmt,cookie_file=''):
    return [str(TOOLS/'yt-dlp.exe'), '--ignore-config', '--no-color', '--newline',
            *(['--cookies',validate_cookie_file(cookie_file)] if cookie_file else []),
            '--sleep-interval','5','--max-sleep-interval','10',
            '--js-runtimes', 'deno:'+str(TOOLS/'deno.exe'), '--ffmpeg-location', str(TOOLS),
            '--windows-filenames', '--trim-filenames', '170', '--socket-timeout', '25',
            '--retries', '3', '--no-overwrites', '--yes-playlist', '-f', 'bestaudio/best',
            '-x', '--audio-format', fmt, '--embed-metadata', '--no-simulate', '--progress', '--progress-delta', '0.5',
            '--progress-template', 'download:'+PROGRESS+'{"downloaded":%(progress.downloaded_bytes|0)j,"total":%(progress.total_bytes,progress.total_bytes_estimate|0)j,"index":%(info.playlist_index|1)j,"count":%(info.n_entries,info.playlist_count|1)j}',
            '--print', 'after_move:'+TRACK_DONE+'{"index":%(playlist_index|1)j,"count":%(n_entries,playlist_count|1)j,"filename":%(filepath|)j}',
            '--download-archive', str(folder/('.archive-'+fmt+'.txt')),
            '-P', str(folder), '-o', '%(playlist_index|1)02d - %(title).140s [%(id)s].%(ext)s', '--', youtube_url(url)]

class App(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode('dark')
        super().__init__()
        icon=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))/'app.ico'
        if icon.exists(): self.after(300,lambda:self.iconbitmap(str(icon)))
        self.title('Albumilataaja · Esikatselu' if PREVIEW else 'Albumilataaja')
        self.geometry('1180x960'); self.minsize(1040,900)
        self.events=queue.Queue(); self.proc=None; self.busy=False
        self.cancel=threading.Event()
        try:
            settings_path=CONFIG if CONFIG.exists() or not PREVIEW else STATE/'settings.json'
            settings=json.loads(settings_path.read_text(encoding='utf-8'))
        except (OSError,ValueError): settings={}
        self.destination=tk.StringVar(value=settings.get('destination',str(Path.home()/'Music'/'Albumilataaja')))
        self.format=tk.StringVar(value=settings.get('format','flac'))
        self.source=tk.StringVar(value=settings.get('source','YouTube'))
        self.layout=tk.StringVar(value=settings.get('layout','Albumi, Vuosi'))
        self.parallel=tk.StringVar(value=str(download_workers(settings.get('parallel_downloads',2))))
        self.status=tk.StringVar(value='Liitä valitun palvelun linkit, yksi linkki riville.')
        self.cookie_file=tk.StringVar(value=settings.get('youtube_cookie_file',''))
        self.youtube_auth_required=False
        self.queue_summary=tk.StringVar(value=''); self.queue_tracker=QueueProgress()
        self.download_rows=DownloadRows(); self.active_download=False; self.download_error=''
        build_interface(self,settings,preview=PREVIEW)
        self.protocol('WM_DELETE_WINDOW',self.close); self.after(100,self.poll)
        self.source_changed()
        if not PREVIEW: self.after(1800,lambda:self.check_updates(False))

    def emit(self,kind,data): self.events.put((kind,data))
    def reset_download_rows(self):
        self.download_rows.clear();self.active_download=True;self.download_error='';self.download_table.render()
    def open_tools(self):
        dialog=getattr(self,'tools_dialog',None)
        if dialog is not None and dialog.winfo_exists():dialog.lift();return
        self.tools_dialog=ToolDialog(self)
        self.tools_dialog.after(200,lambda:dark_titlebar(self.tools_dialog))
    def check_tools(self,dialog):
        dialog.checking()
        def work():self.emit('tools_checked',(dialog,check_tool_releases(TOOLS)))
        threading.Thread(target=work,daemon=True).start()
    def install_tools(self,dialog):
        if self.busy:dialog.message.configure(text='Työkalupäivitykset voi asentaa latausten valmistuttua.');return
        selected=dialog.selected()
        if not selected:return
        dialog.check.configure(state='disabled');dialog.install.configure(state='disabled')
        def work():
            try:
                versions=install_tool_releases(selected,TOOLS,self.cancel,lambda text:self.emit('tool_status',(dialog,text)))
                rows=[dict(row) for row in dialog.rows]
                for row in rows:
                    row['current']=versions[row['key']];row['available']=newer(row['latest'],row['current'])
                    row['can_update']=row['available'] and not row['managed'] and not row['error']
                self.emit('tools_updated',(dialog,rows));self.emit('status','Valitut työkalut on päivitetty. Uudelleenkäynnistystä ei tarvita.')
            except Exception as error:
                self.emit('tools_failed',(dialog,str(error)))
                if self.cancel.is_set():self.emit('status','Työkalupäivitys keskeytetty.')
                else:raise
        self.run_job(work)
    def toggle_console(self):
        self.console_visible=not self.console_visible
        if self.console_visible:
            self.log_frame.pack(fill='x'); self.console_button.configure(text='Piilota loki'); self.minsize(1040,900)
        else:
            self.log_frame.pack_forget(); self.console_button.configure(text='Näytä loki'); self.minsize(1040,800)
    def log_line(self,line):
        self.log.configure(state='normal'); self.log.insert('end',line+'\n')
        if int(self.log.index('end-1c').split('.')[0])>500: self.log.delete('1.0','100.0')
        self.log.see('end'); self.log.configure(state='disabled')
    def set_busy(self,value):
        self.busy=value
        for b in [self.link_btn]: b.configure(state='disabled' if value else 'normal')
        self.stop_btn.configure(state='normal' if value else 'disabled')
        self.progress.start(12) if value else self.progress.stop()
        self.source_combo.configure(state='disabled' if value else 'readonly')
        self.parallel_combo.configure(state='disabled' if value else 'readonly')
        apply_theme(self)
        if not value: self.source_changed()
    def source_changed(self):
        spotify=self.source.get()=='Spotify (spotDL)'
        self.source_note.configure(text='Spotify-tiedot, ääni YouTubesta.' if spotify else 'YouTube-videot ja soittolistat.')
        self.link_note.configure(text='Yksi Spotify-linkki riville: artisti, albumi, soittolista tai kappale. Linkit ladataan samassa jonossa.' if spotify else 'Liitä YouTube-linkit yksi linkki riville. Videot ja albumisoittolistat ladataan samassa jonossa.')
        apply_theme(self)
    def source_switched(self):
        self.direct.set('');self.source_changed()
        self.status.set('Liitä valitun palvelun linkit, yksi linkki riville.')
    def run_job(self,fn):
        if self.busy: return
        self.queue_tracker.reset(); self.queue_summary.set('')
        self.cancel.clear(); self.set_busy(True)
        def work():
            try: fn()
            except Exception as e: self.emit('error',str(e))
            finally:
                self.queue_tracker.stop(cancelled=self.cancel.is_set())
                self.emit('done',None)
        threading.Thread(target=work,daemon=True).start()
    def poll(self):
        rows_changed=False
        try:
            while True:
                kind,data=self.events.get_nowait()
                if kind=='log': self.log_line(data)
                elif kind=='status': self.status.set(data)
                elif kind=='download_row': self.download_rows.update(data); rows_changed=True
                elif kind in ('tools_checked','tools_updated'):
                    dialog,rows=data
                    if dialog.winfo_exists():dialog.show_versions(rows)
                elif kind=='tool_status':
                    dialog,text=data;self.status.set(text)
                    if dialog.winfo_exists():dialog.message.configure(text=text)
                elif kind=='tools_failed':
                    dialog,text=data
                    if dialog.winfo_exists():dialog.show_versions(dialog.rows);dialog.message.configure(text=text)
                elif kind=='error':
                    if self.active_download:self.download_error=str(data)
                    self.status.set('Toiminto epäonnistui.'); self.log_line(data); messagebox.showerror('Albumilataaja',data)
                elif kind=='done':
                    if self.active_download:
                        stopped=self.cancel.is_set() or self.youtube_auth_required
                        error='Jono pysäytetty: YouTube pyytää varmistusta.' if self.youtube_auth_required else self.download_error
                        self.download_rows.finish(cancelled=stopped,error=error);rows_changed=True;self.active_download=False
                    self.set_busy(False)
                elif kind=='update': self.offer_update(data)
                elif kind=='current': messagebox.showinfo('Päivitykset','Sovellus on ajan tasalla.')
                elif kind=='exit_for_update': self.save_settings(); self.destroy(); return
                elif kind=='youtube_auth': self.status.set('YouTube pyytää kirjautumista tai varmistusta. Jono pysäytetty.'); messagebox.showwarning('YouTube-kirjautuminen',AUTH_HELP)
        except queue.Empty: pass
        if rows_changed:self.download_table.render()
        snapshot=self.queue_tracker.snapshot()
        if snapshot:
            self.queue_summary.set(snapshot['text']); self.progress.show_fraction(snapshot['fraction'])
        self.after(100,self.poll)
    def catalog_data(self,operation,value,include_singles=True):
        with tempfile.TemporaryDirectory(prefix='Albumilataaja-catalog-') as temporary:
            output=Path(temporary)/'result.json'
            if getattr(sys,'frozen',False):
                worker=TOOLS/'catalog.exe'
                if not worker.exists(): raise RuntimeError('Hakutyökalu puuttuu. Asenna uusin versio uudelleen.')
                args=[str(worker)]
            else: args=[sys.executable,str(Path(__file__).with_name('spotify_catalog.py'))]
            args += [operation,value,str(output)]
            if not include_singles: args+=['--albums-only']
            code=self.execute(args,metadata=True)
            if self.cancel.is_set(): return None
            data=json.loads(output.read_text(encoding='utf-8')) if output.exists() else {}
            if code or data.get('error'): raise RuntimeError(data.get('error') or 'Spotify-haku epäonnistui. Kokeile uudelleen.')
            key='artists' if operation=='search' else 'albums'
            if key not in data: raise RuntimeError('Spotify-haku palautti puutteelliset tiedot.')
            return data
    def choose_folder(self):
        folder=filedialog.askdirectory()
        if folder: self.destination.set(folder)
    def open_folder(self):
        try:
            p=Path(self.destination.get()).expanduser(); p.mkdir(parents=True,exist_ok=True); os.startfile(p)
        except OSError as e: messagebox.showerror('Kansio',str(e))
    def save_settings(self):
        CONFIG.write_text(json.dumps({'destination':self.destination.get(),'format':self.format.get(),'source':self.source.get(),'layout':self.layout.get(),'parallel_downloads':download_workers(self.parallel.get()),'show_console':self.console_visible,'show_details':self.console_visible,'youtube_cookie_file':self.cookie_file.get()},ensure_ascii=False),encoding='utf-8')
    def choose_youtube_cookies(self):
        if self.busy: return
        path=filedialog.askopenfilename(title='Valitse itse viemäsi YouTube cookies.txt',filetypes=[('Netscape-evästeet','*.txt'),('Kaikki tiedostot','*.*')])
        if not path: return
        try: path=validate_cookie_file(path)
        except ValueError as error: messagebox.showerror('YouTube-evästeet',str(error)); return
        self.cookie_file.set(path); self.save_settings(); self.refresh_cookie_label()
        self.status.set('Itse valittu YouTube-istunto otetaan käyttöön seuraavassa latauksessa.')
    def clear_youtube_cookies(self):
        if self.busy: return
        self.cookie_file.set(''); self.save_settings(); self.refresh_cookie_label()
        self.status.set('YouTube-istunnon valinta poistettiin. Alkuperäistä tiedostoa ei poistettu.')
    def refresh_cookie_label(self):
        self.cookie_label.configure(text='YouTube-istunto: valittu tiedosto' if self.cookie_file.get() else 'YouTube-istunto: ei käytössä')
    def selected_cookies(self):
        try: return validate_cookie_file(self.cookie_file.get())
        except ValueError as error: messagebox.showerror('YouTube-evästeet',str(error)); return None
    def download_link(self):
        if self.busy: return
        if self.source.get()=='Spotify (spotDL)':
            self.download_spotify(); return
        try: urls=download_links(self.direct.get(),youtube_url)
        except ValueError as e: messagebox.showerror('Linkit',str(e)); return
        self.start_download([{'url':url} for url in urls],None)
    def download_spotify(self,urls=None):
        if self.busy: return
        try:
            urls=[spotify_url(u) for u in urls] if urls is not None else download_links(self.direct.get(),spotify_url)
            root=Path(self.destination.get()).expanduser().resolve()
        except ValueError as e: messagebox.showerror('Linkki',str(e)); return
        fmt=self.format.get(); layout=self.layout.get(); include_singles=True; workers=download_workers(self.parallel.get()); self.save_settings()
        cookie_file=self.selected_cookies()
        if cookie_file is None: return
        self.reset_download_rows()
        def work():
            root.mkdir(parents=True,exist_ok=True)
            for name in ['spotdl.exe','yt-dlp.exe','ffmpeg.exe','ffprobe.exe','deno.exe']:
                if not (TOOLS/name).exists(): raise RuntimeError('Puuttuva tiedosto: '+name+'. Asenna sovellus uudelleen.')
            self.emit('status','spotDL hakee kappaleet ja lataa ne albumikansioihin…')
            queue_urls=[]
            for url in urls:
                if re.search(r'/(?:intl-[a-z]+/)?artist/',urlparse(url).path):
                    found=self.catalog_data('search',url)
                    if found is None: return
                    if not found['artists']: raise RuntimeError('Spotify-artistia ei löytynyt.')
                    artist=found['artists'][0]
                    catalog=self.catalog_data('albums',artist['spotify_id'],include_singles)
                    if catalog is None: return
                    queue_urls.extend(a['spotify_url'] for a in newest_first(catalog['albums']))
                else: queue_urls.append(url)
            if not queue_urls: raise RuntimeError('Ladattavia Spotify-julkaisuja ei löytynyt.')
            if workers>1:
                self.queue_tracker.begin(1)
                self.emit('status',f'Spotify: enintään {workers} samanaikaista latausta…')
                result=self.execute(spot_command(list(dict.fromkeys(queue_urls)),root,fmt,layout,cookie_file,workers),tracking=True)
                if self.youtube_auth_required: self.emit('youtube_auth',None); return
                if not self.cancel.is_set():
                    errors=bool(result) or self.download_errors
                    if self.queue_tracker.unit!='tiedostoa': self.queue_tracker.finish_task(0,failed=errors)
                    self.emit('status','Spotify-latauksissa oli virheitä. Katso loki.' if errors else 'Spotify-lataukset valmiit. Musiikki on tallennuskansiossa.')
                else: self.emit('status','Keskeytetty. Valmiit kappaleet säilyvät.')
                return
            self.queue_tracker.begin(len(queue_urls))
            errors=False
            for i,url in enumerate(queue_urls,1):
                if self.cancel.is_set(): break
                self.queue_tracker.start_task(i-1)
                self.emit('status',f'spotDL: {i}/{len(queue_urls)} • haetaan ja ladataan kappaleita…')
                result=self.execute(spot_command(url,root,fmt,layout,cookie_file,workers),tracking=True)
                if self.youtube_auth_required:
                    self.emit('youtube_auth',None); return
                errors=errors or bool(result) or self.download_errors
                if not self.cancel.is_set(): self.queue_tracker.finish_task(i-1,failed=bool(result) or self.download_errors)
            if self.cancel.is_set(): self.emit('status','Keskeytetty. Valmiit kappaleet säilyvät.')
            elif errors: self.emit('status','spotDL ilmoitti virheistä. Katso loki ja yritä tarvittaessa uudelleen.')
            else: self.emit('status','spotDL-lataus valmis. Tarkista tallennuskansio.')
        self.run_job(work)
    def start_download(self,items,artist):
        if self.busy: return
        names=['yt-dlp.exe','ffmpeg.exe','ffprobe.exe','deno.exe']+(['youtube-parallel.exe'] if getattr(sys,'frozen',False) else [])
        missing=[name for name in names if not (TOOLS/name).exists()]
        if missing: messagebox.showerror('Puuttuvia tiedostoja','Asenna sovellus uudelleen: '+', '.join(missing)); return
        root=Path(self.destination.get()).expanduser().resolve(); fmt=self.format.get(); layout=self.layout.get(); workers=download_workers(self.parallel.get()); self.save_settings()
        cookie_file=self.selected_cookies()
        if cookie_file is None: return
        self.reset_download_rows()
        def work():
            failures=0; jobs=[]
            for number,item in enumerate(items,1):
                if self.cancel.is_set(): break
                try:
                    url=youtube_url(item['url']); info=self.inspect_url(url,cookie_file)
                    name=info.get('title') or 'YouTube'; owner=info.get('artist') or info.get('uploader') or info.get('channel') or 'YouTube'
                    year=info.get('release_year') or info.get('release_date')
                    entries=info.get('entries') or []
                    if not year and entries:year=(entries[0] or {}).get('release_year') or (entries[0] or {}).get('release_date')
                    folder=download_folder(root,owner,name,year,layout); folder.mkdir(parents=True,exist_ok=True)
                    jobs.append({'command':command(url,folder,fmt),'album':name,'artist':owner or ''})
                    self.emit('status',f'Valmistellaan latausjonoa: {number}/{len(items)} • {name}')
                except Exception as e:
                    self.emit('download_row',{'id':f'youtube:prepare:{number}','title':item.get('title') or item.get('url') or 'Julkaisu','source':'YouTube','stage':'error','error':str(e)})
                    if self.youtube_auth_required:
                        self.emit('youtube_auth',None); return
                    if not self.cancel.is_set(): failures+=1; self.emit('log',str(e))
            if jobs and not self.cancel.is_set():
                self.queue_tracker.begin(1)
                with tempfile.TemporaryDirectory(prefix='Albumilataaja-queue-') as temporary:
                    manifest=Path(temporary)/'queue.json'; manifest.write_text(json.dumps(jobs),encoding='utf-8')
                    worker=TOOLS/'youtube-parallel.exe'
                    args=[str(worker)] if getattr(sys,'frozen',False) else [sys.executable,str(Path(__file__).with_name('youtube_parallel.py'))]
                    args += [str(manifest),'--workers',str(workers)]
                    if cookie_file: args+=['--cookies',cookie_file]
                    self.emit('status',f'YouTube: enintään {workers} samanaikaista latausta…')
                    code=self.execute(args,tracking=True)
                    if self.youtube_auth_required: self.emit('youtube_auth',None); return
                    if code or self.download_errors: failures+=1
            self.emit('status','Keskeytetty. Valmiit kappaleet säilyvät.' if self.cancel.is_set() else ('Latausjonossa oli virheitä — katso loki.' if failures else 'Valmis. Musiikki on tallennuskansiossa.'))
        self.run_job(work)
    def execute(self,args,capture=False,metadata=False,tracking=False):
        if self.cancel.is_set(): return '' if capture else 1
        with tempfile.TemporaryDirectory(prefix='Albumilataaja-job-') as workspace, isolated_cookie_arguments(args,workspace) as args:
            self.download_errors=False
            self.youtube_auth_required=False
            env=os.environ.copy(); env['PATH']=str(TOOLS)+os.pathsep+env.get('PATH',''); env['PYTHONIOENCODING']='utf-8'; env['NO_COLOR']='1'
            env['ALBUMILATAAJA_WORKSPACE']=workspace
            p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE if capture else subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',creationflags=NO_WINDOW,env=env,cwd=STATE)
            self.proc=p
            finished=threading.Event(); timed_out=threading.Event()
            if capture or metadata or 'save' in args[1:2]:
                def watchdog():
                    if not finished.wait(180) and p.poll() is None:
                        timed_out.set()
                        subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,creationflags=NO_WINDOW)
                threading.Thread(target=watchdog,daemon=True).start()
            try:
                if self.cancel.is_set(): p.terminate()
                if capture:
                    out,err=p.communicate()
                    if requires_youtube_auth(err): self.youtube_auth_required=True; raise RuntimeError('YouTube pyytää kirjautumista tai varmistusta.')
                    if timed_out.is_set(): raise RuntimeError('Linkin lukeminen aikakatkaistiin. Kokeile uudelleen.')
                    if p.returncode: raise RuntimeError(err[-1800:] or 'Linkin lukeminen epäonnistui.')
                    return out
                for line in p.stdout:
                    line=line.strip()
                    row=parse_row(line)
                    if row is not None:
                        if row:
                            self.emit('download_row',row)
                            if row.get('stage')=='error':self.download_errors=True
                        continue
                    if requires_youtube_auth(line):
                        self.youtube_auth_required=True; self.download_errors=True
                        self.emit('log','YouTube pyytää kirjautumista tai manuaalista varmistusta. Jono pysäytettiin.')
                        subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,creationflags=NO_WINDOW)
                        break
                    if re.search(r'\b(error|failed|exception)\b|\b\w*(?:Error|Exception):',line,re.I): self.download_errors=True
                    internal_progress=tracking and self.queue_tracker.consume(line)
                    if line and not internal_progress: self.emit('log',line)
                    if self.cancel.is_set(): break
                code=p.wait()
                if timed_out.is_set(): raise RuntimeError('Spotify-julkaisujen haku aikakatkaistiin. Voit kokeilla albumin suoraa linkkiä.')
                return code
            finally: finished.set(); self.proc=None
    def inspect_url(self,url,cookie_file=''):
        args=[str(TOOLS/'yt-dlp.exe'),'--ignore-config','--flat-playlist','--playlist-items','1','--dump-single-json','--socket-timeout','25','--',url]
        if cookie_file: args[1:1]=['--cookies',validate_cookie_file(cookie_file)]
        return json.loads(self.execute(args,True))
    def stop(self):
        self.cancel.set()
        p=self.proc
        if p and p.poll() is None:
            subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,creationflags=NO_WINDOW)
        self.status.set('Keskeytetään…')
    def close(self):
        if self.busy and not messagebox.askyesno('Sulje','Keskeytetäänkö toiminto ja suljetaan sovellus?'): return
        self.stop(); self.save_settings(); self.destroy()
    def check_updates(self,manual):
        if PREVIEW:
            if manual: messagebox.showinfo('Esikatselu','Tämä ulkoasu on paikallinen esikatselu. Sitä ei ole julkaistu päivityksenä.')
            return
        def work():
            try:
                r=requests.get(f'https://api.github.com/repos/{REPOSITORY}/releases/latest',timeout=20); r.raise_for_status(); release=r.json()
                if version_tuple(release['tag_name'])>version_tuple(VERSION): self.emit('update',release)
                elif manual: self.emit('current',None)
            except Exception as e:
                if manual: self.emit('error','Päivitysten tarkistus epäonnistui: '+str(e))
        threading.Thread(target=work,daemon=True).start()
    def offer_update(self,release):
        if self.busy: self.log_line('Uusi päivitys on saatavilla. Tarkista päivitykset latausten jälkeen.'); return
        if not messagebox.askyesno('Päivitys saatavilla','Uusi päivitys on saatavilla. Päivitetäänkö nyt automaattisesti?\n\nKyllä = päivitä ja käynnistä uudelleen.\nEi = jatka nykyisellä sovelluksella.'): return
        def work():
            assets={a['name']:a for a in release.get('assets',[])}
            installer=assets.get('Albumilataaja-Setup.exe'); checks=assets.get('SHA256SUMS.txt')
            if not installer or not checks: raise ValueError('Julkaisusta puuttuu asentaja tai tarkistussumma.')
            prefix=f'https://github.com/{REPOSITORY}/releases/download/'
            if not all(a['browser_download_url'].startswith(prefix) for a in [installer,checks]): raise ValueError('Virheellinen päivitysosoite.')
            r=requests.get(checks['browser_download_url'],timeout=25); r.raise_for_status()
            expected=next((line.split()[0] for line in r.text.splitlines() if line.split() and line.split()[-1]=='Albumilataaja-Setup.exe'),None)
            if not expected or not re.fullmatch('[0-9a-fA-F]{64}',expected): raise ValueError('Tarkistussumma puuttuu.')
            dest=Path(tempfile.mkdtemp(prefix='Albumilataaja-update-'))/'Albumilataaja-Setup.exe'; h=hashlib.sha256()
            self.emit('status','Ladataan päivitystä…')
            with requests.get(installer['browser_download_url'],stream=True,timeout=60) as response:
                response.raise_for_status()
                with dest.open('wb') as f:
                    for block in response.iter_content(1024*1024):
                        if self.cancel.is_set(): raise RuntimeError('Päivityksen lataus keskeytetty.')
                        if block: f.write(block); h.update(block)
            if h.hexdigest()!=expected.lower(): dest.unlink(); raise ValueError('Päivityksen tarkistussumma ei täsmää.')
            update_environment=os.environ.copy()
            update_environment['PYINSTALLER_RESET_ENVIRONMENT']='1'
            subprocess.Popen([str(dest),'/SILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/CLOSEAPPLICATIONS','/UPDATEAPP=1','/DIR='+str(BASE)],creationflags=NO_WINDOW,env=update_environment)
            self.emit('exit_for_update',None)
        self.run_job(work)

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--runtime-self-test':
        runtime=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
        Path(sys.argv[2]).write_text(json.dumps({'version':VERSION,'runtime_directory':str(runtime),'python_dll_present':(runtime/'python314.dll').is_file()}),encoding='utf-8')
    else: App().mainloop()
