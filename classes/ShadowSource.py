

class ShadowSource:

    def __init__(self):
        self.valid = True

    def invalidate(self):
        self.valid = False

    def isValid(self):
        return self.valid

    


            