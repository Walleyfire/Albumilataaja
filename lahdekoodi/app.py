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
from tkinter import ttk, filedialog, messagebox
from urllib.parse import urlparse
import webbrowser
import requests
from ytmusicapi import YTMusic

VERSION = '1.0.0'
REPOSITORY = 'Walleyfire/Albumilataaja'
BASE = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
TOOLS = BASE / 'tools'
STATE = Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'Albumilataaja'
STATE.mkdir(parents=True, exist_ok=True)
CONFIG = STATE / 'settings.json'
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

def newest_first(albums):
    return sorted(albums,key=lambda a:(-(int(release_year(a.get('year'))) if release_year(a.get('year')) else 0),a.get('title','').casefold()))

def youtube_url(value):
    p = urlparse(value)
    if p.scheme != 'https' or p.hostname not in ('youtube.com','www.youtube.com','music.youtube.com','youtu.be'):
        raise ValueError('Liitä https-alkuinen YouTube-linkki.')
    return value

def version_tuple(value):
    if not re.fullmatch(r'v?\d+\.\d+\.\d+', value):
        raise ValueError('Virheellinen versionumero')
    return tuple(map(int, value.lstrip('v').split('.')))

def spotify_url(value):
    p = urlparse(value)
    if p.scheme != 'https' or p.hostname != 'open.spotify.com' or not re.fullmatch(r'/(?:intl-[a-z]+/)?(?:artist|album|playlist|track)/[A-Za-z0-9]+', p.path.rstrip('/')):
        raise ValueError('Liitä Spotify-artistin, albumin, soittolistan tai kappaleen https://open.spotify.com/…-linkki.')
    return value

def spot_command(url, root, fmt,layout='Vuosi - Albumi'):
    album='{album}, {year}' if layout=='Albumi, Vuosi' else '{year} - {album}'
    return [str(TOOLS/'spotdl.exe'), 'download', spotify_url(url), '--headless',
            '--ffmpeg', str(TOOLS/'ffmpeg.exe'), '--format', fmt, '--threads', '2',
            '--output', str(root/'{album-artist}'/album/'{disc-number}-{track-number} - {title}.{output-ext}'),
            '--overwrite', 'skip', '--archive', str(root/('.spotdl-archive-'+fmt+'.txt')),
            '--simple-tui', '--print-errors', '--max-retries', '3',
            '--max-filename-length', '170', '--yt-dlp-args',
            '--js-runtimes '+json.dumps('deno:'+str(TOOLS/'deno.exe'))]

def command(url, folder, fmt):
    return [str(TOOLS/'yt-dlp.exe'), '--ignore-config', '--no-color', '--newline',
            '--js-runtimes', 'deno:'+str(TOOLS/'deno.exe'), '--ffmpeg-location', str(TOOLS),
            '--windows-filenames', '--trim-filenames', '170', '--socket-timeout', '25',
            '--retries', '3', '--no-overwrites', '--yes-playlist', '-f', 'bestaudio/best',
            '-x', '--audio-format', fmt, '--embed-metadata',
            '--download-archive', str(folder/('.archive-'+fmt+'.txt')),
            '-P', str(folder), '-o', '%(playlist_index|1)02d - %(title).140s [%(id)s].%(ext)s', '--', youtube_url(url)]

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        icon=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))/'app.ico'
        if icon.exists(): self.iconbitmap(str(icon))
        self.title('Albumilataaja'); self.geometry('1060x900'); self.minsize(920,800)
        self.configure(bg='#101827')
        self.events = queue.Queue(); self.proc = None; self.busy = False
        self.cancel = threading.Event(); self.artists = []; self.albums = []; self.artist = ''; self.album_source = ''
        try: settings = json.loads(CONFIG.read_text(encoding='utf-8'))
        except (OSError, ValueError): settings = {}
        self.destination = tk.StringVar(value=settings.get('destination',str(Path.home()/'Music'/'Albumilataaja')))
        self.query = tk.StringVar(); self.artist_choice = tk.StringVar(); self.direct = tk.StringVar()
        self.format = tk.StringVar(value=settings.get('format','flac')); self.singles = tk.BooleanVar(value=True)
        self.source = tk.StringVar(value=settings.get('source','YouTube'))
        self.layout = tk.StringVar(value=settings.get('layout','Albumi, Vuosi'))
        self.status = tk.StringVar(value='Hae artisti tai liitä YouTube-soittolistan linkki.')
        s=ttk.Style(self); s.theme_use('clam')
        s.configure('.', font=('Segoe UI',10), background='#101827', foreground='#e5eaf3')
        s.configure('TButton', padding=(12,8), background='#263c57', foreground='white')
        s.map('TButton',background=[('active','#385978'),('disabled','#202a38')])
        s.configure('TEntry',fieldbackground='#f3f6fb',foreground='#172133',padding=7)
        s.configure('TCombobox',fieldbackground='#f3f6fb',foreground='#172133',padding=6)
        s.configure('Treeview',fieldbackground='#192638', background='#192638',foreground='#edf3fb',rowheight=29)
        s.configure('Treeview.Heading',background='#263c57',foreground='white',padding=7)
        s.map('Treeview',background=[('selected','#286785')])
        outer=ttk.Frame(self,padding=24); outer.pack(fill='both',expand=True)
        top=ttk.Frame(outer); top.pack(fill='x')
        ttk.Label(top,text='ALBUMILATAAJA',font=('Segoe UI',22,'bold')).pack(side='left')
        ttk.Button(top,text='Tarkista päivitykset',command=lambda:self.check_updates(True)).pack(side='right')
        ttk.Label(outer,text='Oma musiikkikirjasto',foreground='#9bacbf').pack(anchor='w',pady=(2,12))
        sources=ttk.Frame(outer); sources.pack(fill='x',pady=(0,10))
        ttk.Label(sources,text='Latauslähde  ').pack(side='left')
        self.source_combo=ttk.Combobox(sources,textvariable=self.source,values=['YouTube','Spotify (spotDL)'],state='readonly',width=22)
        self.source_combo.pack(side='left'); self.source_combo.bind('<<ComboboxSelected>>',lambda e:self.source_switched())
        self.source_note=ttk.Label(sources,text='',foreground='#9bacbf'); self.source_note.pack(side='left',padx=12)
        search=ttk.Frame(outer); search.pack(fill='x')
        entry=ttk.Entry(search,textvariable=self.query); entry.pack(side='left',fill='x',expand=True); entry.bind('<Return>',lambda e:self.search())
        self.search_btn=ttk.Button(search,text='Hae artisti',command=self.search); self.search_btn.pack(side='left',padx=(8,0))
        choose=ttk.Frame(outer); choose.pack(fill='x',pady=8)
        self.combo=ttk.Combobox(choose,textvariable=self.artist_choice,state='readonly',width=35); self.combo.pack(side='left',fill='x',expand=True)
        ttk.Checkbutton(choose,text='Myös singlet ja EP:t',variable=self.singles).pack(side='left',padx=12)
        self.album_btn=ttk.Button(choose,text='Näytä julkaisut',command=self.load_albums); self.album_btn.pack(side='left')
        bar=ttk.Frame(outer); bar.pack(fill='x',pady=(10,5))
        ttk.Label(bar,text='JULKAISUT',font=('Segoe UI',11,'bold')).pack(side='left')
        ttk.Button(bar,text='Valitse kaikki',command=lambda:self.tree.selection_set(self.tree.get_children())).pack(side='right')
        tree_frame=ttk.Frame(outer); tree_frame.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(tree_frame,columns=('title','year','kind'),show='headings',selectmode='extended',height=4)
        for key,label,width in [('title','Albumi / julkaisu',570),('year','Vuosi',80),('kind','Tyyppi',120)]:
            self.tree.heading(key,text=label); self.tree.column(key,width=width)
        self.tree.pack(side='left',fill='both',expand=True)
        scrollbar=ttk.Scrollbar(tree_frame,orient='vertical',command=self.tree.yview); scrollbar.pack(side='right',fill='y')
        self.tree.configure(yscrollcommand=scrollbar.set)
        ttk.Label(outer,text='Uusimmat ensin • valitse kansiomuoto alhaalta. Ctrl ja Shift toimivat monivalinnassa.',foreground='#9bacbf').pack(anchor='w',pady=(4,8))
        link=ttk.Frame(outer); link.pack(fill='x')
        ttk.Entry(link,textvariable=self.direct).pack(side='left',fill='x',expand=True)
        self.link_btn=ttk.Button(link,text='Lataa linkistä',command=self.download_link); self.link_btn.pack(side='left',padx=(8,0))
        self.link_note=ttk.Label(outer,text='',foreground='#9bacbf'); self.link_note.pack(anchor='w',pady=(3,10))
        path=ttk.Frame(outer); path.pack(fill='x')
        ttk.Label(path,text='Tallennuskansio  ').pack(side='left')
        ttk.Entry(path,textvariable=self.destination).pack(side='left',fill='x',expand=True)
        ttk.Button(path,text='Valitse…',command=self.choose_folder).pack(side='left',padx=6)
        ttk.Button(path,text='Avaa kansio',command=self.open_folder).pack(side='left')
        actions=ttk.Frame(outer); actions.pack(fill='x',pady=12)
        ttk.Label(actions,text='Muoto  ').pack(side='left')
        ttk.Combobox(actions,textvariable=self.format,values=['flac','opus','mp3','m4a'],state='readonly',width=7).pack(side='left')
        ttk.Label(actions,text='   Kansiomuoto  ').pack(side='left')
        ttk.Combobox(actions,textvariable=self.layout,values=['Albumi, Vuosi','Vuosi - Albumi'],state='readonly',width=17).pack(side='left')
        self.download_btn=ttk.Button(actions,text='Lataa valitut julkaisut',command=self.download_selected); self.download_btn.pack(side='left',padx=12)
        self.stop_btn=ttk.Button(actions,text='Keskeytä',command=self.stop,state='disabled'); self.stop_btn.pack(side='left')
        ttk.Label(outer,text='FLAC-tallennus ei paranna YouTuben alkuperäistä äänenlaatua.',foreground='#9bacbf').pack(anchor='w')
        self.progress=ttk.Progressbar(outer,mode='indeterminate'); self.progress.pack(fill='x',pady=8)
        ttk.Label(outer,textvariable=self.status,wraplength=960).pack(anchor='w')
        self.log=tk.Text(outer,height=4,bg='#0b1220',fg='#a8bfd6',font=('Consolas',9),relief='flat',state='disabled'); self.log.pack(fill='x',pady=(8,0))
        self.protocol('WM_DELETE_WINDOW',self.close); self.after(100,self.poll)
        self.source_changed()
        self.after(1800,lambda:self.check_updates(False))

    def emit(self,kind,data): self.events.put((kind,data))
    def log_line(self,line):
        self.log.configure(state='normal'); self.log.insert('end',line+'\n')
        if int(self.log.index('end-1c').split('.')[0])>500: self.log.delete('1.0','100.0')
        self.log.see('end'); self.log.configure(state='disabled')
    def set_busy(self,value):
        self.busy=value
        for b in [self.search_btn,self.album_btn,self.download_btn,self.link_btn]: b.configure(state='disabled' if value else 'normal')
        self.stop_btn.configure(state='normal' if value else 'disabled')
        self.progress.start(12) if value else self.progress.stop()
        self.source_combo.configure(state='disabled' if value else 'readonly')
        if not value: self.source_changed()
    def source_changed(self):
        spotify=self.source.get()=='Spotify (spotDL)'
        self.source_note.configure(text='Spotify-tiedot, ääni YouTubesta.' if spotify else 'Artistihaku ja albumit YouTube Musicista.')
        self.link_note.configure(text='Liitä Spotify-artistin linkki ladataksesi tuotannon albumeittain. Myös albumi, soittolista ja kappale käyvät.' if spotify else 'Liitä YouTube-videon tai albumisoittolistan https-linkki.')
        self.search_btn.configure(text='Hae Spotify-julkaisut' if spotify else 'Hae artisti')
        self.album_btn.configure(state='disabled' if spotify else 'normal')
        self.download_btn.configure(state='normal' if self.album_source==self.source.get() and self.albums else 'disabled')
        self.combo.configure(state='disabled' if spotify else 'readonly')
    def source_switched(self):
        self.artists=[]; self.albums=[]; self.album_source=''; self.artist_choice.set(''); self.combo['values']=[]
        self.tree.delete(*self.tree.get_children()); self.direct.set(''); self.source_changed()
        self.status.set('Kirjoita artistin nimi tai liitä valitun palvelun linkki.')
    def run_job(self,fn):
        if self.busy: return
        self.cancel.clear(); self.set_busy(True)
        def work():
            try: fn()
            except Exception as e: self.emit('error',str(e))
            finally: self.emit('done',None)
        threading.Thread(target=work,daemon=True).start()
    def poll(self):
        try:
            while True:
                kind,data=self.events.get_nowait()
                if kind=='log': self.log_line(data)
                elif kind=='status': self.status.set(data)
                elif kind=='error': self.status.set('Toiminto epäonnistui.'); self.log_line(data); messagebox.showerror('Albumilataaja',data)
                elif kind=='done': self.set_busy(False)
                elif kind=='artists':
                    self.artists=data; self.combo['values']=[a['artist'] for a in data]
                    if data: self.combo.current(0); self.status.set('Valitse oikea artisti ja paina Näytä julkaisut.')
                    else: self.status.set('Artisteja ei löytynyt.')
                elif kind=='albums':
                    self.artist,albums=data; self.albums=newest_first(albums); self.album_source=self.source.get(); self.tree.delete(*self.tree.get_children())
                    for i,a in enumerate(self.albums): self.tree.insert('', 'end',iid=str(i),values=(a['title'],a.get('year',''),a['kind']))
                    self.artist_choice.set(self.artist)
                    self.status.set(f'{self.artist}: {len(self.albums)} julkaisua. Valitse haluamasi tai Valitse kaikki.')
                elif kind=='update': self.offer_update(data)
                elif kind=='current': messagebox.showinfo('Päivitykset','Käytössä on uusin versio ('+VERSION+').')
        except queue.Empty: pass
        self.after(100,self.poll)
    def search(self):
        query=self.query.get().strip()
        if not query: return
        if self.source.get()=='Spotify (spotDL)':
            self.search_spotify(query); return
        self.status.set('Haetaan artisteja…')
        self.run_job(lambda:self.emit('artists',YTMusic(requests_session=requests.Session()).search(query,filter='artists',limit=12)))
    def search_spotify(self,query):
        include=self.singles.get()
        if query.startswith('https://'):
            try: query=spotify_url(query)
            except ValueError as e: messagebox.showerror('Spotify-linkki',str(e)); return
        else: query='artist:'+query
        self.status.set('Haetaan Spotify-artistin julkaisutietoja. Suuri tuotanto voi kestää hetken…')
        def work():
            with tempfile.TemporaryDirectory(prefix='Albumilataaja-search-') as temporary:
                output=Path(temporary)/'artist.spotdl'
                args=[str(TOOLS/'spotdl.exe'),'save',query,'--save-file',str(output),'--headless','--simple-tui','--max-retries','2','--ffmpeg',str(TOOLS/'ffmpeg.exe')]
                code=self.execute(args)
                if self.cancel.is_set(): return
                if code or not output.exists(): raise RuntimeError('Spotify-haku epäonnistui. Katso loki tai kokeile suoraa Spotify-linkkiä.')
                songs=json.loads(output.read_text(encoding='utf-8')); albums={}
                for song in songs:
                    if not include and song.get('album_type')=='single': continue
                    key=song.get('album_id')
                    if key and key not in albums:
                        albums[key]={'title':song.get('album_name','Albumi'),'year':song.get('year',''),'kind':song.get('album_type','Albumi'), 'spotify_url':'https://open.spotify.com/album/'+key}
                name=(songs[0].get('list_name') or songs[0].get('artist') or query) if songs else query
                self.emit('albums',(name,list(albums.values())))
        self.run_job(work)
    def load_albums(self):
        index=self.combo.current()
        if index<0: return
        chosen=self.artists[index]; include=self.singles.get()
        self.status.set('Haetaan artistin julkaisuja…')
        def work():
            y=YTMusic(); artist=y.get_artist(chosen['browseId']); albums=[]; seen=set()
            for section,kind in [('albums','Albumi')]+([('singles','Single / EP')] if include else []):
                group=artist.get(section) or {}; entries=group.get('results',[])
                if group.get('params'): entries=y.get_artist_albums(group.get('browseId') or chosen['browseId'],group['params'],limit=None)
                for a in entries:
                    if self.cancel.is_set(): return
                    key=a.get('browseId') or a.get('audioPlaylistId')
                    if key and key not in seen: seen.add(key); albums.append(dict(a,kind=kind))
            self.emit('albums',(artist.get('name',chosen['artist']),albums))
        self.run_job(work)
    def choose_folder(self):
        folder=filedialog.askdirectory()
        if folder: self.destination.set(folder)
    def open_folder(self):
        try:
            p=Path(self.destination.get()).expanduser(); p.mkdir(parents=True,exist_ok=True); os.startfile(p)
        except OSError as e: messagebox.showerror('Kansio',str(e))
    def save_settings(self):
        CONFIG.write_text(json.dumps({'destination':self.destination.get(),'format':self.format.get(),'source':self.source.get(),'layout':self.layout.get()},ensure_ascii=False),encoding='utf-8')
    def download_selected(self):
        items=[dict(self.albums[int(i)]) for i in self.tree.selection()]
        if not items: messagebox.showinfo('Valitse julkaisut','Valitse ensin vähintään yksi julkaisu.'); return
        if self.source.get()=='Spotify (spotDL)': self.download_spotify([a['spotify_url'] for a in items])
        else: self.start_download(items,self.artist)
    def download_link(self):
        if self.source.get()=='Spotify (spotDL)':
            self.download_spotify(); return
        try: url=youtube_url(self.direct.get().strip())
        except ValueError as e: messagebox.showerror('Linkki',str(e)); return
        self.start_download([{'url':url}],None)
    def download_spotify(self,urls=None):
        if self.busy: return
        try:
            urls=[spotify_url(u) for u in urls] if urls else [spotify_url(self.direct.get().strip())]
            root=Path(self.destination.get()).expanduser().resolve()
        except ValueError as e: messagebox.showerror('Linkki',str(e)); return
        fmt=self.format.get(); layout=self.layout.get(); self.save_settings()
        def work():
            root.mkdir(parents=True,exist_ok=True)
            for name in ['spotdl.exe','ffmpeg.exe','ffprobe.exe','deno.exe']:
                if not (TOOLS/name).exists(): raise RuntimeError('Puuttuva tiedosto: '+name+'. Asenna sovellus uudelleen.')
            self.emit('status','spotDL hakee kappaleet ja lataa ne albumikansioihin…')
            errors=False
            for i,url in enumerate(urls,1):
                if self.cancel.is_set(): break
                self.emit('status',f'spotDL: {i}/{len(urls)} • haetaan ja ladataan kappaleita…')
                result=self.execute(spot_command(url,root,fmt,layout))
                errors=errors or bool(result) or self.download_errors
            if self.cancel.is_set(): self.emit('status','Keskeytetty. Valmiit kappaleet säilyvät.')
            elif errors: self.emit('status','spotDL ilmoitti virheistä. Katso loki ja yritä tarvittaessa uudelleen.')
            else: self.emit('status','spotDL-lataus valmis. Tarkista tallennuskansio.')
        self.run_job(work)
    def start_download(self,items,artist):
        if self.busy: return
        missing=[name for name in ['yt-dlp.exe','ffmpeg.exe','ffprobe.exe','deno.exe'] if not (TOOLS/name).exists()]
        if missing: messagebox.showerror('Puuttuvia tiedostoja','Asenna sovellus uudelleen: '+', '.join(missing)); return
        root=Path(self.destination.get()).expanduser().resolve(); fmt=self.format.get(); layout=self.layout.get(); self.save_settings()
        def work():
            y=YTMusic(); failures=0
            for number,item in enumerate(items,1):
                if self.cancel.is_set(): break
                try:
                    if item.get('url'):
                        url=item['url']; info=self.inspect_url(url)
                        name=info.get('title') or 'YouTube'; owner=info.get('artist') or info.get('uploader') or info.get('channel') or 'YouTube'
                        year=info.get('release_year') or info.get('release_date')
                        entries=info.get('entries') or []
                        if not year and entries: year=(entries[0] or {}).get('release_year') or (entries[0] or {}).get('release_date')
                    else:
                        details=y.get_album(item['browseId']) if not item.get('audioPlaylistId') else item
                        playlist=details.get('audioPlaylistId')
                        if not playlist: raise ValueError('Albumin soittolistaa ei löytynyt: '+item['title'])
                        url='https://www.youtube.com/playlist?list='+playlist
                        name=item['title']; owner=artist; year=item.get('year') or details.get('year')
                    folder=root/safe_name(owner)/album_folder(name,year,layout); folder.mkdir(parents=True,exist_ok=True)
                    self.emit('status',f'{number}/{len(items)} • {name}'); self.emit('log','Ladataan: '+str(folder))
                    code=self.execute(command(url,folder,fmt))
                    if code and not self.cancel.is_set(): failures+=1; self.emit('log','Julkaisuun jäi virheitä. Tarkista yllä olevat tiedot ja yritä uudelleen.')
                except Exception as e:
                    if not self.cancel.is_set(): failures+=1; self.emit('log',str(e))
            self.emit('status','Keskeytetty. Valmiit kappaleet säilyvät.' if self.cancel.is_set() else (f'Valmis. Virheitä {failures} julkaisussa — katso loki.' if failures else 'Valmis. Musiikki on tallennuskansiossa.'))
        self.run_job(work)
    def execute(self,args,capture=False):
        if self.cancel.is_set(): return '' if capture else 1
        self.download_errors=False
        env=os.environ.copy(); env['PATH']=str(TOOLS)+os.pathsep+env.get('PATH',''); env['PYTHONIOENCODING']='utf-8'; env['NO_COLOR']='1'
        p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE if capture else subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',creationflags=NO_WINDOW,env=env,cwd=STATE)
        self.proc=p
        finished=threading.Event(); timed_out=threading.Event()
        if capture or 'save' in args[1:2]:
            def watchdog():
                if not finished.wait(180) and p.poll() is None:
                    timed_out.set()
                    subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,creationflags=NO_WINDOW)
            threading.Thread(target=watchdog,daemon=True).start()
        try:
            if self.cancel.is_set(): p.terminate()
            if capture:
                out,err=p.communicate()
                if timed_out.is_set(): raise RuntimeError('Linkin lukeminen aikakatkaistiin. Kokeile uudelleen.')
                if p.returncode: raise RuntimeError(err[-1800:] or 'Linkin lukeminen epäonnistui.')
                return out
            for line in p.stdout:
                line=line.strip()
                if re.search(r'\b(error|failed|exception)\b',line,re.I): self.download_errors=True
                if line: self.emit('log',line)
                if self.cancel.is_set(): break
            code=p.wait()
            if timed_out.is_set(): raise RuntimeError('Spotify-julkaisujen haku aikakatkaistiin. Voit kokeilla albumin suoraa linkkiä.')
            return code
        finally: finished.set(); self.proc=None
    def inspect_url(self,url):
        args=[str(TOOLS/'yt-dlp.exe'),'--ignore-config','--flat-playlist','--playlist-items','1','--dump-single-json','--socket-timeout','25','--',url]
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
        def work():
            try:
                r=requests.get(f'https://api.github.com/repos/{REPOSITORY}/releases/latest',timeout=20); r.raise_for_status(); release=r.json()
                if version_tuple(release['tag_name'])>version_tuple(VERSION): self.emit('update',release)
                elif manual: self.emit('current',None)
            except Exception as e:
                if manual: self.emit('error','Päivitysten tarkistus epäonnistui: '+str(e))
        threading.Thread(target=work,daemon=True).start()
    def offer_update(self,release):
        if self.busy: self.log_line('Uusi versio saatavilla: '+release['tag_name']+'. Tarkista päivitykset latausten jälkeen.'); return
        if not messagebox.askyesno('Päivitys saatavilla',f"Versio {release['tag_name']} on saatavilla. Ladataanko ja avataanko asentaja?"): return
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
            os.startfile(dest); self.emit('status','Asentaja avattu. Se päivittää nykyisen asennuksen.')
        self.run_job(work)

if __name__=='__main__':
    App().mainloop()
