
from TimeOfDayWindow import TimeOfDayWindow

class TimeOfDayManager:

    def __init__(self, instance):
        # Create time of day instance
        self.window = TimeOfDayWindow(instance)
        self.window.show()
