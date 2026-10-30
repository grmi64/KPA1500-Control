# KPA1500 Windows release identity — accepted package

Accepted merge: `a400cfe04a09ac7c007186b0c7c1ab0d164b50cf` ([PR #20](https://github.com/grmi64/KPA1500-Control/pull/20)). Application **0.1.25/build 26, Windows Preview**, numeric Windows version 0.1.25.26; prerelease flag retained. Portable ZIP first; Microsoft Store deferred.

- ZIP: `KPA1500-Control-0.1.25-build26-startup-a400cfe-Windows-x64-signed.zip`.
- ZIP SHA256: `09d4796044eff347e55499d91c2faab503fcfccba9411f76f1f39387db608ddd`.
- EXE SHA256: `a719fd27942cb83f4534c2f8a9191016701085b9d4a9d4539498981d32a48e27`.
- Evidence: [full acceptance report](dist/windows/startup-a400cfe-2026-10-30/FULL-ACCEPTANCE.txt), [structured results](dist/windows/startup-a400cfe-2026-10-30/FULL-ACCEPTANCE.json), [current manifest](WINDOWS-CANDIDATE.json), and [checksums](WINDOWS-CANDIDATE-SHA256SUMS.txt).

Evidence links under `dist/windows/` refer to preserved local acceptance files; those artifacts are not committed or uploaded by this documentation PR.

Publisher: `CN=Gregory Miller, O=Gregory Miller, L=American Canyon, S=ca, C=US`. All 78 native signatures verified; seven newly signed and 71 vendor signatures preserved. The executable is `KPA1500 Control.exe`. Hardware and physical two-monitor acceptance passed; nothing installed or published.

Shared version metadata, production/review names, icon, manifest and license rules below are retained. Historical statements about an older current candidate or pending tests apply only to that earlier package.

## Historical identity and packaging decisions

# KPA1500 Windows release identity — local candidate

| Field | Value |
| --- | --- |
| Product/display name | KPA1500 Control |
| Production executable | KPA1500 Control.exe |
| Production output folder | dist/windows/KPA1500 Control/ |
| Review executable | KPA1500 Control Review.exe |
| Review output folder | dist/windows/KPA1500 Control Review/ |
| Application version | 0.1.25 |
| Shared build | 26 |
| Windows numeric file/product version | 0.1.25.26 |
| ProductVersion text | 0.1.25 |
| Developer/copyright attribution | Greg Miller (NY6C) |
| Internal executable name | KPA1500Control; KPA1500ControlReview for review builds |
| Icon | Existing project artwork, Assets/AppIcon.ico |
| Application license | MIT; root LICENSE |
| PE release status | Prerelease flag retained; Windows Preview approved October 28, 2026 |
| Approved distribution | Portable ZIP first; Microsoft Store deferred |
| Signing/publication | Final candidate from main 9efe8c1: complete payload signed/verified, 78 PE files; not published. See WINDOWS-RELEASE-CANDIDATE.md. |
| Microsoft Store package identity | Not reserved or assigned by this step |

Sources/version.py remains the authoritative shared version; no Mac version, bundle identifier or build script changes are made. A Windows version-resource generator derives the four numeric components from VERSION and BUILD, validates their 16-bit range, and supplies FileDescription, OriginalFilename, CompanyName, copyright and product fields. File metadata attribution is not a code-signing certificate identity or Store publisher assignment.

The ordinary scripts/build-windows.ps1 command retains the review output. Use scripts/build-windows.ps1 -ProductionIdentity to build the production-named candidate separately. Both embed the existing ICO and generated version resource, retain the existing asInvoker/PerMonitorV2 manifest, bundle LICENSE and third-party notices, and run the notice and executable identity audits. The production-named candidate still starts in Simulation; its name does not enable a hardware session or confer release approval.

The ICO contains 16, 24, 32, 48, 64, 128 and 256 pixel entries; no new artwork was generated. Windows PE inspection verifies version strings/numeric fields, icon resources and the prerelease flag without executing the app. The license audit rejects a missing or altered application LICENSE in either packaged location.

This is local release preparation. The candidate at main 9efe8c1 has been rebuilt, completely signed and ZIP-packaged. Private non-Store MSIX/portable feasibility checks passed. Version 0.1.25/build 26 and the Windows Preview designation are owner-approved as of October 28, 2026, retaining the existing prerelease flag and metadata. Portable ZIP is the selected first distribution route; Microsoft Store is deferred. Production Store identity/MSIX/WACK and publication remain separate steps. No public Store name, publisher identifier or package-family name is invented here.

Physical multiple-monitor acceptance and final signed-package hardware acceptance remain pending. Runtime/missing-WebView2, marked-file/shell-launch, SmartScreen and private MSIX evidence belongs to the earlier 9efe8c1 ZIP. Each documentation-reconciled ZIP has its own separately recorded offline simulation, standard-user and reopen checks; earlier results must not be relabeled. Consult WINDOWS-RELEASE-CANDIDATE.md and the external manifest for exact archive hashes and test attribution.

Documentation-only repackage: main 8de93370c3eea153866e17a3601fa8f08905ff55. Runtime/build remains 9efe8c119c0655333e52d4078f43b18f4675cdcc. Signed PE files, config, licenses and third-party notices are preserved byte-for-byte. See the bundled [validation report](WINDOWS-RELEASE-CANDIDATE.md) and the external checksum records for the exact ZIP.

Documentation review correction r2: historical record links are explicitly labeled, and this identity wording separates earlier runtime/security tests from each repackage's own offline checks. Runtime/signatures remain unchanged; r2 checks are recorded externally after creation.

This approval is an external release decision and does not change the signed EXE, bundled files or r2 ZIP. No rebuild, signing, hardware access, commit or publication is performed by recording it. Physical multiple-monitor and final signed-package hardware acceptance remain pending.
