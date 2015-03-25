'''
Created on Apr 8, 2014

@author: Jan Verhoeven

@copyright: MIT license, see http://opensource.org/licenses/MIT
'''
import zmq
import zmq.auth
from zmq.auth.thread import ThreadAuthenticator
import json
import logging
import time
from threading import Thread

logger = logging.getLogger("zmqrpc")


# A ZmqReceiver class will listen on a REP or SUB socket for messages and will invoke a 'HandleIncomingMessage'
# method to process it. Subclasses should override that. A response must be implemented for REP sockets, but
# is useless for SUB sockets.
class ZmqReceiver():
    def __init__(self, zmq_rep_bind_address=None, zmq_sub_connect_addresses=None, recreate_sockets_on_timeout_of_sec=600, username=None, password=None):
        self.context = zmq.Context()
        self.auth = None
        self.last_received_message = None
        self.is_running = False
        self.thread = None
        self.zmq_rep_bind_address = zmq_rep_bind_address
        self.zmq_sub_connect_addresses = zmq_sub_connect_addresses
        self.recreate_sockets_on_timeout_of_sec = recreate_sockets_on_timeout_of_sec
        if username is not None and password is not None:
            # Start an authenticator for this context.
            # Does not work on PUB/SUB as far as I (probably because the more secure solutions
            # require two way communication as well)
            self.auth = ThreadAuthenticator(self.context)
            self.auth.start()
            # Instruct authenticator to handle PLAIN requests
            self.auth.configure_plain(domain='*', passwords={username: password})

    # May take up to 60 seconds to actually stop since poller has timeout of 60 seconds
    def stop(self):
        self.is_running = False
        logger.info("Closing pub and sub sockets...")
        if self.auth is not None:
            self.auth.stop()

    def run(self):
        self.is_running = True
        rep_socket = None
        sub_socket = None
        last_received_sample_timestamp = time.time()

        poller = zmq.Poller()
        create_new_socket_and_poller = True
        while self.is_running:
            # In case of any socket and poller errors: recreate them. Seems to be the only right way in ZeroMQ.
            if create_new_socket_and_poller:
                logger.debug("Creating new socket and poller")
                if rep_socket is not None:
                    poller.unregister(rep_socket)
                    rep_socket.setsockopt(zmq.LINGER, 0)
                    rep_socket.unbind(self.zmq_rep_bind_address)
                    rep_socket.close()
                    rep_socket = None
                    # For some reason, the req_socket binding lasts a bit longer than a couple of milliseconds, so give it a second or so to disconnect
                    time.sleep(1)
                if sub_socket is not None:
                    poller.unregister(sub_socket)
                    sub_socket.setsockopt(zmq.LINGER, 0)
                    for address in self.zmq_sub_connect_addresses:
                        sub_socket.disconnect(address)
                    sub_socket.close()
                    while not sub_socket.closed:
                        time.sleep(1)
                    sub_socket = None
                # Don't try to catch the exception in the following block: If it fails, it should be noted to the calling function via standard exceptions:
                if self.zmq_rep_bind_address is not None:
                    rep_socket = self.context.socket(zmq.REP)
                    if self.auth:
                        rep_socket.plain_server = True
                    rep_socket.bind(self.zmq_rep_bind_address)
                    poller.register(rep_socket, zmq.POLLIN)
                if self.zmq_sub_connect_addresses is not None:
                    sub_socket = self.context.socket(zmq.SUB)
                    sub_socket.setsockopt(zmq.SUBSCRIBE, '')
                    for address in self.zmq_sub_connect_addresses:
                        sub_socket.connect(address)
                    poller.register(sub_socket, zmq.POLLIN)
                create_new_socket_and_poller = False
                last_received_sample_timestamp = time.time()

            socks = dict(poller.poll(1000))
            incoming_message = None
            socket = None
            if socks.get(rep_socket) == zmq.POLLIN:
                last_received_sample_timestamp = time.time()
                socket = rep_socket
            elif socks.get(sub_socket) == zmq.POLLIN:
                last_received_sample_timestamp = time.time()
                socket = sub_socket
            else:
                # This code exists due to a bug in the library for ARM devices where one subscription can block another
                if time.time() > last_received_sample_timestamp + self.recreate_sockets_on_timeout_of_sec:
                    logger.debug("No new messages received since {0} seconds. Re-establishing subcriptions".format(self.recreate_sockets_on_timeout_of_sec))
                    create_new_socket_and_poller = True

            if socket is not None:
                try:
                    incoming_message = socket.recv()
                    self.last_received_message = incoming_message
                except Exception as e:
                    create_new_socket_and_poller = True
                    logger.error(e)
                else:
                    response_message = self.handle_incoming_message(socket, incoming_message)

            if rep_socket and socket == rep_socket:
                # Only send answers for reply sockets
                try:
                    if response_message is not None:
                        rep_socket.send(response_message)
                except Exception as e:
                    logger.error("Could not send message over socket. Recreating all sockets {0}".format(e))
                    create_new_socket_and_poller = True

        if rep_socket:
            rep_socket.close()
        if sub_socket:
            sub_socket.close()

    def create_response_message(self, status_code, status_message, response_message):
        if response_message is not None:
            return json.dumps({"status_code": status_code, "status_message": status_message, "response_message": response_message})
        else:
            return json.dumps({"status_code": status_code, "status_message": status_message})

    def handle_incoming_message(self, socket, message):
        return self.create_response_message(200, "OK", None)


class ZmqReceiverThread(Thread):
    def __init__(self, zmq_rep_bind_address=None, zmq_sub_connect_addresses=None, recreate_sockets_on_timeout_of_sec=60, username=None, password=None):
        Thread.__init__(self)
        self.receiver = ZmqReceiver(zmq_rep_bind_address=zmq_rep_bind_address, zmq_sub_connect_addresses=zmq_sub_connect_addresses, recreate_sockets_on_timeout_of_sec=recreate_sockets_on_timeout_of_sec, username=username, password=password)

    def last_received_message(self):
        return self.receiver.last_received_message

    def run(self):
        self.receiver.run()

    def stop(self):
        self.receiver.stop()
