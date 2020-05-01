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

from setup import setup as rpsetup
from setuptools import setup, find_packages


class CMD_ARGS(object):
    clean = True
    verbose = True
    skip_update = True
    skip_native = True
    skip_samples = True
    ci_build = False


if __name__ == "__main__":
    rpsetup(CMD_ARGS)

    packages = find_packages()
    packages.remove('rpcore.pynative')

    setup(
        name='render_pipeline',
        version='1.3.2',
        description='RenderPipeline',
        long_description=(
            'Physically Based Shading and Deferred Rendering '
            'for the Panda3D game engine'),
        url='https://github.com/tobspr/RenderPipeline/wiki',
        download_url='https://github.com/tobspr/RenderPipeline',
        author='tobspr',
        author_email='tobias.springer1@googlemail.com',
        license='MIT',
        packages=packages,
        include_package_data=True,
        install_requires=[
            'panda3d',
        ],
        entry_points={
            'console_scripts': (
                'material_editor=toolkit.material_editor.main:main',
                'plugin_configurator=toolkit.plugin_configurator.main:main',
                'day_time_editor=toolkit.day_time_editor.main:main',
            ),
        },
    )
