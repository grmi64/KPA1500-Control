param([string]$Python = "$PSScriptRoot/../.venv/Scripts/python.exe", [switch]$ProductionIdentity)
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
$project = (Get-Location).Path
$buildName = if ($ProductionIdentity) { 'KPA1500 Control' } else { 'KPA1500 Control Review' }
$package = Join-Path $project "dist/windows/$buildName"
$exe = Join-Path $package "$buildName.exe"
if (-not (Test-Path -LiteralPath "$project/LICENSE")) { throw 'Application LICENSE is required before packaging.' }
if (Get-Process -Name $buildName -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $exe }) { throw 'Close this packaged app before rebuilding it.' }
$versionInfo = Join-Path $project "build/identity/$buildName-version.txt"
& $Python scripts/windows-version-info.py --name $buildName --output $versionInfo
if ($LASTEXITCODE -ne 0) { throw 'Windows identity generation failed' }
$assets = @('index.html','app.js','app.css','measurements.js','kpa_meter_colors.js')
$options = @('--noconfirm','--clean','--onedir','--windowed','--name',$buildName,'--icon',"$project/Assets/AppIcon.ico",'--version-file',$versionInfo,'--manifest',"$project/Sources/windows_app.manifest",'--distpath','dist/windows','--workpath','build/windows','--specpath','build','--paths','Sources','--collect-all','webview','--hidden-import','serial','--hidden-import','serial.serialwin32','--hidden-import','serial.tools.list_ports_windows','--hidden-import','clr_loader','--hidden-import','pythonnet','--copy-metadata','pywebview','--copy-metadata','pythonnet','--copy-metadata','pyserial','--add-data',"$project/ThirdPartyNotices;ThirdPartyNotices",'--add-data',"$project/LICENSE;.")
foreach ($asset in $assets) { $options += @('--add-data',"$project/Sources/$asset;.") }
& $Python -m PyInstaller @options Sources/windows_app.py
if ($LASTEXITCODE -ne 0) { throw 'Windows candidate build failed' }
Copy-Item -LiteralPath "$project/Sources/windows_dotnet.config" -Destination ($exe + '.config')
Copy-Item -LiteralPath "$project/LICENSE" -Destination (Join-Path $package 'LICENSE')
Copy-Item -LiteralPath "$project/WINDOWS.md" -Destination (Join-Path $package 'README-Windows.txt')
Copy-Item -LiteralPath "$project/LICENSING.md","$project/WINDOWS-RELEASE-IDENTITY.md" -Destination $package
Write-Output $exe

& $Python scripts/check-windows-notices.py --package $package --toc "$project/build/windows/$buildName/PYZ-00.toc"
if ($LASTEXITCODE -ne 0) { throw 'Dependency notice audit failed' }

& $Python scripts/check-windows-identity.py --package $package --name $buildName
if ($LASTEXITCODE -ne 0) { throw 'Windows identity audit failed' }

# Exercise the actual frozen GUI runtime after WebView2 loads. Local settings
# only: no controller, address probes, connections or amplifier commands.
$networkEvidence = Join-Path $project ("build/windows/$buildName/network-self-test-" + [guid]::NewGuid().ToString('N') + '.json')
& $Python scripts/check-windows-network.py --exe $exe --output $networkEvidence
if ($LASTEXITCODE -ne 0) { throw 'Frozen network configuration regression failed' }
