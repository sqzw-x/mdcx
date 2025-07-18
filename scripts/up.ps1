# pyupgrade **/*.py

$dirs = @("mdcx/models", "mdcx/controllers")
foreach ($d in $dirs) {
    Get-ChildItem -Path $d -Recurse -Filter *.py | ForEach-Object {
        Write-Output "pyupgrade $_"
        pyupgrade $_ --py39-plus
    }
}