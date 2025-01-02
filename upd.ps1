param (
    [string]$startDir = "."
)

Get-ChildItem -Path $startDir -Recurse -Filter *.py | ForEach-Object {
    Write-Output $_.FullName
    uv run pyupgrade $_.FullName --py39-plus
}