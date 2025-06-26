time=$(date +"%Y-%m-%d_%H-%M-%S")

FileName="MDCx-$time.exe"
echo "Output File: $FileName"

pyi-makespec -n "$FileName" -F \
-i resources/Img/MDCx.ico \
-w main.py \
-p "./src" \
--add-data "resources:resources" \
--add-data "libs:." \
--hidden-import socks \
--hidden-import urllib3 \
--hidden-import _cffi_backend \
--collect-all curl_cffi

rm -rf dist

pyinstaller "$FileName.spec"

rm -rf build
rm -f "$FileName.spec"

echo 'Done'