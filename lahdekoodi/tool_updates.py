"""Verified, transactional updates from the tools' official GitHub releases."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile
import requests

SPECS={
    'yt-dlp':{'name':'yt-dlp','repo':'yt-dlp/yt-dlp','asset':r'yt-dlp\.exe','files':['yt-dlp.exe']},
    'deno':{'name':'Deno','repo':'denoland/deno','asset':r'deno-x86_64-pc-windows-msvc\.zip','files':['deno.exe']},
    'ffmpeg':{'name':'FFmpeg / ffprobe','repo':'yt-dlp/FFmpeg-Builds','asset':r'ffmpeg-N-.+-win64-gpl\.zip','files':['ffmpeg.exe','ffprobe.exe']},
    'spotdl':{'name':'SpotDL','repo':'spotDL/spotify-downloader','managed':True},
}
FALLBACK={'yt-dlp':'2026.10.26','deno':'v2.9.8','ffmpeg':'autobuild-2026-11-09-23-32','spotdl':'v4.6.0'}
VERSION_FILE='tools-versions.json'


def load_versions(folder):
    versions=dict(FALLBACK)
    try:
        data=json.loads((Path(folder)/VERSION_FILE).read_text(encoding='utf-8'))
        versions.update({key:value for key,value in data.items() if key in SPECS and isinstance(value,str)})
    except (OSError,ValueError,AttributeError): pass
    return versions


def newer(available,current):
    return tuple(map(int,re.findall(r'\d+',available)))>tuple(map(int,re.findall(r'\d+',current)))


def check_updates(folder,http=requests):
    versions=load_versions(folder)
    def check(item):
        key,spec=item
        row={'key':key,'name':spec['name'],'current':versions[key],'latest':'','available':False,
             'managed':bool(spec.get('managed')),'can_update':False,'error':''}
        try:
            endpoint='https://api.github.com/repos/'+spec['repo']+'/releases'
            response=http.get(endpoint+('?per_page=10' if key=='ffmpeg' else '/latest'),timeout=25)
            response.raise_for_status(); release=response.json()
            if key=='ffmpeg': release=next(r for r in release if r['tag_name'].startswith('autobuild-') and not r.get('draft'))
            if release.get('draft') or (release.get('prerelease') and key!='ffmpeg'): raise ValueError('Vakaa julkaisu puuttuu.')
            row.update(latest=release['tag_name'],release_url=release['html_url'])
            row['available']=newer(row['latest'],row['current'])
            if not row['managed']:
                asset=next(a for a in release['assets'] if re.fullmatch(spec['asset'],a['name']))
                row['asset']={field:asset.get(field) for field in ('name','browser_download_url','digest','size')}
                digest=asset.get('digest') or ''
                if not re.fullmatch(r'sha256:[0-9a-fA-F]{64}',digest): raise ValueError('Julkaisusta puuttuu SHA-256-tarkistussumma.')
                row['can_update']=row['available']
        except Exception as error: row['error']='GitHub-tarkistus epäonnistui: '+str(error)
        return row
    with ThreadPoolExecutor(max_workers=4) as pool: return list(pool.map(check,SPECS.items()))


def verify_binary(path):
    with path.open('rb') as source: header=source.read(2)
    if header!=b'MZ': raise ValueError('Paketista puuttuu kelvollinen Windows-ohjelma: '+path.name)
    flag='-version' if path.name in ('ffmpeg.exe','ffprobe.exe') else '--version'
    environment=os.environ.copy();environment['PYINSTALLER_RESET_ENVIRONMENT']='1'
    result=subprocess.run([str(path),flag],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=45,
                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),env=environment)
    if result.returncode: raise ValueError('Uusi työkalu ei läpäissyt käynnistystestiä: '+path.name)


def install_updates(rows,folder,cancel,status=lambda message:None,http=requests):
    root=Path(folder).resolve();root.mkdir(parents=True,exist_ok=True)
    versions=load_versions(root); staged={}; applied=[]
    with tempfile.TemporaryDirectory(prefix='.update-',dir=root) as temporary:
        work=Path(temporary); backup=work/'backup';backup.mkdir()
        for row in rows:
            if cancel.is_set(): raise RuntimeError('Työkalupäivitys keskeytetty.')
            key=row['key']; spec=SPECS[key]
            if spec.get('managed'): raise ValueError('SpotDL päivitetään sovelluspäivityksen mukana.')
            asset=row['asset']; url=asset['browser_download_url']
            prefix='https://github.com/'+spec['repo']+'/releases/download/'
            if not isinstance(url,str) or not url.startswith(prefix): raise ValueError('Virheellinen työkalun latausosoite.')
            digest=asset.get('digest') or ''
            if not re.fullmatch(r'sha256:[0-9a-fA-F]{64}',digest): raise ValueError('Tarkistussumma puuttuu.')
            package=work/(key+'.download'); checksum=hashlib.sha256();size=0
            status('Ladataan '+spec['name']+'…')
            with http.get(url,stream=True,timeout=(15,60)) as response:
                response.raise_for_status()
                with package.open('wb') as output:
                    for block in response.iter_content(1024*1024):
                        if cancel.is_set(): raise RuntimeError('Työkalupäivitys keskeytetty.')
                        if block:
                            output.write(block);checksum.update(block);size+=len(block)
                            if size>1024*1024*1024: raise ValueError('Työkalupaketti on liian suuri.')
            if checksum.hexdigest()!=digest[7:].lower(): raise ValueError('Tarkistussumma ei täsmää: '+spec['name'])
            if asset['name'].endswith('.zip'):
                with zipfile.ZipFile(package) as archive:
                    for filename in spec['files']:
                        matches=[i for i in archive.infolist() if Path(i.filename.replace('\\','/')).name==filename]
                        if len(matches)!=1 or matches[0].file_size>1024*1024*1024: raise ValueError('Työkalupaketin sisältö on virheellinen: '+filename)
                        target=work/filename
                        with archive.open(matches[0]) as source,target.open('wb') as output: shutil.copyfileobj(source,output)
                        staged[filename]=target
            else:
                target=work/spec['files'][0];package.replace(target);staged[target.name]=target
            for filename in spec['files']:
                if cancel.is_set(): raise RuntimeError('Työkalupäivitys keskeytetty.')
                status('Tarkistetaan '+filename+'…');verify_binary(staged[filename])
            versions[key]=row['latest']
        if cancel.is_set(): raise RuntimeError('Työkalupäivitys keskeytetty.')
        status('Asennetaan tarkistetut työkalut…')
        try:
            for filename,path in staged.items():
                destination=root/filename
                if destination.exists(): destination.replace(backup/filename)
                applied.append(filename);path.replace(destination)
            state=work/VERSION_FILE;state.write_text(json.dumps(versions,ensure_ascii=False),encoding='utf-8');state.replace(root/VERSION_FILE)
        except Exception:
            for filename in reversed(applied):
                (root/filename).unlink(missing_ok=True)
                if (backup/filename).exists(): (backup/filename).replace(root/filename)
            raise
    return versions
