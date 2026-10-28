# KPA1500 Control - Windows candidate validation

Prepared October 27, 2026. Local release preparation only; not published.

## Exact candidate

- Runtime/build source: `9efe8c119c0655333e52d4078f43b18f4675cdcc` (main after PR #10).
- Application 0.1.25, build 26; Windows numeric version 0.1.25.26, x64.
- Package: `KPA1500-Control-0.1.25-build26-main-9efe8c1-Windows-x64-signed.zip` in `dist/windows/`.
- Product: KPA1500 Control; executable: `KPA1500 Control.exe`.
- Complete payload signed: EXE and six dependencies newly signed as Gregory Miller; 71 existing vendor signatures preserved. All 78 PE files verified; Microsoft timestamps checked. SignTool reported zero warnings/errors.
- Prerelease flag remains enabled. Signing and this report do not approve publication.
- Requirements: Windows 11 x64 and Microsoft Edge WebView2 Evergreen Runtime. No separate Python/Node installation is needed.
- MIT application license; third-party components retain their own notices and attribution.

Checksums: [WINDOWS-CANDIDATE-SHA256SUMS.txt](WINDOWS-CANDIDATE-SHA256SUMS.txt).
Machine-readable record: [WINDOWS-CANDIDATE.json](WINDOWS-CANDIDATE.json).
User notes: [WINDOWS-RELEASE-NOTES.md](WINDOWS-RELEASE-NOTES.md).

ZIP SHA256: `34ca808bb10c72be73395368681eeaa8a677c1d7d8b8b61537be476d47a6b490`.
EXE SHA256: `f9348de5b08addc2b1abbe51f91289f32911bc7d9db78539429aa88a3d807e06`.
The exact 240 ZIP entries match the local application files byte-for-byte. All 78 signature-receipt output hashes match those files.

## Checksum and manifest path bases

Each JSON declares `record_layout` and `artifact_path_base`. Resolve paths from the directory containing the selected JSON, not an arbitrary working directory.

- **Repository records:** root JSON and checksum file use `dist/windows/...` paths, based at the repository root containing those records.
- **Standalone companion records:** copies in `dist/windows/KPA1500-release-docs-main-9efe8c1/` use `../...` paths, based at that companion directory. Keep the companion directory beside the ZIP, external signature receipt and extracted `KPA1500 Control/` folder. Moving that parent and its contents together preserves the layout.

Run checksum tools from the directory containing the selected checksum file. JSON consumers use `manifest_directory / artifact_path_base.relative_directory / artifact.path`. Do not interchange the two layouts. All six checksum entries must agree with their paired JSON record.

The ZIP and external signature receipt can be checked before extraction; EXE, config and two license entries require the extracted application directory. In Explorer Extract All, choose the directory containing the ZIP rather than an extra ZIP-named subdirectory: the archive already contains `KPA1500 Control/`. Receipt entries themselves are relative to that extracted app directory. A receipt records provenance and signatures; it is not a substitute for ZIP verification, Windows trust checks or the pre/post-sign byte comparison.

## Completed checks and exact scope

| Check | Result / scope |
| --- | --- |
| Build and provenance | Main 9efe8c1 build passed metadata, icons, prerelease, EXE config, both application licenses, 57 pinned notice/source files and frozen dependency mappings. |
| Complete-payload signing | Seven new signatures and 71 preserved signatures; all 78 verified. Byte comparison permits only appended PE certificates, security-directory entry, alignment and checksum changes. The pinned inventory remains the pre-sign vendor inventory; post-sign raw hashes intentionally differ for signed files. |
| Offline private MSIX/portable | Eight cases passed: both mixed orders, same-format duplicates, private/ordinary saved settings and fresh profiles. Stable identities, duplicate activation without a second backend, unchanged settings and owner-death/handoff startup recovery passed. Application Control enforced, zero active adapters, all 78 signatures Valid. Private proof package removed. |
| Separate clean packaged smoke/reopen | First-launch and reopen each passed 18 checks, exit 0. These are distinct from the matrix's deliberate owner-process termination. |
| Harness retry qualification | An initial guest stopped on a test-helper cleanup error. Its evidence is retained; the corrected helper and unchanged signed inputs passed a complete fresh rerun. It is not relabeled as a production startup failure or a passing first attempt. |
| Final-ZIP standard user | Passed with non-admin account/token, read-only app folder, own-profile preferences/close-save, first/reopen exit 0 and default Simulation launch. No Python/Node installation, zero active adapters, enforced Application Control and 78 valid signatures. |
| Missing WebView2 / recovery | Reversible process-local empty-runtime override exercised the failure path while the real runtime remained installed. User confirmed the guidance dialog; the harness observed no backend/listener/activation metadata. That first guest was closed before exit/recovery. A separate fresh repeat used existing smoke mode to suppress the duplicate dialog, verified exit 1, restored the same runtime (156.0.4314.42), then passed 18 recovery checks on the same profile, exit 0, no app left running. No runtime uninstall or registry change. |
| Offline marked-file Explorer launch | User double-click reached live Simulation with no warning reported. ZIP and all 240 extracted files received synthetic ZoneId=3 markers; all remained after launch. Zero active adapters, 78 valid signatures, Application Control enforced; sharing/auto-connect false. |
| Internet-enabled Explorer observation | Same exact ZIP and markers; one active adapter and Microsoft HTTPS status 200. User explicitly reported no warning and Simulation opened. All 240 markers plus ZIP marker remained; EXE hash unchanged. No security-policy changes or warning bypass. A SmartScreen cloud request/verdict was not independently captured. |
| Windows source regressions | Main 9efe8c1: 242 Python tests, 240 passed/two expected Windows skips (POSIX pseudo-terminal and SIGTERM semantics); all 12 JavaScript suites passed. Includes 24 signing regressions; actual path/junction cases ran in both Windows PowerShell 5.1 and PowerShell 7. |
| Reported Mac compatibility | Exact PR #10 commit 5a077fe904d619a570036028f81e9d77ecdedcac: 218 Python passed/24 expected skips, all 14 portable signing tests passed and 10 Windows-only signing tests skipped; 12 JavaScript suites, Swift placement and whitespace checks passed. All 66 production fingerprints and decoded geometry unchanged. No Mac rebuild/app launch was required for the four-file tooling/test/doc scope; Windows signature/junction behavior was not independently verified on Mac. |

The packaged smoke checks cover Full/Compact and maximized restoration, appearance/stay-on-top, preferences/close during save, duplicate activation, simulated controls/tuning/RF/power/discovery and reader failure/recovery guards. These are simulation checks, not equipment commands or physical multiple-monitor acceptance.

Marked-file extraction used Expand-Archive followed by explicit markers on every extracted file. Neither marked-file run was an actual browser download or a test of Explorer's marker propagation. No-warning results describe these guests, not a guarantee for every PC or proof of a positive cloud reputation verdict. The old 51c3106 Internet-run marker-loss qualification belongs only to that older artifact; the current two runs verified all 240 markers remained.

## Remaining acceptance and release work

- **Physical multiple-monitor testing: pending.** DPI/mocked/single-display tests do not establish it.
- **Final signed-package hardware acceptance: pending.** Earlier USB/Ethernet source-host results remain historical for their own versions/harnesses. They are not acceptance of this exact ZIP. Hardware work requires separate authorization; the operator controls RF/drive and the app must not key the radio or adjust drive power.
- **Public release approval, distribution route and release version/prerelease decision: pending.** No publication is authorized by this report.
- **Production Store identity/MSIX/WACK and Store certification/listing acceptance: pending.** Private non-Store MSIX feasibility was tested; it is not a production Store submission. OM Power Control's identity/results do not apply.
- **Support/privacy:** GitHub Issues is the approved support channel, without personal email. Installation/support/data-handling text is finalized locally. No public privacy-policy URL is assigned or published.
- **Shipped-document synchronization: pending before public release.** The immutable ZIP includes its build-time installation/support/data-handling text, README, licensing and release-identity file. Some embedded candidate pointers remain older than this consolidation. The archive does not contain this validation report/JSON/checksum set; relative links from its build-time installation/support text to the report are not self-contained. The external standalone companion supplies a current linked documentation set but does not rewrite links inside the extracted app folder. Do not silently replace files inside the tested ZIP. Any reviewed repackaging requires a new ZIP hash and artifact-specific checks, while preserving/rechecking the signed EXE as appropriate.

## Evidence and preservation

Private local evidence: `.tmp/main-9efe8c1/` (build, tests, sign log, signature receipt, pre-sign baseline, executed harness and guest results), `.tmp/main-9efe8c1-standard/`, `.tmp/main-9efe8c1-runtime/`, `.tmp/main-9efe8c1-download/` and `.tmp/main-9efe8c1-online-smartscreen/`. Mapped guest fixtures remain in the local OM workspace. They are private diagnostics, not release contents or committed credentials.

This consolidation changes local documentation/data only. It does not rebuild, re-sign, unblock or modify the tested EXE, ZIP, config, licenses or receipt. No network/app activity, hardware connection, commit, merge or publication was performed during consolidation. Tests above retain their original dates, artifacts and scope.
