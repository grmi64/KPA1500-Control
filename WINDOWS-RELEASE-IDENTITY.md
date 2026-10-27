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
| PE release status | Prerelease/development candidate |
| Signing/publication | Final candidate from main 51c3106 signed as Gregory Miller; not published. See WINDOWS-RELEASE-CANDIDATE.md. |
| Microsoft Store package identity | Not reserved or assigned by this step |

Sources/version.py remains the authoritative shared version; no Mac version, bundle identifier or build script changes are made. A Windows version-resource generator derives the four numeric components from VERSION and BUILD, validates their 16-bit range, and supplies FileDescription, OriginalFilename, CompanyName, copyright and product fields. File metadata attribution is not a code-signing certificate identity or Store publisher assignment.

The ordinary scripts/build-windows.ps1 command retains the review output. Use scripts/build-windows.ps1 -ProductionIdentity to build the production-named candidate separately. Both embed the existing ICO and generated version resource, retain the existing asInvoker/PerMonitorV2 manifest, bundle LICENSE and third-party notices, and run the notice and executable identity audits. The production-named candidate still starts in Simulation; its name does not enable a hardware session or confer release approval.

The ICO contains 16, 24, 32, 48, 64, 128 and 256 pixel entries; no new artwork was generated. Windows PE inspection verifies version strings/numeric fields, icon resources and the prerelease flag without executing the app. The license audit rejects a missing or altered application LICENSE in either packaged location.

This is local release preparation. The candidate at main 51c3106 has been signed and ZIP-packaged; Store reservation/MSIX identity, release-version approval and publication remain separate steps. The prerelease flag and development-candidate metadata must be reviewed when an actual public release is prepared. No public Store name, publisher identifier or package-family name is invented here.

Physical multiple-monitor acceptance and hardware-enabled packaged acceptance remain pending. Earlier binary acceptance belongs to its own hashes; current final-ZIP simulation, standard-user, runtime and shell-launch evidence is consolidated in WINDOWS-RELEASE-CANDIDATE.md.
