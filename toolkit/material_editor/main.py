"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

# This tool offers an interface to modify materials
# Hacked together in a hour, I'm sorry.

from __future__ import print_function

import os
import sys
import time
import tempfile
from threading import Thread
from functools import partial

os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__))))
sys.path.insert(0, os.getcwd())
sys.path.insert(0, "../../")

from rplibs.six import iteritems  # noqa
from rplibs.pyqt_imports import * #noqa

from ui.main_window_generated import Ui_MainWindow  # noqa
from rpcore.util.network_communication import NetworkCommunication  # noqa

# Allow working with an older version of the material DB.
# ONLY for debugging the viewer.
ALLOW_OUTDATED_MATERIALS = False

class MaterialData:
    def __init__(self):
        self.name = ""
        self.shading_model = 0
        self.metallic = False
        self.roughness = 0.0
        self.specular = 0.0
        self.normal_strength = 0.0
        self.shading_model_param1 = 0.0
        self.shading_model_param2 = 0.0
        self.basecolor_r = 0.6
        self.basecolor_g = 0.6
        self.basecolor_b = 0.6

class MaterialEditor(QMainWindow, Ui_MainWindow):

    """ Interface to change the plugin settings """

    SHADING_MODELS = [
        ("Default", 0, None),
        ("Emissive", 1, None),
        ("Clearcoat", 2, None),
        ("Transparent", 3, "Transparency"),
        ("Skin", 4, None),
        ("Foliage", 5, None),
    ]

    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        self.materials = []
        self.in_update = False

        self.setupUi(self)
        self.init_shading_models()

        self.material = MaterialData()

        qt_connect(self.cb_metallic, "stateChanged", self.set_metallic)
        qt_connect(self.cb_shading_model, "currentIndexChanged", self.set_shading_model)
        qt_connect(self.cb_material, "currentIndexChanged", self.set_material)

        self.sliders = [
            (self.basecolor_r, self.lbl_basecolor_r, 0.0, 1.0, "basecolor_r"),
            (self.basecolor_g, self.lbl_basecolor_g, 0.0, 1.0, "basecolor_g"),
            (self.basecolor_b, self.lbl_basecolor_b, 0.0, 1.0, "basecolor_b"),
            (self.slider_roughness, self.lbl_roughness, 0.0, 1.0, "roughness"),
            (self.slider_specular, self.lbl_specular, 1.0, 2.51, "specular"),
            (self.slider_normal, self.lbl_normal, 0.0, 1.0, "normal_strength"),
            (self.slider_param1, self.lbl_param1, 0.0, 1.0, "shading_model_param1"),
        ]

        for slider, lbl, start, end, prop in self.sliders:
            qt_connect(slider, "valueChanged", self.update_sliders)

        self.update_material_list()
        self.set_material()

    def update_sliders(self):
        for slider, lbl, start, end, prop in self.sliders:
            val = (slider.value() / 100.0) * (end - start) + start
            lbl.setText("{:0.2f}".format(val))
            setattr(self.material, prop, val)

        self.lbl_color_preview.setStyleSheet("background: rgb({}, {}, {});".format(
            int(self.material.basecolor_r * 255),
            int(self.material.basecolor_g * 255),
            int(self.material.basecolor_b * 255)))
        self.send_update()

    def update_material_list(self):
        temp_path = os.path.join(tempfile.gettempdir(), "rp_materials.data")
        print("Waiting for creation of", temp_path)
        if not ALLOW_OUTDATED_MATERIALS:
            try:
                os.remove(temp_path)
            except:
                pass
        NetworkCommunication.send_async(NetworkCommunication.MATERIAL_PORT, "dump_materials " + temp_path)
        start_time = time.time()
        while not os.path.isfile(temp_path) and time.time() - start_time < 5.0:
            time.sleep(0.5)
        if not os.path.isfile(temp_path):
            QMessageBox.critical(self, "Error", "Render Pipeline not responding! Make sure a render pipeline application is running, and try again later.")
            sys.exit(-1)
        if not ALLOW_OUTDATED_MATERIALS:
            time.sleep(0.5)
        self._load_material_list(temp_path)

    def _load_material_list(self, pth):
        self.in_update = True
        self.materials = []
        self.cb_material.clear()
        with open(pth) as handle:
            for line in handle.readlines():
                parts = line.strip().split(" ")
                material = MaterialData()
                material.name = parts[0]
                material.basecolor_r = float(parts[1])
                material.basecolor_g = float(parts[2])
                material.basecolor_b = float(parts[3])
                material.roughness = float(parts[4])
                material.specular = float(parts[5])
                material.metallic = float(parts[6]) > 0.5
                material.shading_model = int(float(parts[7]))
                material.normal_strength = float(parts[8])
                material.shading_model_param1 = float(parts[9])
                material.shading_model_param2 = float(parts[10])
                self.materials.append(material)
                self.cb_material.addItem(material.name)
        self.update_sliders()
        self.in_update = False
        print("Loaded material list")

    def set_material(self):
        index = self.cb_material.currentIndex()
        if index >= len(self.materials) - 1:
            print("invalid material.")
            return
        self.in_update = True
        material = self.materials[index]
        self.cb_shading_model.setCurrentIndex(material.shading_model)
        self.cb_metallic.setChecked(material.metallic)
        self.slider_roughness.setValue(material.roughness * 100.0)
        self.slider_specular.setValue(material.specular / 2.51 * 100.0)
        self.slider_normal.setValue(material.normal_strength * 100.0)
        self.basecolor_r.setValue(material.basecolor_r * 100)
        self.basecolor_g.setValue(material.basecolor_g * 100)
        self.basecolor_b.setValue(material.basecolor_b * 100)
        self.slider_param1.setValue(material.shading_model_param1 * 100)

        self.material = material
        self.update_sliders()
        self.in_update = False

    def set_metallic(self):
        self.material.metallic = self.cb_metallic.isChecked()
        self.slider_specular.setEnabled(not self.material.metallic)
        self.send_update()

    def send_update(self):
        if self.in_update:
            return
        serialized = ("{} " * 11).format(
            self.material.name,
            self.material.basecolor_r,
            self.material.basecolor_g,
            self.material.basecolor_b,
            self.material.roughness,
            self.material.specular,
            1.0 if self.material.metallic else 0.0,
            self.material.shading_model,
            self.material.normal_strength,
            self.material.shading_model_param1,
            self.material.shading_model_param2,
        )
        NetworkCommunication.send_async(NetworkCommunication.MATERIAL_PORT, "update_material " + serialized)

    def set_shading_model(self):
        name, val, optional_param = self.SHADING_MODELS[self.cb_shading_model.currentIndex()]
        if optional_param is None:
            self.slider_param1.setEnabled(False)
            self.lbl_shading_model_param1.setText("Unused")
        else:
            self.slider_param1.setEnabled(True)
            self.lbl_shading_model_param1.setText(optional_param)

        self.cb_metallic.show()
        self.slider_roughness.setEnabled(True)
        self.slider_normal.setEnabled(True)

        if name == "Emissive":
            self.cb_metallic.hide()
            self.slider_roughness.setEnabled(False)
            self.slider_specular.setEnabled(False)
            self.slider_normal.setEnabled(False)
        elif name == "Clearcoat":
            self.cb_metallic.hide()
            self.slider_specular.setEnabled(False)
        elif name == "Transparent":
            pass
        elif name == "Skin":
            self.cb_metallic.hide()
        elif name == "Foliage":
            self.cb_metallic.hide()
            
        

        self.material.shading_model = val
        self.send_update()

    def init_shading_models(self):
        self.cb_shading_model.clear()
        for name, val, optional_param in self.SHADING_MODELS:
            self.cb_shading_model.addItem(name)


# Start application
app = QApplication(sys.argv)
qt_register_fonts()
editor = MaterialEditor()
editor.show()
app.exec_()
