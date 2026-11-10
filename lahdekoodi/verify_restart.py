"""Exercise Setup's restart with an inherited, deleted onefile runtime.

The probe uses a separate AppId, install directory and launch arguments, so it
does not change an existing Albumilataaja installation or its shortcuts.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time

def verify(iscc,package,work):
    package=Path(package).resolve(); work=Path(work).resolve(); work.mkdir(parents=True,exist_ok=True)
    source=Path(__file__).with_name('installer.iss').read_text(encoding='utf-8')
    install=work/'installed'; result=work/'restart-result.json'
    if result.exists(): result.unlink()
    source=re.sub(r'^AppId=.*$', 'AppId=Albumilataaja.RuntimeRestartProbe',source,flags=re.M)
    source=source.replace('OutputBaseFilename=Albumilataaja-Setup','OutputBaseFilename=RuntimeRestart-Probe')
    source=source.replace('DefaultGroupName=Albumilataaja','DefaultGroupName=Albumilataaja runtime probe')
    source=source.replace('SetupIconFile=app.ico','SetupIconFile='+str(Path(__file__).with_name('app.ico').resolve()))
    source=re.sub(r'\[Icons\].*?(?=\[Run\])','',source,flags=re.S)
    source='\n'.join(line for line in source.splitlines() if not line.startswith('Source:') or '\\Albumilataaja.exe"' in line)
    source=source.replace('Flags: nowait; Check: IsUpdateMode',f'Parameters: "--runtime-self-test ""{result}"""; Flags: nowait; Check: IsUpdateMode')
    script=work/'probe.iss'; script.write_text(source,encoding='utf-8')
    subprocess.run([str(iscc),'/DPackageDir='+str(package),'/DOutputDirPath='+str(work),str(script)],check=True,stdout=subprocess.DEVNULL)
    env=os.environ.copy(); env.pop('PYINSTALLER_RESET_ENVIRONMENT',None)
    missing=work/'deleted-old-runtime'
    env.update({'_PYI_ARCHIVE_FILE':str(install/'Albumilataaja.exe'),
                '_PYI_APPLICATION_HOME_DIR':str(missing),'_PYI_PARENT_PROCESS_LEVEL':'1'})
    if missing.exists(): raise RuntimeError('Probe runtime must be absent')
    subprocess.run([str(work/'RuntimeRestart-Probe.exe'),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/NOICONS','/TASKS=',
                    '/UPDATEAPP=1','/DIR='+str(install),'/LOG='+str(work/'install.log')],env=env,check=True,timeout=60)
    deadline=time.monotonic()+20
    while not result.exists() and time.monotonic()<deadline: time.sleep(.1)
    if not result.exists(): raise RuntimeError('Restarted app failed to load its Python runtime; see probe install.log')
    data=json.loads(result.read_text(encoding='utf-8'))
    if not data['python_dll_present'] or data['runtime_directory']==str(missing): raise RuntimeError('Restart reused the deleted runtime')
    subprocess.run([str(install/'unins000.exe'),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'],check=True,timeout=30)
    print('Restart regression passed: fresh Python runtime loaded after Setup, version '+data['version'])

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--iscc',required=True); p.add_argument('--package',required=True); p.add_argument('--work',required=True)
    args=p.parse_args(); verify(args.iscc,args.package,args.work)
