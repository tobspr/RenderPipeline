"""
Colors text in console mode application (win32).
Uses ctypes and Win32 methods SetConsoleTextAttribute and
GetConsoleScreenBufferInfo.

Source:
http://www.burgaud.com/bring-colors-to-the-windows-console-with-python/
"""

import sys

if sys.platform == "win32" or sys.platform == "win64":

    # Windows stuff
    from ctypes import windll, Structure, c_short, c_ushort, byref

    SHORT = c_short
    WORD = c_ushort

    class COORD(Structure):

        """struct in wincon.h."""
        _fields_ = [
            ("X", SHORT),
            ("Y", SHORT)]

    class SMALL_RECT(Structure):

        """struct in wincon.h."""
        _fields_ = [
            ("Left", SHORT),
            ("Top", SHORT),
            ("Right", SHORT),
            ("Bottom", SHORT)]

    class CONSOLE_SCREEN_BUFFER_INFO(Structure):

        """struct in wincon.h."""
        _fields_ = [
            ("dwSize", COORD),
            ("dwCursorPosition", COORD),
            ("wAttributes", WORD),
            ("srWindow", SMALL_RECT),
            ("dwMaximumWindowSize", COORD)]

    # winbase.h
    STD_INPUT_HANDLE = -10
    STD_OUTPUT_HANDLE = -11
    STD_ERROR_HANDLE = -12

    # wincon.h
    FOREGROUND_BLACK = 0x0000
    FOREGROUND_BLUE = 0x0001
    FOREGROUND_GREEN = 0x0002
    FOREGROUND_CYAN = 0x0003
    FOREGROUND_RED = 0x0004
    FOREGROUND_MAGENTA = 0x0005
    FOREGROUND_YELLOW = 0x0006
    FOREGROUND_GREY = 0x0007
    FOREGROUND_INTENSITY = 0x0008  # foreground color is intensified.

    BACKGROUND_BLACK = 0x0000
    BACKGROUND_BLUE = 0x0010
    BACKGROUND_GREEN = 0x0020
    BACKGROUND_CYAN = 0x0030
    BACKGROUND_RED = 0x0040
    BACKGROUND_MAGENTA = 0x0050
    BACKGROUND_YELLOW = 0x0060
    BACKGROUND_GREY = 0x0070
    BACKGROUND_INTENSITY = 0x0080  # background color is intensified.

    stdout_handle = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    SetConsoleTextAttribute = windll.kernel32.SetConsoleTextAttribute
    GetConsoleScreenBufferInfo = windll.kernel32.GetConsoleScreenBufferInfo

    def get_text_attr():
        """Returns the character attributes (colors) of the console screen
        buffer."""
        csbi = CONSOLE_SCREEN_BUFFER_INFO()
        GetConsoleScreenBufferInfo(stdout_handle, byref(csbi))
        return csbi.wAttributes

    def set_text_attr(color):
        """Sets the character attributes (colors) of the console screen
        buffer. Color is a combination of foreground and background color,
        foreground and background intensity."""
        SetConsoleTextAttribute(stdout_handle, color)

    def printRedConsoleText(text):
        """ Prints out red text on the console """
        revert = get_text_attr()
        set_text_attr(FOREGROUND_RED | BACKGROUND_BLACK | FOREGROUND_INTENSITY)
        sys.stdout.write(text)
        set_text_attr(revert)

    def printYellowConsoleText(text):
        """ Prints out yellow text on the console """
        revert = get_text_attr()
        set_text_attr(
            FOREGROUND_YELLOW | BACKGROUND_BLACK | FOREGROUND_INTENSITY)
        sys.stdout.write(text)
        set_text_attr(revert)

    def printGrayConsoleText(text):
        """ Prints out gray text on the console """
        revert = get_text_attr()
        set_text_attr(
            FOREGROUND_GREEN | BACKGROUND_BLACK)
        sys.stdout.write(text)
        set_text_attr(revert)

else:

    # Other operating systems (not supported yet)
    def printRedConsoleText(text):
        """ Prints out red text on the console """
        print text,

    def printYellowConsoleText(text):
        """ Prints out yellow text on the console """
        print text,

    def printGrayConsoleText(text):
        """ Prints out gray text on the console """
        print text,