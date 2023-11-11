$time = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

$FileName = "MDCx-$time.exe"
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