# KPA1500 Control — accepted Windows Preview package

Accepted merge: `a400cfe04a09ac7c007186b0c7c1ab0d164b50cf` ([PR #20](https://github.com/grmi64/KPA1500-Control/pull/20)). Application **0.1.25/build 26, Windows Preview**, numeric Windows version 0.1.25.26; prerelease flag retained. Portable ZIP first; Microsoft Store deferred.

- ZIP: `KPA1500-Control-0.1.25-build26-startup-a400cfe-Windows-x64-signed.zip`.
- ZIP SHA256: `09d4796044eff347e55499d91c2faab503fcfccba9411f76f1f39387db608ddd`.
- EXE SHA256: `a719fd27942cb83f4534c2f8a9191016701085b9d4a9d4539498981d32a48e27`.
- Evidence: [full acceptance report](dist/windows/startup-a400cfe-2026-10-30/FULL-ACCEPTANCE.txt), [structured results](dist/windows/startup-a400cfe-2026-10-30/FULL-ACCEPTANCE.json), [current manifest](WINDOWS-CANDIDATE.json), and [checksums](WINDOWS-CANDIDATE-SHA256SUMS.txt).

Evidence links under `dist/windows/` refer to preserved local acceptance files; those artifacts are not committed or uploaded by this documentation PR.

## Completed acceptance

Full functional acceptance passed October 30, 2026 on the exact signed merge executable. USB monitoring through a hub passed 600.015 seconds (2,305 snapshots, zero anomalies); Ethernet passed 300 seconds (1,152 snapshots, zero anomalies). USB/TCP mode and ATU controls, physical USB power off/on, cable-loss ERROR with cleared readings, explicit reconnect without operating-request replay, Tune/Cancel and RF-backed tuning passed. The operator confirmed app/panel agreement at about 550 W and SWR 1.10, then RF off and Standby. The operator alone supplied and stopped RF.

Two physical displays passed Compact/Full/maximize transitions, two normal monitor-2 reopens, missing-monitor recovery to the primary display, and reconnect/reopen at the recovered primary position. All private acceptance readers/windows closed; no exact-candidate processes remain.

All 237 payload files and ZIP hash remained unchanged. All 78 native signatures were verified (seven newly signed, vendor signatures preserved), with a valid timestamped Gregory Miller signature and signing-only code/data comparison. The clean merge archive's 177 source files and 23 frozen project modules were verified. Two exact signed Simulation smoke runs passed 19 checks each, including six pre-native authenticated activation requests. Earlier 20-startup-test evidence belongs to the reviewed-source candidate; it is supporting evidence, not a new 20-run test of this merge binary. No configured CI checks/runs were reported; no CI pass is claimed.

## Scope and remaining release work

This acceptance covers the recorded Windows laptop, USB hub/FTDI COM3 at 230400 baud, amplifier 01427/FW 03.06, Ethernet 192.168.0.18:1500 and two displays. It does not establish every hub/driver/RF power level or eliminate every possible intermittent fault. The original offline Simulation WinError 6 cause remains unproven; the reviewed bounded startup-only recovery was not needed here. The native sizing stall was reproduced and fixed through managed property dispatch. A missing-window-metadata USB-loss recorder preflight stopped before any hardware command; the subsequent recorded run passed after reopening the private windows.

Nothing was installed or published. Publication authorization, Store identity/MSIX/WACK/certification and public privacy-policy hosting remain separate. Earlier clean-PC, missing-WebView2, marked-file/SmartScreen and private MSIX results retain their historical package attribution. These repository records were updated after acceptance; the tested ZIP and its bundled build-time documents remain unchanged.

## Historical package records

The following reports preserve their original dates, package hashes and then-pending gates. References to current unversioned repository records now resolve to the October 30 accepted package; they do not verify an older archive.

# KPA1500 Control - corrected documentation repackage r2

Prepared October 27, 2026. Documentation base is main 8de93370c3eea153866e17a3601fa8f08905ff55 with uncommitted r2 review corrections. Runtime/build remains 9efe8c119c0655333e52d4078f43b18f4675cdcc. No rebuild/signing or hardware/publication occurred.

Current ZIP: `KPA1500-Control-0.1.25-build26-docs-8de9337-r2-Windows-x64-signed.zip`, SHA256 `5ef5a7ccb57434e7e7a3389339e64f096acee34806f60252a8d82d34abf71c00`, 14232242 bytes. It contains 242 files. Only the bundled identity and validation report differ from r1; all 240 other files, including the signed EXE, all 78 PE files, configuration, licenses and notices, are byte-for-byte unchanged. All signature-receipt output hashes match. Earlier archives and receipts are preserved.

The historical report links below are explicitly current-archive links and do not verify the older ZIP. Identity text now distinguishes earlier runtime/security tests from each repackage's own offline checks. Current [manifest](WINDOWS-CANDIDATE.json) and [checksums](WINDOWS-CANDIDATE-SHA256SUMS.txt) resolve from their containing directory; standalone copies use their declared ../ sibling layout. R2 offline checks passed: 18 artifact hash/size/path checks across repository, standalone and relocated layouts; 63 external and 25 bundled local links. In a fresh network-disabled Sandbox, all 242 extracted file hashes matched and all 78 signatures were Valid with Application Control state 1. A standard user with a read-only app folder passed first-launch/reopen (18 simulation checks each, exit 0), preference close/save and normal Simulation launch; no Python/Node installation was present. The user confirmed Full and Compact views look correct with simulator badge and warning visible. These results apply to the r2 hash above; no fresh missing-runtime, marked-file/SmartScreen or MSIX matrix is claimed for r2. Physical multiple-monitor and final signed-package hardware tests remain pending. No earlier test result is relabeled as r2 acceptance.

## Approved version and distribution decision (October 28, 2026)

The owner approved version 0.1.25, build 26 (numeric Windows version 0.1.25.26) as **Windows Preview**, retaining the existing prerelease flag. Distribution will start with the portable ZIP; Microsoft Store is deferred. This decision preserves the exact signed r2 EXE/ZIP and does not authorize publication or hardware activity. No rebuild, signing or repackaging is needed to retain the existing version/flag. This external record is newer than the immutable bundled documentation; no new archive content or test result is implied. Physical multiple-monitor and final signed-package hardware acceptance remain pending. Historical decision statements below retain their earlier context.

## R2 packaged mode-switching acceptance

Test performed October 27, 2026; recorded October 28, 2026 against the unchanged r2 ZIP hash above. The exact package completed Simulation -> Read-only telemetry -> Hardware control -> Simulation through its native UI in a fresh network-disabled Sandbox. All three handoff confirmations were observed and accepted. USB was selected without a COM port; Connect, discovery and equipment controls were not clicked.

Both hardware modes started and remained disconnected, with blank readings, no reader, no actions, no discovery activity, and auto-connect/sharing off in 325 read-only loopback observations across the sequence. Their notices remained visible in Full and Compact; visible equipment controls were disabled in Compact. Actual close/reopen without a mode flag returned to live Simulation. The observer finished and the guest app was left in Simulation. No independent wire audit was performed; the guest had no active network adapter and no usable USB endpoint was configured. This is disconnected mode-handoff acceptance, not hardware acceptance.

All six external artifact hashes remained unchanged. Source/runtime and signed EXE/ZIP were not modified by the test. Private execution evidence is under `.tmp/r2-mode-switching/`. This recording changes external documentation/data only; it does not alter bundled documents, repackage, rerun the app, connect hardware, commit or publish. Physical multiple-monitor and final signed-package hardware acceptance remain pending.

## Previous documentation repackage r1 - historical artifact

The following r1 report and test results belong to ZIP SHA256 953e29bcf8310dc5597074f446a2f9683ec2f36a57b488b42e00f70f30b4c28b, not r2. Its links to unversioned external records now track the current r2 candidate.

# KPA1500 Control - documentation-reconciled Windows candidate

Prepared October 27, 2026. PR #11 merged as 8de93370c3eea153866e17a3601fa8f08905ff55 after Windows and Mac review at 9452e13. Runtime/build source remains 9efe8c119c0655333e52d4078f43b18f4675cdcc; no rebuild or signing was required.

New ZIP: `KPA1500-Control-0.1.25-build26-docs-8de9337-Windows-x64-signed.zip`. SHA256 `953e29bcf8310dc5597074f446a2f9683ec2f36a57b488b42e00f70f30b4c28b`; 14231855 bytes. It contains 242 files. Four existing documents were changed and two documents added; all other 236 original files are unchanged. All 78 PE receipt hashes match, including EXE SHA256 `f9348de5b08addc2b1abbe51f91289f32911bc7d9db78539429aa88a3d807e06`. Config, licenses and third-party notices are unchanged. Original ZIP/receipt are retained.

All 25 bundled local Markdown links resolve. Bundled validation/release notes now exist; README, installation, support and identity text agree with this documentation-only package. The archive cannot contain its own hash: use the external [manifest](WINDOWS-CANDIDATE.json) and [checksums](WINDOWS-CANDIDATE-SHA256SUMS.txt), with paths based at their containing directory. Standalone companion records use their declared ../ sibling layout. New-archive offline Sandbox standard-user acceptance passed: every one of 242 extracted files matched; all 78 signatures Valid, Application Control state 1, no active adapters, non-admin token and read-only app folder. First-launch and reopen each passed 18 simulation checks and exited 0, including preferences/close-save; normal per-user launch reached Simulation. The user confirmed Full and Compact views look correct with simulator labeling visible. These new-archive results are separate from the historical tests below. No fresh missing-runtime, marked-file/SmartScreen or MSIX matrix was run on this new ZIP; those prior results remain attributed to the previous artifact.

Physical multiple-monitor and final signed-package hardware acceptance remain pending. No hardware or publication is authorized. Earlier SmartScreen and missing-runtime qualifications remain unchanged; no new security/reputation result is implied by byte preservation.

## Prior 9efe8c1 ZIP evidence - historical artifact

The following report applies to the original 240-file ZIP and its hashes. Its shipped-document reconciliation gate is addressed by the new package above, but its native/security test results remain attributed to that original ZIP.

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

Current-archive records only: [checksums](WINDOWS-CANDIDATE-SHA256SUMS.txt), [manifest](WINDOWS-CANDIDATE.json), and [user notes](WINDOWS-RELEASE-NOTES.md). These links track the current repackage, not this historical ZIP. For the original artifact use the explicit ZIP hash below and the manifest's previous_candidate records; do not verify the historical ZIP against the current checksum-file ZIP entry.

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
