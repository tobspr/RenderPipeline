# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main_window.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(262, 556)
        MainWindow.setMinimumSize(QtCore.QSize(262, 556))
        MainWindow.setMaximumSize(QtCore.QSize(262, 556))
        MainWindow.setStyleSheet("QMainWindow { background: #fff;}\n"
"*, QLabel { font-family: Roboto; font-weight: 300; }\n"
"\n"
"QSlider::groove:horizontal {\n"
"    border: 0;\n"
"    height: 4px;\n"
"    background: rgba(0, 0, 0, 15);\n"
"}\n"
"\n"
"QSlider::handle:horizonal {\n"
"    background: #666;\n"
"    width: 9px;\n"
"    margin: -6px 0;\n"
"}\n"
"\n"
"QSlider::handle:horizontal:disabled {\n"
"    background: #ccc;\n"
"}\n"
"QSlider::groove:horizontal:disabled {\n"
"    background: rgba(0, 0, 0, 8);\n"
"}\n"
"\n"
"\n"
"\n"
"QComboBox {\n"
"border: 0;\n"
"background: #fff;\n"
"padding: 7px 10px 3px;\n"
"font-family: Roboto;\n"
"color: #777;\n"
"font-size: 12px;\n"
"}\n"
"\n"
"QComboBox::down-arrow {\n"
"    border: 0;\n"
"    margin: -3px;\n"
"    background: #ddd;\n"
"    margin-left: -16px;\n"
"margin-bottom: -4px;\n"
"    image: url(\":/img/down-arrow.png\");\n"
"}\n"
"\n"
"QCheckBox::indicator {\n"
"    border: 1px solid #aaa;\n"
"    background: #39f;\n"
"    width: 14px;\n"
"    height: 14px;\n"
"    image: url(\":/img/checked.png\");\n"
"}\n"
"\n"
"QCheckBox {\n"
"text-transform: uppercase;\n"
"color: #555;\n"
"}\n"
"\n"
"QCheckBox::indicator:unchecked {\n"
"    background: #fff;\n"
"    image: none;\n"
"}")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setMinimumSize(QtCore.QSize(0, 65))
        self.frame.setMaximumSize(QtCore.QSize(16777215, 65))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.label = QtWidgets.QLabel(self.frame)
        self.label.setGeometry(QtCore.QRect(20, 26, 261, 31))
        self.label.setStyleSheet("font-size: 20px; color: #03C03C;\n"
"font-weight: 100;")
        self.label.setObjectName("label")
        self.label_9 = QtWidgets.QLabel(self.frame)
        self.label_9.setGeometry(QtCore.QRect(20, 6, 261, 31))
        self.label_9.setStyleSheet("font-size: 13px;\n"
"color: #aaa;\n"
"font-weight: 600;")
        self.label_9.setObjectName("label_9")
        self.verticalLayout.addWidget(self.frame)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.sidebar_material = QtWidgets.QFrame(self.centralwidget)
        self.sidebar_material.setMinimumSize(QtCore.QSize(0, 0))
        self.sidebar_material.setMaximumSize(QtCore.QSize(999999, 16777215))
        self.sidebar_material.setStyleSheet("QFrame { background: #eee; } QFrame>QLabel { text-transform: uppercase; color: #888;  background: transparent; }")
        self.sidebar_material.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.sidebar_material.setFrameShadow(QtWidgets.QFrame.Raised)
        self.sidebar_material.setObjectName("sidebar_material")
        self.label_2 = QtWidgets.QLabel(self.sidebar_material)
        self.label_2.setGeometry(QtCore.QRect(20, 20, 61, 16))
        self.label_2.setObjectName("label_2")
        self.cb_material = QtWidgets.QComboBox(self.sidebar_material)
        self.cb_material.setGeometry(QtCore.QRect(20, 40, 221, 30))
        self.cb_material.setObjectName("cb_material")
        self.cb_material.addItem("")
        self.label_14 = QtWidgets.QLabel(self.sidebar_material)
        self.label_14.setGeometry(QtCore.QRect(20, 80, 141, 16))
        self.label_14.setObjectName("label_14")
        self.cb_shading_model = QtWidgets.QComboBox(self.sidebar_material)
        self.cb_shading_model.setGeometry(QtCore.QRect(20, 100, 221, 30))
        self.cb_shading_model.setObjectName("cb_shading_model")
        self.cb_shading_model.addItem("")
        self.cb_shading_model.addItem("")
        self.cb_shading_model.addItem("")
        self.cb_metallic = QtWidgets.QCheckBox(self.sidebar_material)
        self.cb_metallic.setGeometry(QtCore.QRect(20, 140, 81, 17))
        self.cb_metallic.setObjectName("cb_metallic")
        self.horizontalLayoutWidget_3 = QtWidgets.QWidget(self.sidebar_material)
        self.horizontalLayoutWidget_3.setGeometry(QtCore.QRect(20, 200, 221, 73))
        self.horizontalLayoutWidget_3.setObjectName("horizontalLayoutWidget_3")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_3)
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.lbl_basecolor_g = QtWidgets.QLabel(self.horizontalLayoutWidget_3)
        self.lbl_basecolor_g.setMinimumSize(QtCore.QSize(30, 0))
        self.lbl_basecolor_g.setMaximumSize(QtCore.QSize(30, 16777215))
        self.lbl_basecolor_g.setStyleSheet("color: green;background: transparent;")
        self.lbl_basecolor_g.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_basecolor_g.setObjectName("lbl_basecolor_g")
        self.gridLayout.addWidget(self.lbl_basecolor_g, 1, 1, 1, 1)
        self.lbl_basecolor_r = QtWidgets.QLabel(self.horizontalLayoutWidget_3)
        self.lbl_basecolor_r.setMinimumSize(QtCore.QSize(30, 0))
        self.lbl_basecolor_r.setMaximumSize(QtCore.QSize(30, 16777215))
        self.lbl_basecolor_r.setStyleSheet("color: red; background: transparent;")
        self.lbl_basecolor_r.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_basecolor_r.setObjectName("lbl_basecolor_r")
        self.gridLayout.addWidget(self.lbl_basecolor_r, 0, 1, 1, 1)
        self.basecolor_b = QtWidgets.QSlider(self.horizontalLayoutWidget_3)
        self.basecolor_b.setStyleSheet("QSlider::handle:horizontal { background: blue; }")
        self.basecolor_b.setMaximum(100)
        self.basecolor_b.setProperty("value", 53)
        self.basecolor_b.setOrientation(QtCore.Qt.Horizontal)
        self.basecolor_b.setObjectName("basecolor_b")
        self.gridLayout.addWidget(self.basecolor_b, 2, 0, 1, 1)
        self.basecolor_r = QtWidgets.QSlider(self.horizontalLayoutWidget_3)
        self.basecolor_r.setStyleSheet("QSlider::handle:horizontal { background: red; }")
        self.basecolor_r.setMaximum(100)
        self.basecolor_r.setProperty("value", 12)
        self.basecolor_r.setOrientation(QtCore.Qt.Horizontal)
        self.basecolor_r.setObjectName("basecolor_r")
        self.gridLayout.addWidget(self.basecolor_r, 0, 0, 1, 1)
        self.basecolor_g = QtWidgets.QSlider(self.horizontalLayoutWidget_3)
        self.basecolor_g.setStyleSheet("QSlider::handle:horizontal { background: green; }")
        self.basecolor_g.setMaximum(100)
        self.basecolor_g.setProperty("value", 43)
        self.basecolor_g.setOrientation(QtCore.Qt.Horizontal)
        self.basecolor_g.setObjectName("basecolor_g")
        self.gridLayout.addWidget(self.basecolor_g, 1, 0, 1, 1)
        self.lbl_basecolor_b = QtWidgets.QLabel(self.horizontalLayoutWidget_3)
        self.lbl_basecolor_b.setMinimumSize(QtCore.QSize(30, 0))
        self.lbl_basecolor_b.setMaximumSize(QtCore.QSize(30, 16777215))
        self.lbl_basecolor_b.setStyleSheet("color: blue;background: transparent;")
        self.lbl_basecolor_b.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_basecolor_b.setObjectName("lbl_basecolor_b")
        self.gridLayout.addWidget(self.lbl_basecolor_b, 2, 1, 1, 1)
        self.horizontalLayout_4.addLayout(self.gridLayout)
        self.lbl_color_preview = QtWidgets.QLabel(self.horizontalLayoutWidget_3)
        self.lbl_color_preview.setMinimumSize(QtCore.QSize(30, 0))
        self.lbl_color_preview.setMaximumSize(QtCore.QSize(30, 16777215))
        self.lbl_color_preview.setStyleSheet("background: rgba(60, 120, 255);")
        self.lbl_color_preview.setText("")
        self.lbl_color_preview.setObjectName("lbl_color_preview")
        self.horizontalLayout_4.addWidget(self.lbl_color_preview)
        self.label_15 = QtWidgets.QLabel(self.sidebar_material)
        self.label_15.setGeometry(QtCore.QRect(20, 180, 131, 16))
        self.label_15.setObjectName("label_15")
        self.label_16 = QtWidgets.QLabel(self.sidebar_material)
        self.label_16.setGeometry(QtCore.QRect(20, 290, 131, 16))
        self.label_16.setObjectName("label_16")
        self.slider_roughness = QtWidgets.QSlider(self.sidebar_material)
        self.slider_roughness.setGeometry(QtCore.QRect(20, 310, 191, 19))
        self.slider_roughness.setMaximum(100)
        self.slider_roughness.setProperty("value", 32)
        self.slider_roughness.setOrientation(QtCore.Qt.Horizontal)
        self.slider_roughness.setObjectName("slider_roughness")
        self.label_17 = QtWidgets.QLabel(self.sidebar_material)
        self.label_17.setGeometry(QtCore.QRect(20, 340, 131, 16))
        self.label_17.setObjectName("label_17")
        self.slider_specular = QtWidgets.QSlider(self.sidebar_material)
        self.slider_specular.setGeometry(QtCore.QRect(20, 360, 191, 19))
        self.slider_specular.setMaximum(100)
        self.slider_specular.setSliderPosition(20)
        self.slider_specular.setOrientation(QtCore.Qt.Horizontal)
        self.slider_specular.setObjectName("slider_specular")
        self.label_18 = QtWidgets.QLabel(self.sidebar_material)
        self.label_18.setGeometry(QtCore.QRect(20, 390, 131, 16))
        self.label_18.setObjectName("label_18")
        self.slider_normal = QtWidgets.QSlider(self.sidebar_material)
        self.slider_normal.setGeometry(QtCore.QRect(20, 410, 191, 19))
        self.slider_normal.setMaximum(100)
        self.slider_normal.setSliderPosition(80)
        self.slider_normal.setOrientation(QtCore.Qt.Horizontal)
        self.slider_normal.setObjectName("slider_normal")
        self.lbl_roughness = QtWidgets.QLabel(self.sidebar_material)
        self.lbl_roughness.setGeometry(QtCore.QRect(220, 310, 31, 20))
        self.lbl_roughness.setStyleSheet("color: #333;")
        self.lbl_roughness.setObjectName("lbl_roughness")
        self.lbl_specular = QtWidgets.QLabel(self.sidebar_material)
        self.lbl_specular.setGeometry(QtCore.QRect(220, 360, 31, 20))
        self.lbl_specular.setStyleSheet("color: #333;")
        self.lbl_specular.setObjectName("lbl_specular")
        self.lbl_normal = QtWidgets.QLabel(self.sidebar_material)
        self.lbl_normal.setGeometry(QtCore.QRect(220, 409, 31, 20))
        self.lbl_normal.setStyleSheet("color: #333;")
        self.lbl_normal.setObjectName("lbl_normal")
        self.frame_2 = QtWidgets.QFrame(self.sidebar_material)
        self.frame_2.setGeometry(QtCore.QRect(-10, 166, 311, 341))
        self.frame_2.setStyleSheet("QFrame { background: #fff; }")
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.lbl_param1 = QtWidgets.QLabel(self.frame_2)
        self.lbl_param1.setGeometry(QtCore.QRect(230, 289, 31, 20))
        self.lbl_param1.setStyleSheet("color: #333;")
        self.lbl_param1.setObjectName("lbl_param1")
        self.slider_param1 = QtWidgets.QSlider(self.frame_2)
        self.slider_param1.setEnabled(False)
        self.slider_param1.setGeometry(QtCore.QRect(30, 290, 191, 19))
        self.slider_param1.setMaximum(100)
        self.slider_param1.setSliderPosition(80)
        self.slider_param1.setOrientation(QtCore.Qt.Horizontal)
        self.slider_param1.setObjectName("slider_param1")
        self.lbl_shading_model_param1 = QtWidgets.QLabel(self.frame_2)
        self.lbl_shading_model_param1.setGeometry(QtCore.QRect(30, 270, 141, 16))
        self.lbl_shading_model_param1.setObjectName("lbl_shading_model_param1")
        self.frame_2.raise_()
        self.label_2.raise_()
        self.cb_material.raise_()
        self.label_14.raise_()
        self.cb_shading_model.raise_()
        self.cb_metallic.raise_()
        self.horizontalLayoutWidget_3.raise_()
        self.label_15.raise_()
        self.label_16.raise_()
        self.slider_roughness.raise_()
        self.label_17.raise_()
        self.slider_specular.raise_()
        self.label_18.raise_()
        self.slider_normal.raise_()
        self.lbl_roughness.raise_()
        self.lbl_specular.raise_()
        self.lbl_normal.raise_()
        self.horizontalLayout.addWidget(self.sidebar_material)
        self.verticalLayout.addLayout(self.horizontalLayout)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Render Pipeline Material Editor"))
        self.label.setText(_translate("MainWindow", "MATERIAL EDITOR"))
        self.label_9.setText(_translate("MainWindow", "RENDER PIPELINE"))
        self.label_2.setText(_translate("MainWindow", "Material"))
        self.cb_material.setItemText(0, _translate("MainWindow", "tree01"))
        self.label_14.setText(_translate("MainWindow", "Shading model"))
        self.cb_shading_model.setItemText(0, _translate("MainWindow", "Default"))
        self.cb_shading_model.setItemText(1, _translate("MainWindow", "Emissive"))
        self.cb_shading_model.setItemText(2, _translate("MainWindow", "Transparent"))
        self.cb_metallic.setText(_translate("MainWindow", "Metallic"))
        self.lbl_basecolor_g.setText(_translate("MainWindow", "0.43"))
        self.lbl_basecolor_r.setText(_translate("MainWindow", "0.12"))
        self.lbl_basecolor_b.setText(_translate("MainWindow", "0.53"))
        self.label_15.setText(_translate("MainWindow", "Basecolor"))
        self.label_16.setText(_translate("MainWindow", "Roughness"))
        self.label_17.setText(_translate("MainWindow", "Specular IOR"))
        self.label_18.setText(_translate("MainWindow", "Normal-Strength"))
        self.lbl_roughness.setText(_translate("MainWindow", "0.32"))
        self.lbl_specular.setText(_translate("MainWindow", "1.43"))
        self.lbl_normal.setText(_translate("MainWindow", "0.80"))
        self.lbl_param1.setText(_translate("MainWindow", "0.20"))
        self.lbl_shading_model_param1.setText(_translate("MainWindow", "Shading-model-param"))

from . import resources_rc
