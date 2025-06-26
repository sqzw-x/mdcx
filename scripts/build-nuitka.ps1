$env:PYTHONPATH = "$PWD\src"

# 体积可减小至 ~44MB, 运行速度无明显变化. 构建耗时较长.
$nuitkaArgs = @(
    '--standalone' # 包含 Python
    '--onefile'
    '--windows-icon-from-ico=resources/Img/MDCx.ico'
    '--include-module=_cffi_backend'
    '--include-module=_distutils_hack'
    '--include-data-dir=resources=resources'
    '--enable-plugin=pyqt5'
    '--windows-disable-console'
    '.\main.py'
)

nuitka $nuitkaArgs