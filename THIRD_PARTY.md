# Third-party software

Albumilataaja's own code is MIT licensed. The executable invokes separate command-line engines in hidden child processes. They are included for end users; no console commands are required.

- yt-dlp 2026.10.26: https://github.com/yt-dlp/yt-dlp/tree/2026.10.26 . The upstream Windows executable incorporates third-party components; see https://github.com/yt-dlp/yt-dlp#license . Source: https://github.com/yt-dlp/yt-dlp/archive/refs/tags/2026.10.26.zip .
- spotDL 4.6.0 (MIT): https://github.com/spotDL/spotify-downloader/tree/v4.6.0 . Source: https://github.com/spotDL/spotify-downloader/archive/refs/tags/v4.6.0.zip .
- FFmpeg N-128718-gb2b543c079 (GPLv3 build): https://github.com/yt-dlp/FFmpeg-Builds/releases/tag/autobuild-2026-11-09-23-32 . FFmpeg source: https://github.com/FFmpeg/FFmpeg/tree/b2b543c079 . Build scripts and dependency recipes: https://github.com/yt-dlp/FFmpeg-Builds . A copy of FFmpeg's license accompanies the binaries in licenses/FFmpeg.txt. FFmpeg is an independent program, not linked into Albumilataaja.
- Deno: https://github.com/denoland/deno (MIT). Pinned release and binary checksum are recorded in lahdekoodi/tools-lock.json. Upstream dependency sources and notices are available in the matching Deno source tree.
- ytmusicapi 1.12.3 (MIT): https://github.com/sigma67/ytmusicapi . Unofficial read-only YouTube Music client.
- Python 3.14 (PSF): https://www.python.org/ . Requests (Apache-2.0), urllib3 (MIT), certifi (MPL-2.0), charset-normalizer (MIT), idna (BSD-3-Clause), Tcl/Tk (Tcl/Tk license).
- PyInstaller 6.22.3: GPLv2 with a bootloader exception permitting distribution of bundled applications. https://pyinstaller.org/en/stable/license.html
- Inno Setup: https://jrsoftware.org/ . Installer compiler, not installed by the resulting end-user package.

License texts are in licenses/. For corresponding third-party sources, exact versions, original upstream repositories and build recipes are linked above and in tools-lock.json. These components retain their original licenses.

## Separate Spotify catalog worker

`tools/catalog.exe` runs as an independent GPL-3.0-or-later process. Its source is `lahdekoodi/spotify_catalog.py`, also included as `licenses/catalog-source.py`. It uses SpotAPI 1.2.8 (GPLv3) for public metadata: https://pypi.org/project/spotapi/1.2.8/ (source distribution available under Download files). The MIT-licensed UI exchanges JSON files with this worker and does not import it. No Spotify account credentials are used.

Worker dependencies include curl_cffi (MIT), cffi (MIT), Pillow (HPND), pycparser (BSD), readerwriterlock (MIT), typing_extensions (PSF), validators (MIT), pyotp (MIT), beautifulsoup4 (MIT), soupsieve (MIT), websockets (BSD), and colorama (BSD). Their license notices are included in licenses/.

The desktop interface uses CustomTkinter 6.0.0 (MIT) and darkdetect 0.8.0 (BSD-3-Clause). License texts are included in licenses/.
