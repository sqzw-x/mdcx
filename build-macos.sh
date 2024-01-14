#/bin/bash

# Sample build script for pyinstaller

appName="MDCx"

pyi-makespec \
  --name MDCx \
  --osx-bundle-identifier com.mdcuniverse.mdcx \
  -F -w main.py \
  -p "./src" \
  --add-data "resources:resources" \
  --add-data "libs:." \
  --icon resources/Img/MDCx.icns \
  --hidden-import socks \
  --hidden-import urllib3 \
  --hidden-import _cffi_backend \
  --collect-all curl_cffi

rm -rf ./dist

pyinstaller MDCx.spec

rm -rf ./build
rm *.spec
