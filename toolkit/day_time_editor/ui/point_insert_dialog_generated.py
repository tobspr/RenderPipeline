# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'point_insert.ui'
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

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.resize(342, 197)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/res/res/icon.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        self.label = QtGui.QLabel(Dialog)
        self.label.setGeometry(QtCore.QRect(10, 10, 301, 71))
        self.label.setWordWrap(True)
        self.label.setObjectName(_fromUtf8("label"))
        self.label_2 = QtGui.QLabel(Dialog)
        self.label_2.setGeometry(QtCore.QRect(10, 100, 46, 21))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.label_3 = QtGui.QLabel(Dialog)
        self.label_3.setGeometry(QtCore.QRect(10, 130, 46, 21))
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.ipt_value = QtGui.QDoubleSpinBox(Dialog)
        self.ipt_value.setGeometry(QtCore.QRect(70, 130, 121, 22))
        self.ipt_value.setMinimum(-99999.0)
        self.ipt_value.setMaximum(99999.99)
        self.ipt_value.setObjectName(_fromUtf8("ipt_value"))
        self.ipt_time = QtGui.QTimeEdit(Dialog)
        self.ipt_time.setGeometry(QtCore.QRect(70, 100, 121, 22))
        self.ipt_time.setObjectName(_fromUtf8("ipt_time"))
        self.btn_insert = QtGui.QPushButton(Dialog)
        self.btn_insert.setGeometry(QtCore.QRect(240, 160, 75, 23))
        self.btn_insert.setObjectName(_fromUtf8("btn_insert"))

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Insert Point", None))
        self.label.setText(_translate("Dialog", "Enter the values of the point you want to insert. \n"
"\n"
"Did you know: If you dont want to enter concrete values, just click and drag anywhere on the curve to insert a new point.", None))
        self.label_2.setText(_translate("Dialog", "Time:", None))
        self.label_3.setText(_translate("Dialog", "Value:", None))
        self.ipt_time.setDisplayFormat(_translate("Dialog", "HH:mm", None))
        self.btn_insert.setText(_translate("Dialog", "Insert", None))

from . import resources_rc
