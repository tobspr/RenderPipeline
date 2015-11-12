# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main_window.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1000, 700)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QtCore.QSize(1000, 700))
        MainWindow.setMaximumSize(QtCore.QSize(1000, 700))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icon/res/icon.ico")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.lst_plugins = QtGui.QListWidget(self.centralwidget)
        self.lst_plugins.setGeometry(QtCore.QRect(20, 130, 241, 541))
        self.lst_plugins.setStyleSheet(_fromUtf8("QListWidget::item {\n"
"padding: 5px;\n"
"}"))
        self.lst_plugins.setObjectName(_fromUtf8("lst_plugins"))
        item = QtGui.QListWidgetItem()
        self.lst_plugins.addItem(item)
        item = QtGui.QListWidgetItem()
        self.lst_plugins.addItem(item)
        item = QtGui.QListWidgetItem()
        self.lst_plugins.addItem(item)
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(20, 30, 401, 51))
        font = QtGui.QFont()
        font.setPointSize(18)
        self.label.setFont(font)
        self.label.setObjectName(_fromUtf8("label"))
        self.label_2 = QtGui.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(20, 95, 141, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_2.setFont(font)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.frame = QtGui.QFrame(self.centralwidget)
        self.frame.setGeometry(QtCore.QRect(300, 100, 671, 571))
        self.frame.setFrameShape(QtGui.QFrame.Box)
        self.frame.setFrameShadow(QtGui.QFrame.Plain)
        self.frame.setLineWidth(1)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.lbl_plugin_name = QtGui.QLabel(self.frame)
        self.lbl_plugin_name.setGeometry(QtCore.QRect(30, 30, 281, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.lbl_plugin_name.setFont(font)
        self.lbl_plugin_name.setTextFormat(QtCore.Qt.PlainText)
        self.lbl_plugin_name.setObjectName(_fromUtf8("lbl_plugin_name"))
        self.lbl_plugin_version = QtGui.QLabel(self.frame)
        self.lbl_plugin_version.setGeometry(QtCore.QRect(30, 60, 591, 16))
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(0, 170, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 170, 0))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)
        self.lbl_plugin_version.setPalette(palette)
        self.lbl_plugin_version.setTextFormat(QtCore.Qt.PlainText)
        self.lbl_plugin_version.setObjectName(_fromUtf8("lbl_plugin_version"))
        self.lbl_plugin_desc = QtGui.QLabel(self.frame)
        self.lbl_plugin_desc.setGeometry(QtCore.QRect(30, 80, 591, 91))
        self.lbl_plugin_desc.setStyleSheet(_fromUtf8("color: #777"))
        self.lbl_plugin_desc.setTextFormat(QtCore.Qt.PlainText)
        self.lbl_plugin_desc.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.lbl_plugin_desc.setWordWrap(True)
        self.lbl_plugin_desc.setObjectName(_fromUtf8("lbl_plugin_desc"))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1000, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "RenderPipeline Plugin Configurator", None))
        __sortingEnabled = self.lst_plugins.isSortingEnabled()
        self.lst_plugins.setSortingEnabled(False)
        item = self.lst_plugins.item(0)
        item.setText(_translate("MainWindow", "Item 1", None))
        item = self.lst_plugins.item(1)
        item.setText(_translate("MainWindow", "Item 2", None))
        item = self.lst_plugins.item(2)
        item.setText(_translate("MainWindow", "Item 3", None))
        self.lst_plugins.setSortingEnabled(__sortingEnabled)
        self.label.setText(_translate("MainWindow", "RenderPipeline Plugin Configurator", None))
        self.label_2.setText(_translate("MainWindow", "Available Plugins", None))
        self.lbl_plugin_name.setText(_translate("MainWindow", "lbl_plugin_name", None))
        self.lbl_plugin_version.setText(_translate("MainWindow", "lbl_plugin_version", None))
        self.lbl_plugin_desc.setText(_translate("MainWindow", "lbl_plugin_desca\n"
"asd\n"
"Another long line\n"
"Even more lines!", None))

import resources_rc
