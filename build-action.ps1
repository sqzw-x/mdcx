$env:PYTHONPATH = "$PWD\src"

$FileName = "MDCx-windows-x86_64.exe"
Write-Output "Output File: $FileName"

python -m PyInstaller -n "$FileName" -F `
-i resources/Img/MDCx.ico `
-w main.py `
-p "./src" `
--add-data "resources;resources" `
--add-data "libs;." `
--hidden-import socks `
--hidden-import urllib3 `
--hidden-import _cffi_backend `
--collect-all curl_cffi

Write-Output 'Done'