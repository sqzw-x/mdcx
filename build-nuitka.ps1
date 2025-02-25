$env:PYTHONPATH = "$PWD\src"

$nuitkaArgs = @(
    '--standalone' # 包含 Python
    '--onefile'
    '--windows-icon-from-ico=resources/Img/MDCx.ico'
    '--include-module=_cffi_backend'
    '--include-module=_distutils_hack'
    '--include-data-dir=resources=resources'
    '--enable-plugin=pyqt5'
    '.\main.py'
)

nuitka $nuitkaArgs