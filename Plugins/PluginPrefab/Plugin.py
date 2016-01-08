"""

RenderPipeline

Copyright (c) 2014-2015 tobspr <tobias.springer1@gmail.com>

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
# Load the plugin api
from .. import *

# Load your additional plugin classes here, if required

class Plugin(BasePlugin):

    @PluginHook("on_stage_setup")
    def setup_stages(self):
        """ This method gets called when the pipeline setups the render
        stages. You should create your custom stages here """

    @PluginHook("on_pipeline_created")
    def on_created(self):
        """ This method gets called after the pipeline finished the setup,
        and is about to start rendering """

    @SettingChanged("some_setting")
    def update_some_setting(self):
        """ This method gets called when the setting "some_setting"
        of your plugin gets called. You should do all work to update required
        inputs etc. yourself. """
