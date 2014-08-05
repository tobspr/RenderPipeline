
from BetterCheckbox import BetterCheckbox
from BetterOnscreenText import BetterOnscreenText


class CheckboxWithLabel:

    def __init__(self, parent=None, x=0, y=0, chbCallback=None, 
            chbArgs=None, chbChecked=True, text="", textSize=15):

        if chbArgs is None:
            chbArgs = []

        self.checkbox = BetterCheckbox(
            parent=parent, x=x, y=y,
            callback=chbCallback, extraArgs=chbArgs,
            checked=chbChecked)
        self.text = BetterOnscreenText(x=x + 20, y=y+7 + textSize/3, text=text,
            align="left", parent=parent, size=textSize)

    def getCheckbox(self):
        return self.checkbox

    def getLabel(self):
        return self.text