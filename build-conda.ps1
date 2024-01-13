conda activate mdcx-py
$time = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

# 即时构建, 可选后缀
$suffix = Read-Host -Prompt "Suffix(Optional)"
if ($suffix -ne "")
{
    $suffix = "-$suffix"
}
$FileName = "MDCx-$time$suffix.exe"

# 正式版
$release = Read-Host -Prompt "Release version(Optional)"
if ($release -ne "")
{
    $FileName = "MDCx-$release$suffix.exe"
}


Write-Output "Output File: $FileName"

pyi-makespec -n "$FileName" -F `
-i resources/Img/MDCx.ico `
-w main.py `
-p "./src" `
--add-data "resources;resources" `
--add-data "libs;." `
--hidden-import socks `
--hidden-import urllib3 `
--hidden-import _cffi_backend `
--collect-all curl_cffi

Remove-Item -Recurse -Force dist

pyinstaller "$FileName.spec"

Remove-Item -Recurse -Force build
Remove-Item -Force "$FileName.spec"

Write-Output 'Done'