
import socket
from threading import Thread

class UDPListenerService(object):

    """ This class provides a simple server and client interface to send pings
    via the local network. It is mainly used to dynamically update the pipeline
    settings after they got changed by the Plugin Configurator. """

    DEFAULT_PORT = 62323
    
    @staticmethod
    def do_ping(port, message="PING"):
        """ Sends a given message to a given port and immediately returns """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(message, ("127.0.0.1", port))
        finally:
            sock.shutdown(1)
            sock.close()

    @staticmethod
    def do_listen(port, callback):
        """ Listens to a given port, and calls callback in case a message
        arrives """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))

            while True:
                data, addr = sock.recvfrom(1024)
                callback(data)

        finally:
            sock.shutdown(1)
            sock.close()

    @classmethod
    def ping_thread(cls, port, message):
        """ Starts a new thread which sends a given message to a port """
        t = Thread(target=cls.do_ping, args=(port, message))
        t.start()

    @classmethod
    def listener_thread(cls, port, callback):
        """ Starts a new thread listening to the given port """
        t = Thread(target=cls.do_listen, args=(port, callback))
        t.start()
