#!/bin/bash

set -e

# 调试和日志变量
DEBUG_MODE=false
VERBOSE=false
LOG_LEVEL=1  # 1=基本, 2=详细, 3=调试

# 颜色输出支持
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] INFO:${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARN:${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR:${NC} $1" >&2
}

log_debug() {
    if [ "$DEBUG_MODE" = true ] || [ "$LOG_LEVEL" -ge 3 ]; then
        echo -e "${CYAN}[$(date '+%H:%M:%S')] DEBUG:${NC} $1"
    fi
}

log_step() {
    echo -e "${PURPLE}[$(date '+%H:%M:%S')] STEP:${NC} $1"
}

# 错误处理函数
handle_error() {
    local exit_code=$?
    local line_no=$1
    log_error "脚本在第 $line_no 行执行失败，退出码: $exit_code"
    log_error "当前目录: $(pwd)"
    log_error "当前用户: $(whoami)"
    exit $exit_code
}

# 设置错误陷阱
trap 'handle_error ${LINENO}' ERR

# 命令行参数解析
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
    --debug|-d)
      DEBUG_MODE=true
      LOG_LEVEL=3
      log_debug "调试模式已启用"
      shift
      ;;
    --verbose)
      VERBOSE=true
      LOG_LEVEL=2
      shift
      ;;
    --log-level)
      LOG_LEVEL="$2"
      shift
      shift
      ;;
    --help|-h)
      echo "Usage: build-macos.sh [options]"
      echo "Options:"
      echo "  --version, -v       指定版本号。如果未指定，将使用 src/models/config/manual.py 文件中的 LOCAL_VERSION"
      echo "  --create-dmg, -dmg  创建 DMG 文件。默认为 false"
      echo "  --debug, -d         启用调试模式，显示详细的调试信息"
      echo "  --verbose           启用详细输出模式"
      echo "  --log-level LEVEL   设置日志级别 (1=基本, 2=详细, 3=调试)"
      echo "  --help, -h          显示此帮助信息"
      exit 0
      ;;
    *)
      log_warn "未知参数: $1"
      shift
      ;;
  esac
done


# 从Python文件获取应用版本
getAppVersionFromConfig () {
  local configPath="src/models/config/manual.py"
  log_debug "尝试从配置文件获取版本: $configPath"
  
  if [[ -f "$configPath" ]]; then
    log_debug "配置文件存在，正在解析版本号..."
    local version=$(cat $configPath | grep -o 'LOCAL_VERSION\s*=\s*[0-9]\+' | grep -o '[0-9]\+$')
    if [ -n "$version" ]; then
      log_debug "从配置文件中找到版本号: $version"
    else
      log_debug "配置文件中未找到有效的版本号格式"
    fi
    echo $version
  else
    log_warn "配置文件不存在: $configPath"
    echo ''
  fi
}

# 验证环境依赖
check_dependencies() {
  log_step "检查构建环境依赖..."
  
  local missing_deps=()
  
  if ! command -v python3 &> /dev/null; then
    missing_deps+=("python3")
  fi
  
  if ! command -v pyinstaller &> /dev/null; then
    missing_deps+=("pyinstaller")
  fi
  
  if ! command -v pyi-makespec &> /dev/null; then
    missing_deps+=("pyi-makespec")
  fi
  
  if [ ${#missing_deps[@]} -ne 0 ]; then
    log_error "缺少以下依赖: ${missing_deps[*]}"
    log_info "请先安装这些依赖项"
    exit 1
  fi
  
  log_info "所有必要依赖项已就绪"
  
  # 显示版本信息
  if [ "$LOG_LEVEL" -ge 2 ]; then
    log_info "Python 版本: $(python3 --version)"
    log_info "PyInstaller 版本: $(pyinstaller --version)"
  fi
}

# 检查必要文件
check_required_files() {
  log_step "检查必要文件..."
  
  local required_files=(
    "main.py"
    "src"
    "resources/Img/MDCx.icns"
    "resources"
    "libs"
  )
  
  for file in "${required_files[@]}"; do
    if [ ! -e "$file" ]; then
      log_error "必要文件/目录不存在: $file"
      exit 1
    else
      log_debug "✓ $file"
    fi
  done
  
  log_info "所有必要文件检查完成"
}


# 初始化构建环境
script_start_time=$(date +%s)
log_step "初始化构建环境..."
log_info "开始 macOS 应用构建流程"
log_info "工作目录: $(pwd)"

# 检查环境和文件
check_dependencies
check_required_files

# 检查APP_VERSION
log_step "确定应用版本..."
if [ -z "$APP_VERSION" ]; then
  log_info "APP_VERSION 未设置，尝试从 src/models/config/manual.py 获取..."
  APP_VERSION=$(getAppVersionFromConfig)
  if [ -z "$APP_VERSION" ]; then
    log_error "❌ APP_VERSION 未设置且无法从 src/models/config/manual.py 中找到!"
    exit 1
  else
    log_info "✓ APP_VERSION 设置为: $APP_VERSION"
  fi
else
  log_info "✓ 使用指定的 APP_VERSION: $APP_VERSION"
fi


appName="MDCx"
log_debug "应用名称: $appName"

# 生成 .spec 文件
log_step "生成 PyInstaller .spec 文件..."

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

if [ $? -eq 0 ]; then
  log_info "✓ .spec 文件生成成功"
else
  log_error "❌ .spec 文件生成失败"
  exit 1
fi

# 清理之前的构建
log_step "清理之前的构建文件..."
if [ -d "./dist" ]; then
  log_debug "删除旧的 dist 目录"
  rm -rf ./dist
fi

# Find line number by keyword
findLine() {
  local file="$1"
  local keyword="$2"
  log_debug "在文件 '$file' 中查找关键字 '$keyword'"
  local line=$(grep -n "$keyword" "$file" | cut -d: -f1)
  if [ -n "$line" ]; then
    log_debug "找到关键字 '$keyword' 在第 $line 行"
  else
    log_warn "未找到关键字 '$keyword'"
  fi
  echo "$line"
}

# Insert content after a specific line
insertAfterLine() {
  local file="$1"
  local line="$2"
  local content="$3"
  log_debug "在文件 '$file' 的第 $line 行后插入内容"
  local newContent=""
  local i=1
  while IFS= read -r lineContent; do
    if [ $i -eq $line ]; then
      newContent+="$lineContent\n$content\n"
      log_debug "在第 $i 行后插入了内容"
    else
      newContent+="$lineContent\n"
    fi
    i=$((i+1))
  done < "$file"
  printf "%b" "$newContent"
}

# 修改 .spec 文件以添加版本信息
log_step "修改 .spec 文件，添加版本信息..."

# Add `info_plist` to `MDCx.spec` file
INFO_PLIST=$(cat <<EOF
    info_plist={
        'CFBundleShortVersionString': '$APP_VERSION',
        'CFBundleVersion': '$APP_VERSION',
    }
EOF
)

if [ ! -f "MDCx.spec" ]; then
  log_error "❌ MDCx.spec 文件不存在!"
  exit 1
fi

log_debug "正在修改 MDCx.spec 文件..."
LINE=$(findLine "MDCx.spec" "bundle_identifier")

if [ -z "$LINE" ]; then
  log_error "❌ 在 MDCx.spec 文件中未找到 'bundle_identifier' 关键字!"
  exit 1
fi

NEW_CONTENT=$(insertAfterLine "MDCx.spec" $LINE "$INFO_PLIST")
printf "%b" "$NEW_CONTENT" > MDCx.spec

if [ $? -eq 0 ]; then
  log_info "✓ .spec 文件修改成功，已添加版本信息"
else
  log_error "❌ .spec 文件修改失败"
  exit 1
fi

# 显示修改后的关键部分（调试模式）
if [ "$DEBUG_MODE" = true ]; then
  log_debug "修改后的 .spec 文件关键部分:"
  grep -A 5 -B 2 "info_plist" MDCx.spec || true
fi


# 构建应用
log_step "开始构建应用..."
log_info "正在使用 PyInstaller 构建 $appName.app..."

# 记录开始时间
build_start_time=$(date +%s)

pyinstaller MDCx.spec


build_end_time=$(date +%s)
build_duration=$((build_end_time - build_start_time))

if [ $? -eq 0 ]; then
  log_info "✓ 应用构建成功! 耗时: ${build_duration}秒"
else
  log_error "❌ 应用构建失败!"
  if [ "$LOG_LEVEL" -lt 2 ]; then
    log_error "构建日志保存在: /tmp/pyinstaller.log"
    log_info "可以使用 --verbose 参数重新运行以查看详细输出"
  fi
  exit 1
fi

# 验证构建结果
if [ -d "dist/$appName.app" ]; then
  log_info "✓ 应用包生成成功: dist/$appName.app"
  
  # 显示应用包信息
  if [ "$LOG_LEVEL" -ge 2 ]; then
    app_size=$(du -sh "dist/$appName.app" | cut -f1)
    log_info "应用包大小: $app_size"
    
    # 检查应用包结构
    if [ -f "dist/$appName.app/Contents/Info.plist" ]; then
      log_debug "Info.plist 文件存在"
      if [ "$DEBUG_MODE" = true ]; then
        log_debug "Bundle 版本信息:"
        plutil -p "dist/$appName.app/Contents/Info.plist" | grep -E "(CFBundleShortVersionString|CFBundleVersion)" || true
      fi
    else
      log_warn "Info.plist 文件不存在"
    fi
  fi
else
  log_error "❌ 应用包未生成!"
  exit 1
fi

# 清理临时文件
log_step "清理临时文件..."
cleanup_files=()

if [ -d "./build" ]; then
  rm -rf ./build
  cleanup_files+=("build目录")
fi

if [ -f "*.spec" ]; then
  rm -f *.spec
  cleanup_files+=(".spec文件")
fi

if [ ${#cleanup_files[@]} -gt 0 ]; then
  log_info "✓ 已清理: ${cleanup_files[*]}"
else
  log_debug "无需清理的文件"
fi


# DMG 相关处理
if [ "$CREATE_DMG" = true ]; then
  log_step "准备创建 DMG 文件..."
  
  # Install `create-dmg` if `CREATE_DMG` is true
  if ! command -v create-dmg &> /dev/null; then
    log_info "create-dmg 未安装，正在安装..."
    log_warn "这可能需要一些时间..."
    
    if command -v brew &> /dev/null; then
      brew install create-dmg
      if [ $? -ne 0 ]; then
        log_error "❌ 安装 create-dmg 失败!"
        exit 1
      fi
      log_info "✓ create-dmg 安装成功"
    else
      log_error "❌ 需要 Homebrew 来安装 create-dmg!"
      log_info "请先安装 Homebrew: https://brew.sh/"
      exit 1
    fi
  else
    log_debug "create-dmg 已安装"
  fi

  # Create DMG file
  log_step "创建 DMG 文件..."
  log_info "正在创建 $appName.dmg..."
  
  # 记录 DMG 创建开始时间
  dmg_start_time=$(date +%s)
  
  # https://github.com/create-dmg/create-dmg?tab=readme-ov-file#usage
  if [ "$LOG_LEVEL" -ge 2 ]; then
    # 详细模式：显示 create-dmg 输出
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
  else
    # 基本模式：隐藏详细输出
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
      "dist/$appName.app" > /tmp/create-dmg.log 2>&1
  fi

  dmg_end_time=$(date +%s)
  dmg_duration=$((dmg_end_time - dmg_start_time))

  if [ $? -eq 0 ]; then
    log_info "✓ DMG 文件创建成功! 耗时: ${dmg_duration}秒"
    
    # 验证 DMG 文件
    if [ -f "dist/$appName.dmg" ]; then
      dmg_size=$(du -sh "dist/$appName.dmg" | cut -f1)
      log_info "✓ DMG 文件: dist/$appName.dmg (大小: $dmg_size)"
    else
      log_warn "DMG 文件验证失败"
    fi
  else
    log_error "❌ 创建 DMG 文件失败!"
    if [ "$LOG_LEVEL" -lt 2 ]; then
      log_error "DMG 创建日志保存在: /tmp/create-dmg.log"
    fi
    exit 1
  fi
else
  log_debug "跳过 DMG 文件创建"
fi

# 构建完成总结
log_step "构建完成!"

# 计算总耗时
script_end_time=$(date +%s)
total_duration=$((script_end_time - script_start_time))

log_info "=========================================="
log_info "           构建总结报告"
log_info "=========================================="
log_info "应用名称: $appName"
log_info "应用版本: $APP_VERSION"
log_info "总耗时: ${total_duration}秒"

# 输出文件信息
if [ -d "dist/$appName.app" ]; then
  app_size=$(du -sh "dist/$appName.app" | cut -f1)
  log_info "应用包: dist/$appName.app ($app_size)"
fi

if [ "$CREATE_DMG" = true ] && [ -f "dist/$appName.dmg" ]; then
  dmg_size=$(du -sh "dist/$appName.dmg" | cut -f1)
  log_info "DMG 文件: dist/$appName.dmg ($dmg_size)"
fi

log_info "构建目录: $(pwd)/dist"
log_info "=========================================="
