# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'posterCutToolibttbX.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class Ui_Dialog_cut_poster(object):
    def setupUi(self, Dialog_cut_poster):
        if not Dialog_cut_poster.objectName():
            Dialog_cut_poster.setObjectName(u"Dialog_cut_poster")
        Dialog_cut_poster.resize(1000, 600)
        self.widget_cutimage = QWidget(Dialog_cut_poster)
        self.widget_cutimage.setObjectName(u"widget_cutimage")
        self.widget_cutimage.setGeometry(QRect(0, 0, 800, 540))
        self.widget_cutimage.setAutoFillBackground(False)
        self.widget_cutimage.setStyleSheet(u"background-color: rgb(200, 200, 200);")
        self.label_backgroud_pic = QLabel(self.widget_cutimage)
        self.label_backgroud_pic.setObjectName(u"label_backgroud_pic")
        self.label_backgroud_pic.setGeometry(QRect(0, 0, 800, 540))
        self.label_backgroud_pic.setAlignment(Qt.AlignCenter)
        self.widget = QWidget(Dialog_cut_poster)
        self.widget.setObjectName(u"widget")
        self.widget.setGeometry(QRect(800, 0, 200, 600))
        self.label_2 = QLabel(self.widget)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(20, 280, 131, 16))
        font = QFont()
        font.setBold(True)
        font.setWeight(75)
        self.label_2.setFont(font)
        self.pushButton_open_pic = QPushButton(self.widget)
        self.pushButton_open_pic.setObjectName(u"pushButton_open_pic")
        self.pushButton_open_pic.setGeometry(QRect(30, 20, 141, 40))
        self.label_3 = QLabel(self.widget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(20, 80, 131, 16))
        self.label_3.setFont(font)
        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(20, 230, 59, 16))
        self.label.setFont(font)
        self.label_origin_size = QLabel(self.widget)
        self.label_origin_size.setObjectName(u"label_origin_size")
        self.label_origin_size.setGeometry(QRect(40, 100, 91, 16))
        self.label_5 = QLabel(self.widget)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(20, 130, 131, 16))
        self.label_5.setFont(font)
        self.label_cut_size = QLabel(self.widget)
        self.label_cut_size.setObjectName(u"label_cut_size")
        self.label_cut_size.setGeometry(QRect(40, 150, 91, 16))
        self.label_cut_postion = QLabel(self.widget)
        self.label_cut_postion.setObjectName(u"label_cut_postion")
        self.label_cut_postion.setGeometry(QRect(40, 200, 131, 20))
        self.label_7 = QLabel(self.widget)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setGeometry(QRect(20, 180, 131, 16))
        self.label_7.setFont(font)
        self.label_cut_ratio = QLabel(self.widget)
        self.label_cut_ratio.setObjectName(u"label_cut_ratio")
        self.label_cut_ratio.setGeometry(QRect(40, 250, 111, 20))
        self.pushButton_cut_close = QPushButton(self.widget)
        self.pushButton_cut_close.setObjectName(u"pushButton_cut_close")
        self.pushButton_cut_close.setGeometry(QRect(30, 440, 141, 50))
        self.pushButton_cut = QPushButton(self.widget)
        self.pushButton_cut.setObjectName(u"pushButton_cut")
        self.pushButton_cut.setGeometry(QRect(30, 500, 141, 40))
        self.pushButton_close = QPushButton(self.widget)
        self.pushButton_close.setObjectName(u"pushButton_close")
        self.pushButton_close.setGeometry(QRect(30, 550, 141, 40))
        self.gridLayoutWidget = QWidget(self.widget)
        self.gridLayoutWidget.setObjectName(u"gridLayoutWidget")
        self.gridLayoutWidget.setGeometry(QRect(20, 305, 162, 81))
        self.gridLayout = QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.radioButton_add_no = QRadioButton(self.gridLayoutWidget)
        self.radioButton_add_no.setObjectName(u"radioButton_add_no")

        self.gridLayout.addWidget(self.radioButton_add_no, 2, 1, 1, 1)

        self.radioButton_add_uncensored = QRadioButton(self.gridLayoutWidget)
        self.radioButton_add_uncensored.setObjectName(u"radioButton_add_uncensored")

        self.gridLayout.addWidget(self.radioButton_add_uncensored, 1, 1, 1, 1)

        self.radioButton_add_censored = QRadioButton(self.gridLayoutWidget)
        self.radioButton_add_censored.setObjectName(u"radioButton_add_censored")

        self.gridLayout.addWidget(self.radioButton_add_censored, 1, 0, 1, 1)

        self.radioButton_add_leak = QRadioButton(self.gridLayoutWidget)
        self.radioButton_add_leak.setObjectName(u"radioButton_add_leak")

        self.gridLayout.addWidget(self.radioButton_add_leak, 1, 2, 1, 1)

        self.radioButton_add_umr = QRadioButton(self.gridLayoutWidget)
        self.radioButton_add_umr.setObjectName(u"radioButton_add_umr")

        self.gridLayout.addWidget(self.radioButton_add_umr, 2, 0, 1, 1)

        self.checkBox_add_sub = QCheckBox(self.gridLayoutWidget)
        self.checkBox_add_sub.setObjectName(u"checkBox_add_sub")

        self.gridLayout.addWidget(self.checkBox_add_sub, 0, 0, 1, 1)

        self.widget1 = QWidget(self.widget)
        self.widget1.setObjectName(u"widget1")
        self.widget1.setGeometry(QRect(20, 390, 161, 31))
        self.horizontalLayout = QHBoxLayout(self.widget1)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.radioButton_add_4k = QRadioButton(self.widget1)
        self.radioButton_add_4k.setObjectName(u"radioButton_add_4k")

        self.horizontalLayout.addWidget(self.radioButton_add_4k)

        self.radioButton_add_8k = QRadioButton(self.widget1)
        self.radioButton_add_8k.setObjectName(u"radioButton_add_8k")

        self.horizontalLayout.addWidget(self.radioButton_add_8k)

        self.radioButton_add_no_2 = QRadioButton(self.widget1)
        self.radioButton_add_no_2.setObjectName(u"radioButton_add_no_2")

        self.horizontalLayout.addWidget(self.radioButton_add_no_2)

        self.widget_2 = QWidget(Dialog_cut_poster)
        self.widget_2.setObjectName(u"widget_2")
        self.widget_2.setGeometry(QRect(0, 540, 800, 60))
        self.widget_2.setStyleSheet(u"")
        self.pushButton_to_cut_2 = QPushButton(self.widget_2)
        self.pushButton_to_cut_2.setObjectName(u"pushButton_to_cut_2")
        self.pushButton_to_cut_2.setGeometry(QRect(30, 520, 141, 61))
        self.horizontalSlider_right = QSlider(self.widget_2)
        self.horizontalSlider_right.setObjectName(u"horizontalSlider_right")
        self.horizontalSlider_right.setGeometry(QRect(480, 30, 311, 21))
        self.horizontalSlider_right.setMaximum(10000)
        self.horizontalSlider_right.setSingleStep(1)
        self.horizontalSlider_right.setValue(5000)
        self.horizontalSlider_right.setOrientation(Qt.Horizontal)
        self.horizontalSlider_left = QSlider(self.widget_2)
        self.horizontalSlider_left.setObjectName(u"horizontalSlider_left")
        self.horizontalSlider_left.setGeometry(QRect(50, 31, 311, 20))
        self.horizontalSlider_left.setMaximum(10000)
        self.horizontalSlider_left.setSingleStep(1)
        self.horizontalSlider_left.setValue(5000)
        self.horizontalSlider_left.setOrientation(Qt.Horizontal)
        self.label_4 = QLabel(self.widget_2)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(30, 10, 141, 16))
        self.label_6 = QLabel(self.widget_2)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(440, 10, 131, 16))
        self.pushButton_to_cut_2.raise_()
        self.label_4.raise_()
        self.label_6.raise_()
        self.horizontalSlider_right.raise_()
        self.horizontalSlider_left.raise_()

        self.retranslateUi(Dialog_cut_poster)

        QMetaObject.connectSlotsByName(Dialog_cut_poster)

    # setupUi

    def retranslateUi(self, Dialog_cut_poster):
        Dialog_cut_poster.setWindowTitle(
            QCoreApplication.translate("Dialog_cut_poster", u"\u5c01\u9762\u56fe\u7247\u88c1\u526a", None))
        self.label_backgroud_pic.setText("")
        self.label_2.setText(QCoreApplication.translate("Dialog_cut_poster", u"\u6dfb\u52a0\u6c34\u5370:", None))
        self.pushButton_open_pic.setText(
            QCoreApplication.translate("Dialog_cut_poster", u"\u6253\u5f00\u56fe\u7247", None))
        self.label_3.setText(QCoreApplication.translate("Dialog_cut_poster", u"\u539f\u56fe\u5c3a\u5bf8\uff1a", None))
        self.label.setText(QCoreApplication.translate("Dialog_cut_poster", u"\u9ad8\u5bbd\u6bd4\u4f8b\uff1a1.5", None))
        self.label_origin_size.setText(QCoreApplication.translate("Dialog_cut_poster", u"800\uff0c538", None))
        self.label_5.setText(QCoreApplication.translate("Dialog_cut_poster", u"\u88c1\u526a\u5c3a\u5bf8\uff1a", None))
        self.label_cut_size.setText(QCoreApplication.translate("Dialog_cut_poster", u"379\uff0c538", None))
        self.label_cut_postion.setText(
            QCoreApplication.translate("Dialog_cut_poster", u"400\uff0c0\uff0c379\uff0c538", None))
        self.label_7.setText(QCoreApplication.translate("Dialog_cut_poster", u"\u88c1\u526a\u4f4d\u7f6e\uff1a", None))
        self.label_cut_ratio.setText(QCoreApplication.translate("Dialog_cut_poster", u"1.50", None))
        self.pushButton_cut_close.setText(
            QCoreApplication.translate("Dialog_cut_poster", u"\u88c1\u526a\u5e76\u5173\u95ed", None))
        self.pushButton_cut.setText(QCoreApplication.translate("Dialog_cut_poster", u"\u88c1\u526a", None))
        self.pushButton_close.setText(QCoreApplication.translate("Dialog_cut_poster", u"\u5173\u95ed", None))
        self.radioButton_add_no.setText(QCoreApplication.translate("Dialog_cut_poster", u"\u65e0", None))
        self.radioButton_add_uncensored.setText(QCoreApplication.translate("Dialog_cut_poster", u"\u65e0\u7801", None))
        self.radioButton_add_censored.setText(QCoreApplication.translate("Dialog_cut_poster", u"\u6709\u7801", None))
        self.radioButton_add_leak.setText(QCoreApplication.translate("Dialog_cut_poster", u"\u6d41\u51fa", None))
        self.radioButton_add_umr.setText(QCoreApplication.translate("Dialog_cut_poster", u"\u7834\u89e3", None))
        self.checkBox_add_sub.setText(QCoreApplication.translate("Dialog_cut_poster", u"\u5b57\u5e55", None))
        self.radioButton_add_4k.setText(QCoreApplication.translate("Dialog_cut_poster", u"4K", None))
        self.radioButton_add_8k.setText(QCoreApplication.translate("Dialog_cut_poster", u"8K", None))
        self.radioButton_add_no_2.setText(QCoreApplication.translate("Dialog_cut_poster", u"\u65e0", None))
        self.pushButton_to_cut_2.setText(
            QCoreApplication.translate("Dialog_cut_poster", u"\u786e\u5b9a\u88c1\u526a", None))
        self.label_4.setText(
            QCoreApplication.translate("Dialog_cut_poster", u"\u88c1\u526a\u6846\u5de6/\u4e0a\u4f4d\u7f6e", None))
        self.label_6.setText(
            QCoreApplication.translate("Dialog_cut_poster", u"\u88c1\u526a\u6846\u53f3/\u4e0b\u4f4d\u7f6e", None))
    # retranslateUi
