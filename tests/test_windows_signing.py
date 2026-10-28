"""Offline signing-transform regressions; no certificate, network, GUI or hardware."""
import importlib.util, json, os, pathlib, shutil, struct, subprocess, sys, tempfile, unittest

_spec=importlib.util.spec_from_file_location('signing_check',pathlib.Path(__file__).resolve().parents[1]/'scripts/check-windows-signing.py')
check=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(check)


def image(magic=0x20b, extra=3):
    data=bytearray(512+extra);data[:2]=b'MZ';struct.pack_into('<I',data,0x3c,0x80)
    data[0x80:0x84]=b'PE\0\0';struct.pack_into('<H',data,0x94,240)
    struct.pack_into('<H',data,0x98,magic)
    struct.pack_into('<I',data,0x98+(108 if magic==0x20b else 92),16)
    data[450:454]=b'CODE'
    return bytes(data)


def signed(data):
    result=bytearray(data);checksum,security,_,_=check.pe_fields(data)
    offset=(len(data)+7)&~7
    struct.pack_into('<I',result,checksum,12345);struct.pack_into('<II',result,security,offset,16)
    result.extend(bytes(offset-len(data)));result.extend(struct.pack('<IHH',16,0x200,2)+b'CERTDATA')
    return bytes(result)


class SigningTests(unittest.TestCase):
    def test_signing_accepts_pe32_and_pe64_without_code_changes(self):
        for magic in (0x10b,0x20b):
            for padding in range(8):
                with self.subTest(magic=magic,padding=padding):
                    original=image(magic,padding);check.signing_only(original,signed(original))
    def test_rejects_changed_code(self):
        original=image();changed=bytearray(signed(original));changed[450]^=1
        with self.assertRaisesRegex(ValueError,'code/data'):check.signing_only(original,bytes(changed))
    def test_rejects_nonzero_alignment_padding(self):
        original=image();changed=bytearray(signed(original));changed[len(original)]=1
        with self.assertRaisesRegex(ValueError,'alignment'):check.signing_only(original,bytes(changed))
    def test_rejects_certificate_overlapping_original_payload(self):
        original=image();changed=bytearray(signed(original));security=check.pe_fields(original)[1]
        struct.pack_into('<I',changed,security,500)
        with self.assertRaisesRegex(ValueError,'appended'):check.signing_only(original,bytes(changed))
    def test_rejects_trailing_payload_after_certificate(self):
        original=image()
        with self.assertRaisesRegex(ValueError,'appended'):check.signing_only(original,signed(original)+b'extra')
    def test_rejects_replacing_existing_vendor_signature(self):
        original=signed(image())
        with self.assertRaisesRegex(ValueError,'originally unsigned'):check.signing_only(original,original)
    def test_rejects_invalid_certificate_header(self):
        original=image();changed=bytearray(signed(original));offset=check.pe_fields(changed)[2]
        struct.pack_into('<H',changed,offset+6,1)
        with self.assertRaisesRegex(ValueError,'WIN_CERTIFICATE'):check.signing_only(original,bytes(changed))
    def test_rejects_malformed_pe_headers(self):
        for data in (b'',b'MZ',b'not PE',bytes(512)):
            with self.subTest(data=data[:4]),self.assertRaises(ValueError):check.pe_fields(data)
    def test_package_comparison_preserves_other_files_and_vendor_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            a=pathlib.Path(folder)/'source';b=pathlib.Path(folder)/'signed';a.mkdir();b.mkdir()
            original=image()
            for root,payload in ((a,original),(b,signed(original))):
                (root/'dependency.pyd').write_bytes(payload);(root/'vendor.dll').write_bytes(b'unchanged vendor');(root/'LICENSE').write_text('notice')
            self.assertEqual(check.compare(a,b),['dependency.pyd'])
            (b/'LICENSE').write_text('changed')
            with self.assertRaisesRegex(ValueError,'Non-PE'):check.compare(a,b)
    def test_package_comparison_rejects_added_or_removed_files(self):
        with tempfile.TemporaryDirectory() as folder:
            a=pathlib.Path(folder)/'a';b=pathlib.Path(folder)/'b';a.mkdir();b.mkdir()
            for root in (a,b):(root/'same.dll').write_bytes(image())
            (a/'missing').write_text('x')
            with self.assertRaisesRegex(ValueError,'file list'):check.compare(a,b)


class SigningInputTests(unittest.TestCase):
    def cli(self,source,target):
        return subprocess.run([sys.executable,str(pathlib.Path(check.__file__)), '--source',str(source),'--target',str(target)],capture_output=True,text=True,timeout=10)
    def test_missing_inputs_fail_closed_in_api_and_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder);valid=root/'valid';valid.mkdir();(valid/'payload.dll').write_bytes(image())
            missing=root/'missing'
            for source,target in ((missing,missing),(missing,valid),(valid,missing)):
                with self.subTest(source=source,target=target):
                    with self.assertRaisesRegex(ValueError,'missing or not a directory'):check.compare(source,target)
                    result=self.cli(source,target)
                    self.assertNotEqual(result.returncode,0);self.assertNotIn('passed',result.stdout);self.assertIn('missing or not a directory',result.stderr)
    def test_file_inputs_fail_closed_in_api_and_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder);valid=root/'valid';valid.mkdir();(valid/'payload.dll').write_bytes(image());file=root/'file';file.write_text('not a directory')
            for source,target in ((file,file),(file,valid),(valid,file)):
                with self.subTest(source=source,target=target):
                    with self.assertRaisesRegex(ValueError,'not a directory'):check.compare(source,target)
                    result=self.cli(source,target);self.assertNotEqual(result.returncode,0);self.assertNotIn('passed',result.stdout)
    def test_empty_inputs_fail_closed_in_api_and_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder);valid=root/'valid';valid.mkdir();(valid/'payload.dll').write_bytes(image());empty=root/'empty';(empty/'nested').mkdir(parents=True)
            for source,target in ((empty,empty),(empty,valid),(valid,empty)):
                with self.subTest(source=source,target=target):
                    with self.assertRaisesRegex(ValueError,'empty'):check.compare(source,target)
                    result=self.cli(source,target);self.assertNotEqual(result.returncode,0);self.assertNotIn('passed',result.stdout);self.assertIn('empty',result.stderr)
    def test_cli_accepts_nonempty_identical_and_signing_only_packages(self):
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder);a=root/'a';b=root/'b';a.mkdir();b.mkdir();original=image()
            for path in (a,b):(path/'payload.dll').write_bytes(original)
            self.assertEqual(check.compare(a,b),[]);self.assertEqual(self.cli(a,b).returncode,0)
            (b/'payload.dll').write_bytes(signed(original))
            self.assertEqual(check.compare(a,b),['payload.dll']);self.assertEqual(self.cli(a,b).returncode,0)


@unittest.skipUnless(os.name=='nt','Windows PowerShell provider semantics')
class SigningOutputPathTests(unittest.TestCase):
    def run_case(self,case):
        # Invoke the actual workflow without -Sign. Mock only provenance/signature
        # providers; forbid audit execution on guard failures. No Azure or app runs.
        workflow=pathlib.Path(__file__).resolve().parents[1]/'scripts/sign-windows.ps1'
        with tempfile.TemporaryDirectory() as folder:
            root=pathlib.Path(folder);ps=root/'ps-location';net=root/'net-location';ps.mkdir();net.mkdir()
            package=ps/'package';package.mkdir();(package/'vendor.dll').write_bytes(b'offline fixture');(ps/'existing-output').mkdir()
            script=root/'test.ps1'
            script.write_text(PS_PATH_CASE,encoding='utf-8-sig')
            shells=[shutil.which('powershell.exe'),shutil.which('pwsh.exe')]
            self.assertTrue(shells[0],'Windows PowerShell is required for this regression')
            for shell in dict.fromkeys(s for s in shells if s):
                result=subprocess.run([shell,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),str(workflow),str(ps),str(net),case],capture_output=True,text=True,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                report=json.loads(result.stdout)
                self.assertEqual(report['audit_called'],case in ('relative','absolute'))
                if case in ('relative','absolute'):self.assertEqual(pathlib.Path(report['output']),ps/'new-output')
                self.assertFalse((ps/'new-output').exists());self.assertFalse((net/'new-output').exists())
                self.assertFalse((package/'child').exists());self.assertFalse((package/'missing').exists())
                self.assertEqual((package/'vendor.dll').read_bytes(),b'offline fixture')
            # Remove only our junction links, never their target directories.
            for name in ('package-alias','location-alias','outside-alias'):
                alias=ps/name
                if alias.is_junction():
                    self.assertTrue(alias.resolve().is_relative_to(root.resolve()))
                    os.rmdir(alias)
    def test_relative_output_uses_active_powershell_location(self):self.run_case('relative')
    def test_existing_relative_output_is_rejected_before_audit(self):self.run_case('existing')
    def test_nested_relative_output_is_rejected_before_audit(self):self.run_case('nested')
    def test_nonfilesystem_output_is_rejected_before_audit(self):self.run_case('provider')
    def test_absolute_plain_output_remains_supported(self):self.run_case('absolute')
    def test_junction_output_parent_is_rejected_before_audit(self):self.run_case('junction-output')
    def test_junction_above_missing_output_parents_is_rejected(self):self.run_case('junction-deep')
    def test_junction_source_root_is_rejected_before_audit(self):self.run_case('junction-source')
    def test_junction_source_ancestor_is_rejected_before_audit(self):self.run_case('junction-source-parent')
    def test_junction_to_separate_output_tree_is_also_rejected(self):self.run_case('junction-outside')


PS_PATH_CASE=r"""
param($Workflow,$PsLocation,$NetLocation,$Case)
$ErrorActionPreference='Stop'
$env:PSModulePath=Join-Path $PSHOME 'Modules'
Import-Module Microsoft.PowerShell.Utility -ErrorAction Stop
Set-Location -LiteralPath $PsLocation
[Environment]::CurrentDirectory=$NetLocation
$global:audited=$false
function Invoke-AuditStub {$global:audited=$true;$global:LASTEXITCODE=0}
function Get-AuthenticodeSignature {param($LiteralPath) [pscustomobject]@{Status='Valid';SignerCertificate=[pscustomobject]@{Subject='Offline fixture'}}}
$outputPath='new-output'
$packagePath='./package'
$expectedError=$null
function New-ReviewJunction($Name,$Target) {
 $link=Join-Path $PsLocation $Name
 if(-not (Test-Path -LiteralPath $link)){New-Item -ItemType Junction -Path $link -Target $Target|Out-Null}
 return $link
}
if($Case -eq 'absolute'){$outputPath=Join-Path $PsLocation 'new-output'}
if($Case -in @('junction-output','junction-deep','junction-source')) {
 $alias=New-ReviewJunction 'package-alias' (Join-Path $PsLocation 'package')
 if($Case -eq 'junction-source'){$packagePath=$alias}
 elseif($Case -eq 'junction-deep'){$outputPath=Join-Path $alias 'missing/child'}
 else {$outputPath=Join-Path $alias 'child'}
 $expectedError='reparse points'
}
if($Case -eq 'junction-source-parent') {
 $alias=New-ReviewJunction 'location-alias' $PsLocation
 $packagePath=Join-Path $alias 'package';$expectedError='reparse points'
}
if($Case -eq 'junction-outside') {
 $alias=New-ReviewJunction 'outside-alias' $NetLocation
 $outputPath=Join-Path $alias 'new-output';$expectedError='reparse points'
}
if($Case -eq 'existing'){$outputPath='existing-output';$expectedError='existing candidates'}
if($Case -eq 'nested'){$outputPath='package/child';$expectedError='outside the source'}
if($Case -eq 'provider'){$outputPath='HKCU:\Software\KPAOfflineReview';$expectedError='FileSystem provider'}
try {
 $raw=& $Workflow -Package $packagePath -Toc 'unused' -Output $outputPath -Python 'Invoke-AuditStub'
 if($expectedError){throw 'Expected output guard rejection'}
 $plan=$raw|ConvertFrom-Json
 if($plan.files.Count -ne 1 -or $plan.files[0].action -ne 'preserve'){throw 'Unexpected offline plan'}
 if(-not $global:audited){throw 'Valid plan did not audit'}
 [ordered]@{output=$plan.output;audit_called=$global:audited}|ConvertTo-Json -Compress
} catch {
 if(-not $expectedError -or $_.Exception.Message -notlike ('*'+$expectedError+'*')){throw}
 if($global:audited){throw 'Output rejection occurred after audit'}
 [ordered]@{output=$null;audit_called=$global:audited}|ConvertTo-Json -Compress
}
"""


if __name__=='__main__':unittest.main()
