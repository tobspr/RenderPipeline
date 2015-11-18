



class BadPluginException(Exception):
    """ Exception which is raised when a plugin failed to load """
    pass


class BadSettingException(Exception):
    """ Exception which is raised when an exception failed to load """
    pass


class PluginConfigError(Exception):
    """ Exception which is raised when something went wrong during reading the
    plugin configuration """
    pass
