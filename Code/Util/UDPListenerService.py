
import socket
import thread

class UDPListenerService(object):

    """ This class provides a simple server and client interface to send pings
    via the local network. It is mainly used to dynamically update the pipeline
    settings after they got changed by the Plugin Configurator. """

    DEFAULT_PORT = 62323
    
    @staticmethod
    def ping_location(port, message="PING"):
        """ Sends a given message to a given port and immediately returns """
        print("Pinging localhost:" + str(port))
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
    def listener_thread(cls, port, callback):
        """ Starts a new thread listening to the given port """
        thread.start_new_thread(cls.do_listen, (port, callback))


if __name__ == "__main__":

    # Example usage:

    if True:
        # Client
        UDPListenerService.ping_location(UDPListenerService.DEFAULT_PORT)
    else:
        # Server
        def callback(msg):
            print("MSG:", msg)

        UDPListenerService.listener_thread(UDPListenerService.DEFAULT_PORT, callback)

        while True: pass
