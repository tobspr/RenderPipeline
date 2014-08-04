

class AbstractMethodException(Exception):

    """ This exception is thrown when somebody tries to
    call an abstract function """

    def __init__(self):
        Exception.__init__(self, "This is an abstract method."
                           "You can't call it. Either the subclass "
                           "does not implement it, or you are calling "
                           "it on the base class (you should not do that).")
