import hashlib
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile
import tool_updates as updates


class Response:
    def __init__(self,payload=b'',data=None):self.payload=payload;self.data=data
    def raise_for_status(self):pass
    def json(self):return self.data
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def iter_content(self,size):yield self.payload


def release(key,tag,payload=b'MZnew',name=None):
    spec=updates.SPECS[key]
    name=name or {'yt-dlp':'yt-dlp.exe','deno':'deno-x86_64-pc-windows-msvc.zip','ffmpeg':'ffmpeg-N-test-win64-gpl.zip'}.get(key,'spotdl.exe')
    asset={'name':name,'digest':'sha256:'+hashlib.sha256(payload).hexdigest(),
           'browser_download_url':f"https://github.com/{spec['repo']}/releases/download/{tag}/{name}",'size':len(payload)}
    return {'key':key,'latest':tag,'asset':asset}


class ToolUpdateTests(unittest.TestCase):
    def test_bad_digest_or_binary_check_never_changes_installed_tools(self):
        for bad_digest in (True,False):
            with self.subTest(digest=bad_digest),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);(root/'yt-dlp.exe').write_bytes(b'old')
                row=release('yt-dlp','2026.11.23')
                if bad_digest:row['asset']['digest']='sha256:'+'0'*64
                class HTTP:
                    def get(self,*args,**kwargs):return Response(b'MZnew')
                with patch.object(updates,'verify_binary',side_effect=ValueError('binary check failed')):
                    with self.assertRaises(ValueError):updates.install_updates([row],root,threading.Event(),http=HTTP())
                self.assertEqual((root/'yt-dlp.exe').read_bytes(),b'old')
                self.assertFalse(list(root.glob('.update-*')))
    def test_cancel_during_download_keeps_original(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'yt-dlp.exe').write_bytes(b'old');cancel=threading.Event()
            class CancelResponse(Response):
                def iter_content(self,size):cancel.set();yield b'MZnew'
            class HTTP:
                def get(self,*args,**kwargs):return CancelResponse()
            with self.assertRaises(RuntimeError):updates.install_updates([release('yt-dlp','2026.11.23')],root,cancel,http=HTTP())
            self.assertEqual((root/'yt-dlp.exe').read_bytes(),b'old')
    def test_install_transaction_rolls_back_all_files_if_second_replace_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name in ('yt-dlp.exe','deno.exe'):(root/name).write_bytes(b'old-'+name.encode())
            (root/updates.VERSION_FILE).write_text(json.dumps({'yt-dlp':'old','deno':'old'}))
            payload=io.BytesIO()
            with zipfile.ZipFile(payload,'w') as archive:archive.writestr('deno.exe',b'MZdeno')
            zipped=payload.getvalue();rows=[release('yt-dlp','2026.11.23'),release('deno','v2.9.9',zipped)]
            class HTTP:
                def get(self,url,**kwargs):return Response(zipped if url.endswith('.zip') else b'MZnew')
            original_replace=Path.replace
            def replace(path,target):
                if path.name=='deno.exe' and path.parent.name!='backup' and Path(target)==root/'deno.exe':raise OSError('simulated locked destination')
                return original_replace(path,target)
            with patch.object(updates,'verify_binary'),patch.object(Path,'replace',replace):
                with self.assertRaises(OSError):updates.install_updates(rows,root,threading.Event(),http=HTTP())
            for name in ('yt-dlp.exe','deno.exe'):self.assertEqual((root/name).read_bytes(),b'old-'+name.encode())
            self.assertEqual(json.loads((root/updates.VERSION_FILE).read_text()),{'yt-dlp':'old','deno':'old'})
    def test_zip_extraction_cannot_write_outside_tools_and_versions_are_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'tools';root.mkdir()
            payload=io.BytesIO()
            with zipfile.ZipFile(payload,'w') as archive:
                archive.writestr('../../deno.exe',b'MZdeno');archive.writestr('../../escaped.txt',b'bad')
            zipped=payload.getvalue()
            class HTTP:
                def get(self,*args,**kwargs):return Response(zipped)
            with patch.object(updates,'verify_binary'):
                result=updates.install_updates([release('deno','v2.9.9',zipped)],root,threading.Event(),http=HTTP())
            self.assertEqual((root/'deno.exe').read_bytes(),b'MZdeno')
            self.assertFalse((Path(directory)/'escaped.txt').exists())
            self.assertEqual(result['deno'],'v2.9.9')
            self.assertEqual(updates.load_versions(root)['deno'],'v2.9.9')
    def test_untrusted_url_and_managed_spotdl_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            row=release('yt-dlp','2026.11.23');row['asset']['browser_download_url']='https://example.com/yt-dlp.exe'
            with self.assertRaises(ValueError):updates.install_updates([row],directory,threading.Event())
            with self.assertRaises(ValueError):updates.install_updates([{'key':'spotdl'}],directory,threading.Event())
    def test_check_uses_named_ffmpeg_release_and_marks_spotdl_managed(self):
        with tempfile.TemporaryDirectory() as directory:
            class HTTP:
                def get(self,url,**kwargs):
                    key=next(key for key,spec in updates.SPECS.items() if spec['repo'] in url)
                    tag={'yt-dlp':'2026.11.23','deno':'v2.9.9','ffmpeg':'autobuild-2026-11-24-02-40','spotdl':'v4.7.0'}[key]
                    row=release(key,tag)
                    data={'tag_name':tag,'html_url':'https://github.com/release','assets':[row['asset']]}
                    return Response(data=[{'tag_name':'latest'},data] if key=='ffmpeg' else data)
            rows={row['key']:row for row in updates.check_updates(directory,http=HTTP())}
            self.assertTrue(rows['yt-dlp']['can_update'])
            self.assertEqual(rows['ffmpeg']['latest'],'autobuild-2026-11-24-02-40')
            self.assertTrue(rows['spotdl']['available']);self.assertFalse(rows['spotdl']['can_update'])


if __name__=='__main__':unittest.main()
