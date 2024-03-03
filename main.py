#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import platform
import sys

import urllib3  # yapf: disable # NOQA: E402
from PIL import ImageFile
from PyQt5.QtCore import QCoreApplication, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from controllers.main_window.main_window import MyMAinWindow

# import faulthandler
# faulthandler.enable()
urllib3.disable_warnings()  # yapf: disable # NOQA: E402
ImageFile.LOAD_TRUNCATED_IMAGES = True

if __name__ == '__main__':
    '''
    主函数
    '''
    if platform.system() != 'Windows':
        import faulthandler

        faulthandler.enable()

        # TODO 运行pyinstaller打包的程序时，该处理不太合理
        # 想法: 在`main.py`这里，读取config，然后判断`'hide_dock' in config.switch_on`
        if os.path.isfile('resources/Img/1'):
            try:
                import AppKit

                info = AppKit.NSBundle.mainBundle().infoDictionary()
                info["LSUIElement"] = True
            except:
                pass

    if os.path.isfile('highdpi_passthrough'):
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
    if platform.system() != 'Windows':
        app.setWindowIcon(QIcon('resources/Img/MDCx.ico'))  # 设置任务栏图标
    ui = MyMAinWindow()
    ui.show()
    app.installEventFilter(ui)
    # newWin2 = CutWindow()
    try:
        sys.exit(app.exec_())
    except Exception as e:
        print(e)
