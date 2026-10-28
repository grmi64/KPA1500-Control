# Run ONLY inside a fresh, network-disabled Windows Sandbox, using the
# private KPA1500Control.Feasibility identity and unsigned review binaries.
# Mappings: C:\KPAMSIXInput (read-only), C:\KPAMSIXResults (writable).
# Inputs: feasibility-unsigned.msix, package.sha256, portable.zip containing
# KPA1500 Control Review/, and the existing offline tools/signTool runtime.
# This installs a guest-only temporary test certificate; never run on host.
# All app processes force --demo. Fixture IPs are documentation-only values.
$ErrorActionPreference='Stop'
$out='C:\KPAMSIXResults'
$r=[ordered]@{passed=$false;stage='setup';hardware=$false;publication=$false;identity='private non-Store feasibility identity';multiple_monitor='pending';final_package_hardware='pending'}
function Save-Report {$r|ConvertTo-Json -Depth 10|Set-Content "$out\result.json" -Encoding UTF8}
Start-Transcript -Path "$out\harness.log" -Force
try {
 $r.active_network_adapters=@(Get-NetAdapter -ErrorAction SilentlyContinue|Where-Object Status -eq 'Up').Count
 if($r.active_network_adapters){throw 'Network-disabled guest required'}
 if([Environment]::UserName -ne 'WDAGUtilityAccount'){throw 'Disposable guest required'}
 $root='C:\KPAFeasibility';New-Item -ItemType Directory -Path $root|Out-Null
 $source='C:\KPAMSIXInput\feasibility-unsigned.msix'
 $r.unsigned_msix_sha256=(Get-FileHash $source).Hash.ToLower()
 if($r.unsigned_msix_sha256 -ne (Get-Content 'C:\KPAMSIXInput\package.sha256').Trim()){throw 'Proof package mismatch'}
 Copy-Item $source "$root\feasibility.msix"
 $cert=New-SelfSignedCertificate -Type Custom -KeyUsage DigitalSignature -Subject 'CN=KPA1500OfflineFeasibility' -CertStoreLocation Cert:\CurrentUser\My -NotAfter (Get-Date).AddDays(2) -FriendlyName 'Disposable KPA1500 offline feasibility only' -TextExtension @('2.5.29.37={text}1.3.6.1.5.5.7.3.3','2.5.29.19={text}')
 Export-Certificate -Cert $cert -FilePath "$root\test.cer"|Out-Null
 Import-Certificate -FilePath "$root\test.cer" -CertStoreLocation Cert:\LocalMachine\TrustedPeople|Out-Null
 & C:\KPAMSIXInput\tools\signtool.exe sign /fd SHA256 /sha1 $cert.Thumbprint "$root\feasibility.msix" *> "$out\test-package-sign.log"
 if($LASTEXITCODE -ne 0){throw 'Guest-only package signing failed'}
 $r.test_signing='Disposable guest-only self-signed certificate; no network timestamp; not a release signature'
 Add-AppxPackage -Path "$root\feasibility.msix"
 $package=Get-AppxPackage -Name KPA1500Control.Feasibility
 if(-not $package -or [string]$package.Version -ne '1.0.25.0'){throw 'Package not installed correctly'}
 $r.package_full_name=$package.PackageFullName;$r.package_family=$package.PackageFamilyName;$r.install_location=$package.InstallLocation
 $r.stage='installed';Save-Report
 Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Text;
[ComImport,Guid("45BA127D-10A8-46EA-8AB7-56EA9078943C")] class KPAActivationManager {}
[ComImport,InterfaceType(ComInterfaceType.InterfaceIsIUnknown),Guid("2E941141-7F97-4756-BA1D-9DECDE894A3D")]
interface IKPAActivationManager {
 [PreserveSig] int ActivateApplication([MarshalAs(UnmanagedType.LPWStr)] string id,[MarshalAs(UnmanagedType.LPWStr)] string args,uint options,out uint processId);
 [PreserveSig] int ActivateForFile(string id,IntPtr item,string verb,out uint processId);
 [PreserveSig] int ActivateForProtocol(string id,IntPtr item,out uint processId);
}
public static class KPAPackageTest {
 static IKPAActivationManager manager=(IKPAActivationManager)new KPAActivationManager();
 public static int Launch(string id,string args){uint pid;int hr=manager.ActivateApplication(id,args,2,out pid);if(hr<0)Marshal.ThrowExceptionForHR(hr);return (int)pid;}
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode)] static extern int GetPackageFullName(IntPtr process,ref uint size,StringBuilder name);
 public static string PackageName(IntPtr process){uint size=0;int hr=GetPackageFullName(process,ref size,null);if(hr==15700)return "unpackaged";if(hr!=122)throw new Exception("Package query: "+hr);var s=new StringBuilder((int)size);hr=GetPackageFullName(process,ref size,s);if(hr!=0)throw new Exception("Package query: "+hr);return s.ToString();}
}
"@
 $aumid=$package.PackageFamilyName+'!App'
 $r.stage='instance-investigation';$r.cases=@();Save-Report
 $portableRoot="$root\portable"
 Expand-Archive -LiteralPath 'C:\KPAMSIXInput\portable.zip' -DestinationPath $portableRoot
 $portableExe="$portableRoot\KPA1500 Control Review\KPA1500 Control Review.exe"
 function App-Processes {
  @(Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -and ($_.ExecutablePath -eq $portableExe -or $_.ExecutablePath -eq ($package.InstallLocation+'\App\KPA1500 Control Review.exe'))})
 }
 function Snapshot-Apps {
  $rows=@()
  foreach($p in @(App-Processes)) {
   $proc=Get-Process -Id $p.ProcessId -ErrorAction SilentlyContinue
   if(-not $proc){continue}
   $listen=@(Get-NetTCPConnection -State Listen -OwningProcess $p.ProcessId -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort)
   $rows+=@{pid=[int]$p.ProcessId;parent=[int]$p.ParentProcessId;identity=[KPAPackageTest]::PackageName($proc.Handle);title=$proc.MainWindowTitle;listeners=$listen;arguments=$p.CommandLine}
  }
  return $rows
 }
 function Simulation-Window($process) {
  try{$process.Refresh();return (-not $process.HasExited -and $process.MainWindowTitle.StartsWith('KPA1500 Control') -and $process.MainWindowTitle.EndsWith('Simulation'))}catch{return $false}
 }
 function Metadata-Snapshot($shared) {
  $paths=@([IO.Path]::ChangeExtension($shared,'instance.json'))
  $private=Join-Path $env:LOCALAPPDATA ('Packages\'+$package.PackageFamilyName)
  if(Test-Path $private){$paths+=@(Get-ChildItem $private -Filter '*.instance.json' -Recurse -ErrorAction SilentlyContinue|ForEach-Object FullName)}
  $low=Join-Path (Split-Path $env:LOCALAPPDATA -Parent) 'LocalLow\Station Instruments\instances';if(Test-Path $low){$paths+=@(Get-ChildItem $low -Filter '*.json'|ForEach-Object FullName)};$found=@()
  foreach($mp in @($paths|Select-Object -Unique)) {
   if(-not (Test-Path $mp)){continue}
   try {
    $metaValue=Get-Content $mp -Raw|ConvertFrom-Json
    $uri=[uri]$metaValue.url
    if($uri.Host -ne '127.0.0.1' -or $uri.Scheme -ne 'http'){throw 'Nonloopback metadata'}
    $s=Invoke-RestMethod ($metaValue.url+'state') -TimeoutSec 2
    $found+=@{path=$mp;port=$uri.Port;live=($s.offline_only -and $s.state.demo -and $s.state.status -eq 'live');offline_only=$s.offline_only;mode=$s.state.status}
   }catch{$found+=@{path=$mp;error=$_.Exception.GetType().Name}}
  }
  return $found
 }
 function Launch-App($kind,$settingsPath,$port,$handoff=$false) {
  $arguments='--demo --http-port '+$port+' --settings '+$settingsPath
  if($handoff){$arguments+=' --mode-handoff'}
  if($kind -eq 'packaged'){$pidValue=[KPAPackageTest]::Launch($aumid,$arguments);return Get-Process -Id $pidValue}
  return Start-Process -FilePath $portableExe -ArgumentList $arguments -PassThru -RedirectStandardError "$out\portable-$port.stderr.txt" -RedirectStandardOutput "$out\portable-$port.stdout.txt"
 }
 $caseIndex=0
 foreach($plan in @(
  @{first='packaged';second='portable';storage='private'},
  @{first='portable';second='packaged';storage='both'},
  @{first='packaged';second='portable';storage='both'},
  @{first='portable';second='packaged';storage='real'},
  @{first='packaged';second='portable';storage='fresh'},
  @{first='portable';second='packaged';storage='fresh'},
  @{first='packaged';second='packaged';storage='private'},
  @{first='portable';second='portable';storage='real'})) {
  $pair=@($plan.first,$plan.second)
  $caseIndex++
  $shared=if($plan.storage -eq 'fresh'){"$root\case$caseIndex\settings.json"}else{Join-Path $env:LOCALAPPDATA "KPA1500SavedIdentity\case$caseIndex\settings.json"}
  $port1=52200+($caseIndex*2);$port2=$port1+1
  $case=[ordered]@{first=$pair[0];second=$pair[1];settings=$shared;first_port=$port1;second_port=$port2}
  $r.stage='starting-'+$pair[0]+'-then-'+$pair[1];Save-Report
  try {
   $case.storage=$plan.storage;$case.seeded_files=@()
   $relative="KPA1500SavedIdentity\case$caseIndex\settings.json"
   $privateSettings=Join-Path $env:LOCALAPPDATA ('Packages\'+$package.PackageFamilyName+'\LocalCache\Local\'+$relative)
   if($plan.storage -in @('private','both')){
    New-Item -ItemType Directory -Path (Split-Path $privateSettings -Parent) -Force|Out-Null
    [IO.File]::WriteAllText($privateSettings,'{"mode":"tcp","host":"192.0.2.41","auto_connect":true,"share_readings":true}')
    $case.seeded_files+=@{path=$privateSettings;sha256=(Get-FileHash $privateSettings).Hash}
   }
   if($plan.storage -in @('real','both')){
    New-Item -ItemType Directory -Path (Split-Path $shared -Parent) -Force|Out-Null
    [IO.File]::WriteAllText($shared,'{"mode":"tcp","host":"192.0.2.42","auto_connect":true,"share_readings":true}')
    $case.seeded_files+=@{path=$shared;sha256=(Get-FileHash $shared).Hash}
   }
   $case.expected_host=if($plan.storage -eq 'fresh'){''}elseif($pair[0] -eq 'packaged' -and $plan.storage -in @('private','both')){'192.0.2.41'}else{'192.0.2.42'}
   $logicalKey='KPA1500-Windows-review:'+$shared.ToLowerInvariant()
   $sha=[Security.Cryptography.SHA256]::Create();$logicalHash=([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($logicalKey)))).Replace('-','').ToLowerInvariant();$sha.Dispose()
   $case.logical_hash=$logicalHash
   $first=Launch-App $pair[0] $shared $port1
   $deadline=(Get-Date).AddSeconds(45);$initial=@()
   do{$initial=@(Metadata-Snapshot $shared);if(@($initial|Where-Object {$_.port -eq $port1 -and $_.live}).Count -and (Simulation-Window $first)){break};Start-Sleep -Milliseconds 700}while((Get-Date) -lt $deadline)
   if(-not @($initial|Where-Object {$_.port -eq $port1 -and $_.live}).Count -or -not (Simulation-Window $first)){throw 'First simulator/window not ready'}
   $case.logical_identity_matches=(@($initial|Where-Object { $_.live -and $_.port -eq $port1 -and [IO.Path]::GetFileName($_.path) -eq ($logicalHash+'.json') }).Count -gt 0);$case.before=$initial;$case.before_processes=@(Snapshot-Apps)
   $originalPath=@($initial|Where-Object {$_.port -eq $port1 -and $_.live})[0].path;$original=Get-Content $originalPath -Raw|ConvertFrom-Json
   $second=Launch-App $pair[1] $shared $port2;$null=$second.Handle
   $didExit=$second.WaitForExit(15000)
   $case.second_exited=$didExit
   if($didExit){$case.second_exit_code=$second.ExitCode}
   $case.after=@(Metadata-Snapshot $shared);$case.processes=@(Snapshot-Apps)
   try {
    $oldState=Invoke-RestMethod ($original.url+'state') -TimeoutSec 2
    $case.correct_settings_view=($oldState.connection.host -eq $case.expected_host);$case.simulation_safeguards=($oldState.offline_only -and $oldState.state.demo -and -not $oldState.connection.auto_connect -and -not $oldState.connection.share_readings)
    $case.first_still_live=($oldState.offline_only -and $oldState.state.demo -and $oldState.state.status -eq 'live')
    $reply=Invoke-RestMethod ($original.url+'activate') -Method Post -Body '{}' -ContentType 'application/json' -Headers @{'X-Amp-Token'=$original.token} -TimeoutSec 2
    $case.direct_activation=($reply.activated -eq $true)
   }catch{$case.activation_error=$_.Exception.GetType().Name}
   $case.second_listener=@($case.processes|ForEach-Object {$_.listeners}|Where-Object LocalPort -eq $port2).Count -gt 0
   $case.two_verified_live=($case.first_still_live -and @($case.after|Where-Object {$_.port -eq $port2 -and $_.live}).Count -gt 0)
   # End the synthetic owner process, then acquire the identical settings
   # identity from the other context without any lock-recovery command.
   foreach($p in @(App-Processes)){Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue}
   Start-Sleep -Milliseconds 500
   $takeover=Launch-App $pair[1] $shared $port2 $true;$null=$takeover.Handle
   $deadline=(Get-Date).AddSeconds(30);$recovered=$false
   do{$fresh=@(Metadata-Snapshot $shared);if(@($fresh|Where-Object {$_.port -eq $port2 -and $_.live}).Count -and (Simulation-Window $takeover)){$recovered=$true;break};Start-Sleep -Milliseconds 400}while((Get-Date) -lt $deadline)
   $case.same_settings_after_owner_death=$recovered;$case.takeover_mode_handoff=$true;$case.reopen_identity_matches=(@($fresh|Where-Object {$_.live -and $_.port -eq $port2 -and [IO.Path]::GetFileName($_.path) -eq ($logicalHash+'.json')}).Count -gt 0)
   $case.recovery_processes=@(Snapshot-Apps)
   $lockKey='KPA1500-Windows-review:'+$shared.ToLowerInvariant()
   $sha=[Security.Cryptography.SHA256]::Create();$hash=([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($lockKey)))).Replace('-','').ToLowerInvariant();$sha.Dispose()
   $case.lock_hash=$hash
   $case.lock_paths=@(Get-ChildItem -Path (Join-Path $env:LOCALAPPDATA 'Station Instruments'),(Join-Path $env:LOCALAPPDATA ('Packages\'+$package.PackageFamilyName)) -Filter ($hash+'.lock') -Recurse -ErrorAction SilentlyContinue|ForEach-Object FullName)
  }catch{$case.error=$_.Exception.Message}
  finally {
   $case.final_processes=@(Snapshot-Apps)
   foreach($p in @(App-Processes)){Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue}
   Start-Sleep -Seconds 2
   $case.remaining=@(App-Processes).Count;$case.saved_files_unchanged=(@($case.seeded_files|Where-Object {-not (Test-Path $_.path) -or (Get-FileHash $_.path).Hash -ne $_.sha256}).Count -eq 0)
   $r.cases+=@($case);Save-Report
  }
 }
 $r.instance_acceptance_passed=(@($r.cases|Where-Object {-not $_.second_exited -or $_.second_exit_code -ne 0 -or $_.second_listener -or -not $_.first_still_live -or -not $_.direct_activation -or -not $_.same_settings_after_owner_death -or -not $_.logical_identity_matches -or -not $_.reopen_identity_matches -or -not $_.correct_settings_view -or -not $_.simulation_safeguards -or -not $_.saved_files_unchanged -or $_.error}).Count -eq 0)
 $settings="$root\final-smoke\settings.json"
 foreach($phase in @('first-launch','reopen')) {
  $r.stage='final-'+$phase;Save-Report
  $activationArgs='--demo --http-port 0 --settings '+$settings+' --smoke-test --smoke-close-test'
  if($phase -eq 'reopen'){$activationArgs+=' --smoke-reopen'}
  $appPid=[KPAPackageTest]::Launch($aumid,$activationArgs);$app=Get-Process -Id $appPid;$null=$app.Handle
  if([KPAPackageTest]::PackageName($app.Handle) -ne $package.PackageFullName){throw 'Smoke missing package identity'}
  if(-not $app.WaitForExit(120000)){throw 'Final smoke timed out'}
  if($app.ExitCode -ne 0){throw ('Final smoke failed: '+$app.ExitCode)}
  $s=Get-Content "$root\final-smoke\settings.smoke.json" -Raw|ConvertFrom-Json
  if($s.status -ne 'passed' -or -not $s.offline_only -or $s.sharing -or $s.auto_connect){throw 'Final smoke not offline/pass'}
  Copy-Item "$root\final-smoke\settings.smoke.json" "$out\$phase.json"
  $r[$phase+'_exit']=0
 }
 $r.stage='uninstall';Save-Report
 Remove-AppxPackage -Package $package.PackageFullName
 $r.uninstalled=(-not [bool](Get-AppxPackage -Name KPA1500Control.Feasibility))
 $r.passed=$r.instance_acceptance_passed;$r.stage='complete'
} catch {$r.error=$_.Exception.Message}
finally {
 # Scope cleanup to the known review images and fixed private proof identity.
 if(Get-Command App-Processes -ErrorAction SilentlyContinue){foreach($p in @(App-Processes)){Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue}}
 if($package -and $package.Name -eq 'KPA1500Control.Feasibility'){
  try{if(Get-AppxPackage -Name KPA1500Control.Feasibility){Remove-AppxPackage -Package $package.PackageFullName};$r.uninstalled=(-not [bool](Get-AppxPackage -Name KPA1500Control.Feasibility))}catch{$r.cleanup_error=$_.Exception.Message;$r.passed=$false}
 }
 Save-Report;Stop-Transcript
}
