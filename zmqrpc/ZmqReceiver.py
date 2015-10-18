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

class SubSocket():
    def __init__(self, ctx, poller, address, timeout_in_sec=None):
        self.ctx = ctx
        self.poller = poller
        self.address = address
        self.timeout_in_sec = timeout_in_sec
        self.zmq_socket = None
        self.create()
        
    def create(self):
        if not self.zmq_socket:
            self.zmq_socket = self.ctx.socket(zmq.SUB)
            self.zmq_socket.setsockopt(zmq.SUBSCRIBE, '')
            self.zmq_socket.setsockopt(zmq.LINGER, 0)
            if type(self.address) is str: 
                self.zmq_socket.connect(self.address)
            else:
                self.zmq_socket.connect(self.address[0])
                self.timeout_in_sec = self.address[1]
            self.poller.register(self.zmq_socket, zmq.POLLIN)
            self.last_received_bytes = time.time()
            logger.debug("Created SUB socket to {0}".format(self.address))
        
    def destroy(self):
        if self.zmq_socket:
            self.poller.unregister(self.zmq_socket)
            address = self.address
            if type(address) is tuple:
                address = address[0]
            # Since some recent version of pyzmq it does not accept unbind
            # of an address with '*'. Replace it with 0.0.0.0
            if '*' in address:
                address = address.replace('*', '0.0.0.0')
            self.zmq_socket.disconnect(address)
            self.zmq_socket.close()
            while not self.zmq_socket.closed:
                time.sleep(1)
            self.zmq_socket = None
            logger.debug("Destroyed SUB socket bound to {0}".format(self.address))

    def recv(self, socks):
        if self.zmq_socket is not None and (socks.get(self.zmq_socket) == zmq.POLLIN):
            result = self.zmq_socket.recv()
            self.last_received_bytes = time.time()
            return result
        if (self.timeout_in_sec is not None) and time.time() > self.last_received_bytes + self.timeout_in_sec:
            # Recreate sockets
            logger.warn("Heartbeat timeout exceeded. Recreating SUB socket to {0}".format(self.address))
            self.destroy()
            self.create()
        return None

class RepSocket():
    def __init__(self, ctx, poller, address, auth):
        self.ctx = ctx
        self.poller = poller
        self.address = address
        self.auth = auth
        self.zmq_socket = None
        self.create()
        
    def create(self):
        if not self.zmq_socket:
            self.zmq_socket = self.ctx.socket(zmq.REP)
            self.zmq_socket.setsockopt(zmq.LINGER, 0)
            if self.auth:
                self.zmq_socket.plain_server = True
            self.zmq_socket.bind(self.address)
            self.poller.register(self.zmq_socket, zmq.POLLIN)
            logger.debug("Created REP socket bound to {0}".format(self.address))
        
    def destroy(self):
        if self.zmq_socket:
            self.poller.unregister(self.zmq_socket)
            address = self.address
            # Since some recent version of pyzmq it does not accept unbind
            # of an address with '*'. Replace it with 0.0.0.0
            if '*' in address:
                address = address.replace('*', '0.0.0.0')
            self.zmq_socket.unbind(address)
            self.zmq_socket.close()
            while not self.zmq_socket.closed:
                time.sleep(1)
            self.zmq_socket = None
            logger.debug("Destroyed REP socket bound to {0}".format(self.address))

    def recv(self, socks):
        if self.zmq_socket is not None and (socks.get(self.zmq_socket) == zmq.POLLIN):
            result = self.zmq_socket.recv()
            self.last_received_bytes = time.time()
            return result
        return None
    
    def send(self, message):
        if self.zmq_socket is not None and message is not None:
            self.zmq_socket.send(message)
            

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
        self.poller = zmq.Poller()
        self.sub_sockets = []
        self.rep_socket = None
        if username is not None and password is not None:
            # Start an authenticator for this context.
            # Does not work on PUB/SUB as far as I (probably because the more secure solutions
            # require two way communication as well)
            self.auth = ThreadAuthenticator(self.context)
            self.auth.start()
            # Instruct authenticator to handle PLAIN requests
            self.auth.configure_plain(domain='*', passwords={username: password})
            
        if self.zmq_sub_connect_addresses:
            for address in self.zmq_sub_connect_addresses:
                self.sub_sockets.append(SubSocket(self.context, self.poller, address, recreate_sockets_on_timeout_of_sec))
        if zmq_rep_bind_address:
            self.rep_socket = RepSocket(self.context, self.poller, zmq_rep_bind_address, self.auth)

    # May take up to 60 seconds to actually stop since poller has timeout of 60 seconds
    def stop(self):
        self.is_running = False
        logger.info("Closing pub and sub sockets...")
        if self.auth is not None:
            self.auth.stop()

    def run(self):
        self.is_running = True

        while self.is_running:
            socks = dict(self.poller.poll(1000))
            logger.debug("Poll cycle over. checking sockets")
            if self.rep_socket:
                incoming_message = self.rep_socket.recv(socks)
                if incoming_message is not None:
                    self.last_received_message = incoming_message
                    try:
                        logger.debug("Got info from REP socket")
                        response_message = self.handle_incoming_message(incoming_message)
                        self.rep_socket.send(response_message)
                    except Exception as e:
                        logger.error(e)
            for sub_socket in self.sub_sockets:
                incoming_message = sub_socket.recv(socks)
                if incoming_message is not None:
                    self.last_received_message = incoming_message
                    logger.debug("Got info from SUB socket")
                    try:
                        self.handle_incoming_message(incoming_message)
                    except Exception as e:
                        logger.error(e)

        if self.rep_socket:
            self.rep_socket.destroy()
        for sub_socket in self.sub_sockets:
            sub_socket.destroy()

    def create_response_message(self, status_code, status_message, response_message):
        if response_message is not None:
            return json.dumps({"status_code": status_code, "status_message": status_message, "response_message": response_message})
        else:
            return json.dumps({"status_code": status_code, "status_message": status_message})

    def handle_incoming_message(self, message):
        if message != "zmq_sub_heartbeat":
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
