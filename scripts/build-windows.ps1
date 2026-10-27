param([string]$Python = "$PSScriptRoot/../.venv/Scripts/python.exe")
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
$project = (Get-Location).Path
$assets = @('index.html','app.js','app.css','measurements.js','kpa_meter_colors.js')
$options = @('--noconfirm','--clean','--onedir','--windowed','--name','KPA1500 Control Review','--manifest',"$project/Sources/windows_app.manifest",'--distpath','dist/windows','--workpath','build/windows','--specpath','build','--paths','Sources','--collect-all','webview','--hidden-import','serial','--hidden-import','serial.serialwin32','--hidden-import','serial.tools.list_ports_windows','--hidden-import','clr_loader','--hidden-import','pythonnet','--copy-metadata','pywebview','--copy-metadata','pythonnet','--copy-metadata','pyserial','--add-data',"$project/ThirdPartyNotices;ThirdPartyNotices")
foreach ($asset in $assets) { $options += @('--add-data',"$project/Sources/$asset;.") }
& $Python -m PyInstaller @options Sources/windows_app.py
if ($LASTEXITCODE -ne 0) { throw 'Review build failed' }
Write-Output "$project/dist/windows/KPA1500 Control Review/KPA1500 Control Review.exe"

& $Python scripts/check-windows-notices.py
if ($LASTEXITCODE -ne 0) { throw 'Dependency notice audit failed' }
