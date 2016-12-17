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
        MainWindow.resize(215, 457)
        MainWindow.setMinimumSize(QtCore.QSize(215, 457))
        MainWindow.setMaximumSize(QtCore.QSize(215, 457))
        MainWindow.setStyleSheet("QMainWindow { background: #eee; }\n"
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
"    width: 8px;\n"
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
"QRadioButton {\n"
"    background: #eee;\n"
"    padding: 4px 6px 3px;\n"
"   font-size: 12px;\n"
"    color: #333;\n"
"}\n"
"\n"
"QRadioButton::indicator {\n"
"    width: 15px;\n"
"    height: 15px;\n"
"    margin-top: -1px;\n"
"}\n"
"\n"
"QRadioButton:checked {\n"
"font-weight: bold;\n"
"}\n"
"\n"
"\n"
"QComboBox {\n"
"border: 0;\n"
"background: #fff;\n"
"padding: 5px 10px 1px;\n"
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
"\n"
"\n"
"\n"
"QLabel {\n"
"    color: #444;\n"
"}")
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setVerticalSpacing(0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setContentsMargins(12, 9, 12, 9)
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.cb_material = QtWidgets.QComboBox(self.centralwidget)
        self.cb_material.setMinimumSize(QtCore.QSize(0, 28))
        self.cb_material.setObjectName("cb_material")
        self.cb_material.addItem("")
        self.verticalLayout.addWidget(self.cb_material)
        spacerItem = QtWidgets.QSpacerItem(20, 8, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem)
        self.label_14 = QtWidgets.QLabel(self.centralwidget)
        self.label_14.setObjectName("label_14")
        self.verticalLayout.addWidget(self.label_14)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSpacing(12)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.cb_shading_model = QtWidgets.QComboBox(self.centralwidget)
        self.cb_shading_model.setMinimumSize(QtCore.QSize(0, 28))
        self.cb_shading_model.setObjectName("cb_shading_model")
        self.cb_shading_model.addItem("")
        self.cb_shading_model.addItem("")
        self.cb_shading_model.addItem("")
        self.horizontalLayout.addWidget(self.cb_shading_model)
        self.cb_metallic = QtWidgets.QCheckBox(self.centralwidget)
        self.cb_metallic.setObjectName("cb_metallic")
        self.horizontalLayout.addWidget(self.cb_metallic)
        self.horizontalLayout.setStretch(0, 1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacerItem1 = QtWidgets.QSpacerItem(20, 8, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem1)
        self.label_15 = QtWidgets.QLabel(self.centralwidget)
        self.label_15.setObjectName("label_15")
        self.verticalLayout.addWidget(self.label_15)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.cb_rgb = QtWidgets.QRadioButton(self.centralwidget)
        self.cb_rgb.setChecked(True)
        self.cb_rgb.setObjectName("cb_rgb")
        self.horizontalLayout_3.addWidget(self.cb_rgb)
        self.cb_hsv = QtWidgets.QRadioButton(self.centralwidget)
        self.cb_hsv.setObjectName("cb_hsv")
        self.horizontalLayout_3.addWidget(self.cb_hsv)
        self.cb_srgb = QtWidgets.QRadioButton(self.centralwidget)
        self.cb_srgb.setObjectName("cb_srgb")
        self.horizontalLayout_3.addWidget(self.cb_srgb)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(0, -1, -1, -1)
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.lbl_basecolor3 = QtWidgets.QLabel(self.centralwidget)
        self.lbl_basecolor3.setMinimumSize(QtCore.QSize(11, 0))
        self.lbl_basecolor3.setStyleSheet("background: transparent; color: #555; ")
        self.lbl_basecolor3.setObjectName("lbl_basecolor3")
        self.gridLayout.addWidget(self.lbl_basecolor3, 2, 0, 1, 1)
        self.basecolor_3 = QtWidgets.QSlider(self.centralwidget)
        self.basecolor_3.setMaximum(100)
        self.basecolor_3.setProperty("value", 53)
        self.basecolor_3.setOrientation(QtCore.Qt.Horizontal)
        self.basecolor_3.setObjectName("basecolor_3")
        self.gridLayout.addWidget(self.basecolor_3, 2, 1, 1, 1)
        self.lbl_basecolor2 = QtWidgets.QLabel(self.centralwidget)
        self.lbl_basecolor2.setMinimumSize(QtCore.QSize(11, 0))
        self.lbl_basecolor2.setStyleSheet("background: transparent; color: #555; ")
        self.lbl_basecolor2.setObjectName("lbl_basecolor2")
        self.gridLayout.addWidget(self.lbl_basecolor2, 1, 0, 1, 1)
        self.lbl_basecolor_val3 = QtWidgets.QLabel(self.centralwidget)
        self.lbl_basecolor_val3.setMinimumSize(QtCore.QSize(30, 0))
        self.lbl_basecolor_val3.setMaximumSize(QtCore.QSize(30, 16777215))
        self.lbl_basecolor_val3.setStyleSheet("background: transparent;")
        self.lbl_basecolor_val3.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_basecolor_val3.setObjectName("lbl_basecolor_val3")
        self.gridLayout.addWidget(self.lbl_basecolor_val3, 2, 2, 1, 1)
        self.lbl_basecolor_val2 = QtWidgets.QLabel(self.centralwidget)
        self.lbl_basecolor_val2.setMinimumSize(QtCore.QSize(30, 0))
        self.lbl_basecolor_val2.setMaximumSize(QtCore.QSize(30, 16777215))
        self.lbl_basecolor_val2.setStyleSheet("background: transparent;")
        self.lbl_basecolor_val2.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_basecolor_val2.setObjectName("lbl_basecolor_val2")
        self.gridLayout.addWidget(self.lbl_basecolor_val2, 1, 2, 1, 1)
        self.lbl_basecolor_val1 = QtWidgets.QLabel(self.centralwidget)
        self.lbl_basecolor_val1.setMinimumSize(QtCore.QSize(30, 0))
        self.lbl_basecolor_val1.setMaximumSize(QtCore.QSize(30, 16777215))
        self.lbl_basecolor_val1.setStyleSheet("background: transparent;")
        self.lbl_basecolor_val1.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_basecolor_val1.setObjectName("lbl_basecolor_val1")
        self.gridLayout.addWidget(self.lbl_basecolor_val1, 0, 2, 1, 1)
        self.basecolor_2 = QtWidgets.QSlider(self.centralwidget)
        self.basecolor_2.setMaximum(100)
        self.basecolor_2.setProperty("value", 43)
        self.basecolor_2.setOrientation(QtCore.Qt.Horizontal)
        self.basecolor_2.setObjectName("basecolor_2")
        self.gridLayout.addWidget(self.basecolor_2, 1, 1, 1, 1)
        self.basecolor_1 = QtWidgets.QSlider(self.centralwidget)
        self.basecolor_1.setMaximum(100)
        self.basecolor_1.setProperty("value", 12)
        self.basecolor_1.setOrientation(QtCore.Qt.Horizontal)
        self.basecolor_1.setObjectName("basecolor_1")
        self.gridLayout.addWidget(self.basecolor_1, 0, 1, 1, 1)
        self.lbl_basecolor1 = QtWidgets.QLabel(self.centralwidget)
        self.lbl_basecolor1.setMinimumSize(QtCore.QSize(11, 0))
        self.lbl_basecolor1.setStyleSheet("background: transparent; color: #555; ")
        self.lbl_basecolor1.setObjectName("lbl_basecolor1")
        self.gridLayout.addWidget(self.lbl_basecolor1, 0, 0, 1, 1)
        self.horizontalLayout_2.addLayout(self.gridLayout)
        self.color_container = QtWidgets.QWidget(self.centralwidget)
        self.color_container.setMinimumSize(QtCore.QSize(48, 48))
        self.color_container.setMaximumSize(QtCore.QSize(48, 48))
        self.color_container.setObjectName("color_container")
        self.lbl_color_preview = QtWidgets.QLabel(self.color_container)
        self.lbl_color_preview.setGeometry(QtCore.QRect(0, 0, 48, 48))
        self.lbl_color_preview.setMinimumSize(QtCore.QSize(0, 0))
        self.lbl_color_preview.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.lbl_color_preview.setStyleSheet("background: rgba(60, 120, 255);")
        self.lbl_color_preview.setText("")
        self.lbl_color_preview.setObjectName("lbl_color_preview")
        self.label = QtWidgets.QLabel(self.color_container)
        self.label.setGeometry(QtCore.QRect(0, 0, 48, 48))
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap(":/img/color_picker_mask.png"))
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.color_container)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        spacerItem2 = QtWidgets.QSpacerItem(20, 8, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem2)
        self.tt_roughness = QtWidgets.QLabel(self.centralwidget)
        self.tt_roughness.setObjectName("tt_roughness")
        self.verticalLayout.addWidget(self.tt_roughness)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.slider_roughness = QtWidgets.QSlider(self.centralwidget)
        self.slider_roughness.setMaximum(100)
        self.slider_roughness.setProperty("value", 32)
        self.slider_roughness.setOrientation(QtCore.Qt.Horizontal)
        self.slider_roughness.setObjectName("slider_roughness")
        self.horizontalLayout_4.addWidget(self.slider_roughness)
        self.lbl_roughness = QtWidgets.QLabel(self.centralwidget)
        self.lbl_roughness.setStyleSheet("color: #333;")
        self.lbl_roughness.setObjectName("lbl_roughness")
        self.horizontalLayout_4.addWidget(self.lbl_roughness)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        spacerItem3 = QtWidgets.QSpacerItem(20, 8, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem3)
        self.tt_specular = QtWidgets.QLabel(self.centralwidget)
        self.tt_specular.setObjectName("tt_specular")
        self.verticalLayout.addWidget(self.tt_specular)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.slider_specular = QtWidgets.QSlider(self.centralwidget)
        self.slider_specular.setMaximum(100)
        self.slider_specular.setSliderPosition(20)
        self.slider_specular.setOrientation(QtCore.Qt.Horizontal)
        self.slider_specular.setObjectName("slider_specular")
        self.horizontalLayout_5.addWidget(self.slider_specular)
        self.lbl_specular = QtWidgets.QLabel(self.centralwidget)
        self.lbl_specular.setStyleSheet("color: #333;")
        self.lbl_specular.setObjectName("lbl_specular")
        self.horizontalLayout_5.addWidget(self.lbl_specular)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        spacerItem4 = QtWidgets.QSpacerItem(20, 8, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem4)
        self.tt_normal = QtWidgets.QLabel(self.centralwidget)
        self.tt_normal.setObjectName("tt_normal")
        self.verticalLayout.addWidget(self.tt_normal)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.slider_normal = QtWidgets.QSlider(self.centralwidget)
        self.slider_normal.setMaximum(100)
        self.slider_normal.setSliderPosition(80)
        self.slider_normal.setOrientation(QtCore.Qt.Horizontal)
        self.slider_normal.setObjectName("slider_normal")
        self.horizontalLayout_6.addWidget(self.slider_normal)
        self.lbl_normal = QtWidgets.QLabel(self.centralwidget)
        self.lbl_normal.setStyleSheet("color: #333;")
        self.lbl_normal.setObjectName("lbl_normal")
        self.horizontalLayout_6.addWidget(self.lbl_normal)
        self.verticalLayout.addLayout(self.horizontalLayout_6)
        spacerItem5 = QtWidgets.QSpacerItem(20, 8, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem5)
        self.tt_param1 = QtWidgets.QLabel(self.centralwidget)
        self.tt_param1.setObjectName("tt_param1")
        self.verticalLayout.addWidget(self.tt_param1)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.slider_param1 = QtWidgets.QSlider(self.centralwidget)
        self.slider_param1.setEnabled(False)
        self.slider_param1.setMaximum(100)
        self.slider_param1.setSliderPosition(80)
        self.slider_param1.setOrientation(QtCore.Qt.Horizontal)
        self.slider_param1.setObjectName("slider_param1")
        self.horizontalLayout_7.addWidget(self.slider_param1)
        self.lbl_param1 = QtWidgets.QLabel(self.centralwidget)
        self.lbl_param1.setStyleSheet("color: #333;")
        self.lbl_param1.setObjectName("lbl_param1")
        self.horizontalLayout_7.addWidget(self.lbl_param1)
        self.verticalLayout.addLayout(self.horizontalLayout_7)
        spacerItem6 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem6)
        self.gridLayout_2.addLayout(self.verticalLayout, 1, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setMinimumSize(QtCore.QSize(0, 38))
        self.label_3.setMaximumSize(QtCore.QSize(16777215, 38))
        self.label_3.setStyleSheet("font-size: 17px; color: #03C03C;\n"
"font-weight: 100; background: #fff; padding-left: 7px;")
        self.label_3.setObjectName("label_3")
        self.gridLayout_2.addWidget(self.label_3, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Material Editor"))
        self.label_2.setText(_translate("MainWindow", "Material"))
        self.cb_material.setItemText(0, _translate("MainWindow", "tree01"))
        self.label_14.setText(_translate("MainWindow", "Shading model"))
        self.cb_shading_model.setItemText(0, _translate("MainWindow", "Default"))
        self.cb_shading_model.setItemText(1, _translate("MainWindow", "Emissive"))
        self.cb_shading_model.setItemText(2, _translate("MainWindow", "Transparent"))
        self.cb_metallic.setText(_translate("MainWindow", "Metallic"))
        self.label_15.setText(_translate("MainWindow", "Basecolor"))
        self.cb_rgb.setText(_translate("MainWindow", "RGB"))
        self.cb_hsv.setText(_translate("MainWindow", "HSV"))
        self.cb_srgb.setText(_translate("MainWindow", "sRGB"))
        self.lbl_basecolor3.setText(_translate("MainWindow", "B"))
        self.lbl_basecolor2.setText(_translate("MainWindow", "G"))
        self.lbl_basecolor_val3.setText(_translate("MainWindow", "0.53"))
        self.lbl_basecolor_val2.setText(_translate("MainWindow", "0.43"))
        self.lbl_basecolor_val1.setText(_translate("MainWindow", "0.12"))
        self.lbl_basecolor1.setText(_translate("MainWindow", "R"))
        self.tt_roughness.setText(_translate("MainWindow", "Roughness"))
        self.lbl_roughness.setText(_translate("MainWindow", "0.322"))
        self.tt_specular.setText(_translate("MainWindow", "Specular IOR"))
        self.lbl_specular.setText(_translate("MainWindow", "1.435"))
        self.tt_normal.setText(_translate("MainWindow", "Normal-Strength"))
        self.lbl_normal.setText(_translate("MainWindow", "0.804"))
        self.tt_param1.setText(_translate("MainWindow", "Shading-model-param"))
        self.lbl_param1.setText(_translate("MainWindow", "0.206"))
        self.label_3.setText(_translate("MainWindow", "MATERIAL EDITOR"))

from . import resources_rc
