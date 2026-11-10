"""Download pinned upstream Windows tools, checking every archive before extraction."""
import hashlib
import json
from pathlib import Path
import sys
import urllib.request
import zipfile

def fetch(destination):
    destination=Path(destination).resolve(); destination.mkdir(parents=True,exist_ok=True)
    cache=destination.parent.parent/'tool-downloads'; cache.mkdir(exist_ok=True)
    lock=json.loads(Path(__file__).with_name('tools-lock.json').read_text())
    for item in lock:
        archive=cache/item['filename']
        if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest()!=item['sha256']:
            print('Downloading',item['filename'],flush=True)
            with urllib.request.urlopen(item['url'],timeout=120) as response, archive.open('wb') as output:
                import shutil
                shutil.copyfileobj(response,output)
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=item['sha256']:
            archive.unlink(); raise RuntimeError('SHA256 mismatch: '+item['filename'])
        if item['target']:
            (destination/item['target']).write_bytes(archive.read_bytes())
        else:
            with zipfile.ZipFile(archive) as z:
                for name in z.namelist():
                    leaf=Path(name).name
                    if leaf in ['ffmpeg.exe','ffprobe.exe','deno.exe']:
                        (destination/leaf).write_bytes(z.read(name))
    print('Tool checksums verified.')

if __name__=='__main__': fetch(sys.argv[1])
