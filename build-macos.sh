#/bin/bash

set -e

while [[ $# -gt 0 ]]
do
  key="$1"
  case $key in
    --version|-v)
      APP_VERSION="$2"
      shift
      shift
      ;;
    --create-dmg|-dmg)
      CREATE_DMG=true
      shift
      ;;
    --help|-h)
      echo "Usage: build-macos.sh [options]"
      echo "Options:"
      echo "  --version, -v       Specify the version number. \
      The value within config.ini.default file will be usded if not specified."
      echo "  --create-dmg, -dmg  Create DMG file. Default is false."
      exit 0
      ;;
    *)
      shift
      ;;
  esac
done


# 从配置文件获取应用版本
getAppVersionFromConfig () {
  local configPath="$1"
  if [[ -f "$configPath" ]]; then
    local version=$(cat $configPath | grep -oi 'version\s*=\s*[0-9]\+' | grep -oi '[0-9]\+$')
    echo $version
  else
    echo ''
  fi
}


# Check APP_VERSION
if [ -z "$APP_VERSION" ]; then
  echo "APP_VERSION is not set. Trying to get it from config.ini.default..."
  APP_VERSION=$(getAppVersionFromConfig "config.ini.default")
  if [ -z "$APP_VERSION" ]; then
    echo "❌ APP_VERSION is not set and cannot be found in config.ini.default!"
    exit 1
  else
    echo "APP_VERSION is set to $APP_VERSION"
  fi
fi


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

# Find line number by keyword
findLine() {
  local file="$1"
  local keyword="$2"
  local line=$(grep -n "$keyword" "$file" | cut -d: -f1)
  echo "$line"
}

# Insert content after a specific line
insertAfterLine() {
  local file="$1"
  local line="$2"
  local content="$3"
  local newContent=""
  local i=1
  while IFS= read -r lineContent; do
    if [ $i -eq $line ]; then
      newContent+="$lineContent\n$content\n"
    else
      newContent+="$lineContent\n"
    fi
    i=$((i+1))
  done < "$file"
  echo -e "$newContent"
}

# Add `info_plist` to `MDCx.spec` file
INFO_PLIST=$(cat <<EOF
    info_plist={
        'CFBundleShortVersionString': '$APP_VERSION',
        'CFBundleVersion': '$APP_VERSION',
    }
EOF
)

LINE=$(findLine "MDCx.spec" "bundle_identifier")
NEW_CONTENT=$(insertAfterLine "MDCx.spec" $LINE "$INFO_PLIST")
echo -e "$NEW_CONTENT" > MDCx.spec


# Build the app
pyinstaller MDCx.spec

# Remove unnecessary files
rm -rf ./build
rm *.spec


# Install `create-dmg` if `CREATE_DMG` is true
if [ "$CREATE_DMG" = true ] && ! command -v create-dmg &> /dev/null; then
  echo "Installing create-dmg..."
  brew install create-dmg
  if [ $? -ne 0 ]; then
    echo "❌ Failed to install create-dmg!"
    exit 1
  fi
fi


# Create DMG file
if [ "$CREATE_DMG" = true ]; then
  echo "Creating DMG file..."
  # https://github.com/create-dmg/create-dmg?tab=readme-ov-file#usage
  create-dmg \
    --volname "$appName" \
    --volicon "resources/Img/MDCx.icns" \
    --window-pos 200 120 \
    --window-size 800 400 \
    --icon-size 80 \
    --icon "$appName.app" 300 36 \
    --hide-extension "$appName.app" \
    --app-drop-link 500 36 \
    "dist/$appName.dmg" \
    "dist/$appName.app"

  if [ $? -ne 0 ]; then
    echo "❌ Failed to create DMG file!"
    exit 1
  fi
fi