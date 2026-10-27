$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
& ./.venv/Scripts/python.exe -B -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Python regressions failed' }
Get-ChildItem -LiteralPath tests -Filter *.cjs | ForEach-Object {
    & node $_.FullName
    if ($LASTEXITCODE -ne 0) { throw "JavaScript suite failed: $($_.Name)" }
}
