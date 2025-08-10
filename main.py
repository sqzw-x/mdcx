#!/usr/bin/env python3
import os
import platform
import sys

from PIL import ImageFile
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from mdcx.consts import show_constants
from mdcx.controllers.main_window.main_window import MyMAinWindow

ImageFile.LOAD_TRUNCATED_IMAGES = True

show_constants()


if os.path.isfile("highdpi_passthrough"):
    # 解决不同电脑不同缩放比例问题，非整数倍缩放，如系统中设置了150%的缩放，QT程序的缩放将是两倍，QT 5.14中增加了非整数倍的支持，需要加入下面的代码才能使用150%的缩放
    # 默认是 Qt.HighDpiScaleFactorRoundingPolicy.Round，会将150%缩放变成200%
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

# 适应高DPI设备
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

# 解决图片在不同分辨率显示模糊问题
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

app = QApplication(sys.argv)
if platform.system() != "Windows":
    app.setWindowIcon(QIcon("resources/Img/MDCx.ico"))  # 设置任务栏图标
ui = MyMAinWindow()
ui.show()
app.installEventFilter(ui)
# newWin2 = CutWindow()
try:
    sys.exit(app.exec_())
except Exception as e:
    print(e)
