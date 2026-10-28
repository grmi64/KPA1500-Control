# KPA1500 Control — Windows candidate validation

Prepared October 27, 2026. Local release preparation only; not published.

## Exact candidate

- Source: `51c310629a460d3e4a927ced1ac77955e6b05367` (main after PR #6).
- Application: 0.1.25, build 26; Windows numeric version 0.1.25.26.
- Package: `KPA1500-Control-0.1.25-build26-main-51c3106-Windows-x64-signed.zip` in `dist/windows/`.
- Product: KPA1500 Control; executable: `KPA1500 Control.exe`.
- Publisher: Gregory Miller. Authenticode status Valid; Microsoft timestamp verified.
- SignTool `/pa /all /v /tw`: one verified signature, zero warnings/errors.
- Prerelease flag remains enabled. Signing does not approve publication.
- Requirements: Windows 11 x64 and Microsoft Edge WebView2 Evergreen Runtime. Python/Node are not required on the user's PC.
- MIT application license; separately licensed bundled components retain their notices.

Checksums are in [WINDOWS-CANDIDATE-SHA256SUMS.txt](WINDOWS-CANDIDATE-SHA256SUMS.txt).
The machine-readable artifact record is [WINDOWS-CANDIDATE.json](WINDOWS-CANDIDATE.json).
Installation and release notes are in [WINDOWS-RELEASE-NOTES.md](WINDOWS-RELEASE-NOTES.md).

## Checksum and manifest path bases

Two record layouts are provided. Each JSON record declares its `record_layout`
and `artifact_path_base`; paths resolve from the directory containing that JSON,
not from an arbitrary caller's working directory.

- **Repository records:** root WINDOWS-CANDIDATE.json and
  WINDOWS-CANDIDATE-SHA256SUMS.txt use repository-relative `dist/windows/...`
  paths. Their base directory is the repository root containing these files.
- **Standalone companion records:** the copies inside
  `dist/windows/KPA1500-release-docs-main-51c3106/` use `../...` paths. Their base
  directory is that companion folder. Keep it beside the signed ZIP and the
  extracted `KPA1500 Control/` directory in the same parent directory. Moving
  that parent, with its contents together, preserves the relative layout.

For a checksum tool that resolves entries from its current working directory,
first change to the directory containing the selected checksum file. For a JSON
consumer, use `manifest_directory / artifact_path_base.relative_directory /
artifact.path`. Do not interchange the repository and companion checksum files.
The ZIP checksum can be checked before extraction; the EXE, config and two
license entries require the extracted application directory. In Explorer Extract
All, choose the directory containing the ZIP as the destination for this
standalone layout, rather than the default additional ZIP-named subfolder. The
archive already contains the `KPA1500 Control/` top-level directory.

## Completed checks and their scope

| Check | Result / scope |
| --- | --- |
| Production build and package audits | Passed on main 51c3106: metadata, icon payloads, prerelease flag, EXE-specific CLR config, both application licenses, 57 pinned notice/source files and frozen dependency mappings. |
| Signing | Valid Gregory Miller signature and Microsoft timestamp verified on the exact final EXE. |
| Offline downloaded-file shell launch | Passed on the exact final signed ZIP in a fresh network-disabled Sandbox. A synthetic Internet-zone marker was placed on the ZIP; Explorer Extract All propagated it to EXE, managed DLL and config. Shell launch with explicit simulation arguments reached live simulation, sharing/auto-connect false. Checked markers remained in this run. |
| Internet-enabled Explorer launch | Same final ZIP; one active adapter and Microsoft HTTPS status 200. Guest signature Valid with timestamp. Explorer double-click reached default Simulation. Agent and user observed no SmartScreen warning. |
| Internet-enabled harness limitation | The post-launch EXE Zone.Identifier stream was absent. The harness marked that evidence check failed after simulation readiness had passed. No test action unblocked files or changed security settings. Cause of stream disappearance is not established; retain this qualification. |
| Standard-user clean guest | Passed on final ZIP: non-administrator token, read-only app folder, EXE/config hashes verified, no active adapters or installed Python/Node. Both first-launch and reopen smoke processes exited 0. Preferences, including close-during-save, persisted in the test user's LocalAppData. Normal per-user simulation launch passed. |
| Missing WebView2 and recovery | Passed on final ZIP in a fresh network-disabled guest. Process-local empty-runtime override confirmed unavailable; user observed the expected guidance dialog. No listener, child process or instance metadata started; exit 1 after OK. Removing only the override restored the same installed runtime (156.0.4314.42); offline simulation recovery/close smoke exited 0 with no test app processes remaining. Host runtime and registry were not changed. |
| Frozen simulation coverage | Final standard-user and recovery smoke reports cover Full/Compact, appearance, stay-on-top, simulated controls/tuning/RF/power, instance activation, preferences, discovery simulation, stale/error guards, abrupt simulator-reader recovery, maximized view restoration and close during pending save. All remain simulation-only. |
| Windows source regressions | Reviewed PR #6 source: 190 total Python tests, 188 passed/two expected platform skips; three config regressions; all 12 JavaScript suites. Final targeted review/config audit and portable import check passed. Source tests were recorded against the reviewed change incorporated into 51c3106; these are distinct from final-ZIP acceptance. |
| Mac compatibility | Mac agent reported exact PR #6 commit 24b8bc7bb6a7913b5772969fa6c351c293bdc3f7: 183 Python passed/seven expected skips, all three config tests, 12 JavaScript suites, Swift placement and diff checks passed; 66 production fingerprints and geometry unchanged. No Mac build/launch was repeated for this Windows-only scope. |

Downloaded-file marking was synthetic, not a real public browser download. No-warning observations on one guest do not guarantee SmartScreen behavior on every PC or prove which reputation-service requests were made. The Internet-enabled observation is historical evidence; this documentation consolidation used no network or app activity.

## Remaining acceptance and release decisions

- **Physical multiple-monitor testing: pending.** Do not mark it passed or implied by DPI/mocked tests.
- **Final signed-package hardware acceptance: pending.** Earlier USB/Ethernet source-host results remain historical evidence for their own versions/harnesses. They are not acceptance of this exact ZIP. Hardware work requires separate authorization.
- **Distribution route and public release approval: pending.** This candidate remains prerelease. Version/prerelease designation must be reviewed before public release.
- **Microsoft Store identity, MSIX/WACK and Store policy/listing acceptance: not performed for KPA1500.** OM Power Control's identity and Store results do not apply to KPA1500.
- **Support and data-handling text finalized locally.** The owner selected this repository's GitHub Issues as the support channel, without a personal email listing. WINDOWS-INSTALL.md, WINDOWS-SUPPORT.md and WINDOWS-DATA-HANDLING.md hold the finalized local text. A public privacy-policy URL and publication remain pending.
- **Distribution-document synchronization:** source documentation was consolidated after the tested ZIP was created. The immutable ZIP contains its original build-time documentation, including historical unsigned/development wording. Use this report for current signing/test status. Before release, reconcile the docs shipped to users; any regenerated ZIP needs new checksums and artifact-specific validation rather than reusing this ZIP's hash.

## Evidence and artifact preservation

Private local evidence is under `.tmp/main-51c3106/`: `signature.json`, `signature-verify.log`, `download-shell-result.json`, `online-smartscreen-result.json`, `standard-user-result.json` and `missing-webview2-result.json`. Raw mapped guest reports remain in the local OM workspace's `.tmp/kpa-main-51c3106-*` fixtures. These logs/harnesses are not release contents or committed credentials.

The signed EXE and ZIP were not rebuilt, re-signed, unblocked or modified during consolidation. Application runtime, shared/Mac code, dependencies and version are unchanged. No hardware connection or publication was performed.
