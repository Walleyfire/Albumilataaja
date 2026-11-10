param([string]$Iscc = '')
$ErrorActionPreference = 'Stop'
$source = $PSScriptRoot
$repo = Split-Path $source -Parent
$package = Join-Path $repo 'dist\Albumilataaja'
New-Item -ItemType Directory -Force $package | Out-Null
python -m pip install -r (Join-Path $source 'requirements.txt')
if ($LASTEXITCODE) { throw 'Dependency installation failed' }
python -m unittest discover -s $source -v
if ($LASTEXITCODE) { throw 'Tests failed' }
python (Join-Path $source 'fetch_tools.py') (Join-Path $package 'tools')
if ($LASTEXITCODE) { throw 'Tool download failed' }
python -m PyInstaller --noconfirm --clean --windowed --onefile --name Albumilataaja --icon (Join-Path $source 'app.ico') --add-data "$(Join-Path $source 'app.ico');." --distpath $package --workpath (Join-Path $repo 'build') --specpath (Join-Path $repo 'build') --collect-all ytmusicapi (Join-Path $source 'app.py')
if ($LASTEXITCODE) { throw 'Application build failed' }
Copy-Item -LiteralPath (Join-Path $repo 'licenses') -Destination $package -Recurse -Force
Copy-Item -LiteralPath (Join-Path $repo 'README.md'),(Join-Path $repo 'THIRD_PARTY.md') -Destination $package -Force
$versionLine = Select-String -LiteralPath (Join-Path $source 'app.py') -Pattern "^VERSION = '([0-9.]+)'"
$appVersion = $versionLine.Matches[0].Groups[1].Value
if (-not $Iscc) {
  $candidates = @('C:\Program Files (x86)\Inno Setup 6\ISCC.exe','C:\Program Files\Inno Setup 7\ISCC.exe')
  $Iscc = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $Iscc) { throw 'Install Inno Setup 6/7 or provide -Iscc with the compiler path.' }
$dist = Join-Path $repo 'dist'
& $Iscc "/DAppVersion=$appVersion" "/DPackageDir=$package" "/DOutputDirPath=$dist" (Join-Path $source 'installer.iss')
if ($LASTEXITCODE) { throw 'Installer build failed' }
$installer=Join-Path $dist 'Albumilataaja-Setup.exe'
$hash=(Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content -LiteralPath (Join-Path $dist 'SHA256SUMS.txt') -Value "$hash  Albumilataaja-Setup.exe" -Encoding ascii
Write-Output "Built Albumilataaja $appVersion in $dist"
