"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

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
#
import socket
from threading import Thread

class UDPListenerService(object):

    """ This class provides a simple server and client interface to send pings
    via the local network. It is mainly used to dynamically update the pipeline
    settings after they got changed by the various configurators. """

    CONFIG_PORT = 62324
    DAYTIME_PORT = 62325

    @staticmethod
    def do_ping(port, message="PING"):
        """ Sends a given message to a given port and immediately returns """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(message, ("127.0.0.1", port))
        finally:
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
            sock.close()

    @classmethod
    def ping_thread(cls, port, message):
        """ Starts a new thread which sends a given message to a port """
        thread = Thread(target=cls.do_ping, args=(port, message), name="UDPPingThread")
        thread.setDaemon(True)
        thread.start()
        return thread

    @classmethod
    def listener_thread(cls, port, callback):
        """ Starts a new thread listening to the given port """
        thread = Thread(target=cls.do_listen, args=(port, callback), name="UDPListenerThread")
        thread.setDaemon(True)
        thread.start()
        return thread
