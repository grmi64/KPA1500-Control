param(
 [Parameter(Mandatory=$true)][string]$Package,
 [Parameter(Mandatory=$true)][string]$Toc,
 [Parameter(Mandatory=$true)][string]$Output,
 [string]$Python = "$PSScriptRoot/../.venv/Scripts/python.exe",
 [switch]$Sign,
 [string]$SignTool,
 [string]$Dlib,
 [string]$Metadata,
 [string]$ExpectedPublisher,
 [string]$TimestampUrl = 'http://timestamp.acs.microsoft.com'
)
# Without -Sign this is an offline audit/plan only. -Sign contacts Azure and the timestamp service.
$ErrorActionPreference='Stop'
$sourceItem=Resolve-Path -LiteralPath $Package
if($sourceItem.Provider.Name -ne 'FileSystem'){throw 'Package must use the FileSystem provider.'}
$source=$sourceItem.ProviderPath
function Assert-PlainSigningPath([string]$Path) {
 # Walk even missing descendants up to the root. Never follow a junction or
 # symbolic link into a source/output alias, and do not suppress access errors.
 $candidate=$Path
 while($candidate) {
  $item=$null
  try {$item=Get-Item -LiteralPath $candidate -Force -ErrorAction Stop}
  catch [System.Management.Automation.ItemNotFoundException] {}
  if($item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw "Signing paths must not contain reparse points: $candidate"}
  if($item -and -not $item.PSIsContainer){throw "Signing path ancestor must be a directory: $candidate"}
  $parent=[IO.Directory]::GetParent($candidate)
  $candidate=if($parent){$parent.FullName}else{$null}
 }
}
$outputProvider=$null;$outputDrive=$null
$Output=$ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Output,[ref]$outputProvider,[ref]$outputDrive)
if($outputProvider.Name -ne 'FileSystem'){throw 'Output must use the FileSystem provider.'}
if($Output.Equals($source,[StringComparison]::OrdinalIgnoreCase) -or $Output.StartsWith($source+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Output must be outside the source package.'}
if(Test-Path -LiteralPath $Output){throw 'Output must be a new, separate directory; existing candidates are never modified.'}
Assert-PlainSigningPath $source
Assert-PlainSigningPath $Output
if(@(Get-ChildItem -LiteralPath $source -Recurse -Force|Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}).Count){throw 'Package must not contain reparse points.'}
& $Python "$PSScriptRoot/check-windows-notices.py" --package $source --toc $Toc
if($LASTEXITCODE -ne 0){throw 'Pre-sign pinned dependency/license audit failed'}
$allowed=@('_internal/_cffi_backend.cp312-win_amd64.pyd','_internal/clr_loader/ffi/dlls/amd64/ClrLoader.dll','_internal/clr_loader/ffi/dlls/x86/ClrLoader.dll','_internal/pythonnet/runtime/Python.Runtime.dll','_internal/webview/lib/WebBrowserInterop.x64.dll','_internal/webview/lib/WebBrowserInterop.x86.dll')
$rows=@()
foreach($file in Get-ChildItem -LiteralPath $source -Recurse -File) {
 if($file.Extension -notin '.exe','.dll','.pyd'){continue}
 $relative=$file.FullName.Substring($source.Length+1).Replace('\','/')
 $signature=Get-AuthenticodeSignature -LiteralPath $file.FullName
 $action='preserve'
 if($signature.Status -eq 'NotSigned') {
  if($relative -notin $allowed -and $relative -notin @('KPA1500 Control.exe','KPA1500 Control Review.exe')){throw "Unreviewed unsigned binary: $relative"}
  $action='sign'
 } elseif($signature.Status -ne 'Valid'){throw "Untrusted or damaged signature: $relative ($($signature.Status))"}
 $rows+=@([ordered]@{path=$relative;before=(Get-FileHash -LiteralPath $file.FullName).Hash.ToLowerInvariant();action=$action;original_publisher=$signature.SignerCertificate.Subject})
}
if(-not $Sign){[ordered]@{source=$source;output=$Output;files=$rows}|ConvertTo-Json -Depth 5;return}
foreach($value in @($SignTool,$Dlib,$Metadata,$ExpectedPublisher)){if(-not $value){throw '-Sign requires SignTool, Dlib, Metadata and ExpectedPublisher.'}}
foreach($path in @($SignTool,$Dlib,$Metadata)){if(-not (Test-Path -LiteralPath $path -PathType Leaf)){throw "Signing input missing: $path"}}
# Recheck path guards immediately before copying; audit/verification may take time.
Assert-PlainSigningPath $source
Assert-PlainSigningPath $Output
if(Test-Path -LiteralPath $Output){throw 'Output appeared during the signing audit; choose a new directory.'}
# Copy only after every signature/provenance prerequisite passes.
Copy-Item -LiteralPath $source -Destination $Output -Recurse
$destination=(Resolve-Path -LiteralPath $Output).Path
foreach($row in $rows) {
 $file=Join-Path $destination $row.path
 if((Get-FileHash -LiteralPath $file).Hash.ToLowerInvariant() -ne $row.before){throw "Copy changed before signing: $($row.path)"}
 if($row.action -eq 'sign') {
  & $SignTool sign /v /fd SHA256 /tr $TimestampUrl /td SHA256 /dlib $Dlib /dmdf $Metadata $file
  if($LASTEXITCODE -ne 0){throw "Signing failed: $($row.path). Partial output is not a release candidate."}
 }
 $signature=Get-AuthenticodeSignature -LiteralPath $file
 if($signature.Status -ne 'Valid'){throw "Signature verification failed: $($row.path)"}
 if($row.action -eq 'sign' -and ($signature.SignerCertificate.Subject -ne $ExpectedPublisher -or -not $signature.TimeStamperCertificate)){throw "Wrong publisher or missing timestamp: $($row.path)"}
 & $SignTool verify /pa /all /v /tw $file
 if($LASTEXITCODE -ne 0){throw "SignTool verification failed: $($row.path)"}
 $row.after=(Get-FileHash -LiteralPath $file).Hash.ToLowerInvariant()
 $row.publisher=$signature.SignerCertificate.Subject
 if($row.action -eq 'preserve' -and $row.before -ne $row.after){throw "Vendor-signed payload changed: $($row.path)"}
}
& $Python "$PSScriptRoot/check-windows-signing.py" --source $source --target $destination
if($LASTEXITCODE -ne 0){throw 'Signing changed payload code/data; reject this output.'}
# External receipt: keep the package file set identical to the pre-sign audited source.
$rows|ConvertTo-Json -Depth 5|Set-Content ($destination+'.signatures.json') -Encoding UTF8
Write-Output "Fully signed payload verified: $destination"
