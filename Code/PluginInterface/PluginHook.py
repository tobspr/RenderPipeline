

class PluginHook(object):

    """ This is a function decorator which can be used to mark hooks instead
    of calling _bind_to_hook from the base plugin class. """

    def __init__(self, hook_name):
        self._hook_id = hook_name

    def __call__(self, func):
        func.hook_id = self._hook_id
        return func


class SettingChanged(object):

    """ This is a function decorator which is used to mark methods which should
    get called when a certain setting got changed """

    def __init__(self, setting_name):
        self._setting_name = setting_name

    def __call__(self, func):
        func.setting_id = self._setting_name
        return func
