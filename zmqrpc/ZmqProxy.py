'''
Created on Apr 8, 2014

@author: Jan Verhoeven

@copyright: MIT license, see http://opensource.org/licenses/MIT
'''
from ZmqReceiver import ZmqReceiver
from ZmqSender import ZmqSender
from threading import Thread
import logging

logger = logging.getLogger("zmqrpc")


# This class implements a simple message forwarding from a PUB/SUB connection to a
# REQ/REP connection.
class ZmqProxySub2Req(ZmqReceiver):
    # Note, at the moment username/password only protects the REQ-REP socket connection
    def __init__(self, zmq_sub_connect_addresses, zmq_req_connect_addresses, recreate_sockets_on_timeout_of_sec=600, username_sub=None, password_sub=None, username_req=None, password_req=None):
        ZmqReceiver.__init__(self, zmq_sub_connect_addresses=zmq_sub_connect_addresses, recreate_sockets_on_timeout_of_sec=recreate_sockets_on_timeout_of_sec, username=username_sub, password=password_sub)
        self.sender = ZmqSender(zmq_req_endpoints=zmq_req_connect_addresses, username=username_req, password=password_req)

    def handle_incoming_message(self, socket, message):
        # We don't care for the response, since we cannot pass it back via the pub socket or we got none from a pub socket
        try:
            self.sender.send(message, time_out_waiting_for_response_in_sec=60)
        except Exception as e:
            logger.error(e)
        return None


# This class implements a simple message forwarding from a PUB/SUB connection to another
# PUB/SUB connection. Could be used to aggregate messages into one end-point.
class ZmqProxySub2Pub(ZmqReceiver):
    # Note, at the moment username/password only protects the REQ-REP socket connection
    def __init__(self, zmq_sub_connect_addresses, zmq_pub_bind_address, recreate_sockets_on_timeout_of_sec=600, username_sub=None, password_sub=None, username_pub=None, password_pub=None):
        ZmqReceiver.__init__(self, zmq_sub_connect_addresses=zmq_sub_connect_addresses, recreate_sockets_on_timeout_of_sec=recreate_sockets_on_timeout_of_sec, username=username_sub, password=password_sub)
        self.sender = ZmqSender(zmq_pub_endpoint=zmq_pub_bind_address, username=username_pub, password=username_pub)

    def handle_incoming_message(self, socket, message):
        # We don't care for the response, since we cannot pass it back via the pub socket or we got none from a pub socket
        try:
            self.sender.send(message, time_out_waiting_for_response_in_sec=60)
        except Exception as e:
            logger.error(e)
        return None


# This class implements a simple message forwarding from a REQ/REP connection to a
# PUB/SUB connection.
class ZmqProxyRep2Pub(ZmqReceiver):
    # Note, at the moment username/password only protects the REQ-REP socket connection
    def __init__(self, zmq_rep_bind_address, zmq_pub_bind_address, recreate_sockets_on_timeout_of_sec=600, username_rep=None, password_rep=None, username_pub=None, password_pub=None):
        ZmqReceiver.__init__(self, zmq_rep_bind_address=zmq_rep_bind_address, recreate_sockets_on_timeout_of_sec=recreate_sockets_on_timeout_of_sec, username=username_rep, password=password_rep)
        self.sender = ZmqSender(zmq_req_endpoints=None, zmq_pub_endpoint=zmq_pub_bind_address, username=username_pub, password=password_pub)

    def handle_incoming_message(self, socket, message):
        try:
            self.sender.send(message, time_out_waiting_for_response_in_sec=60)
            # Pub socket does not provide response message, so return OK message
            return self.create_response_message(200, "OK", None)
        except Exception as e:
            return self.create_response_message(status_code=400, status_message="Error", response_message=e)


# This class implements a simple message forwarding from a REQ/REP connection to another
# REQ/REP connection.
class ZmqProxyRep2Req(ZmqReceiver):
    # Note, at the moment username/password only protects the REQ-REP socket connection
    def __init__(self, zmq_rep_bind_address, zmq_req_connect_addresses, recreate_sockets_on_timeout_of_sec=600, username_rep=None, password_rep=None, username_req=None, password_req=None):
        ZmqReceiver.__init__(self, zmq_rep_bind_address=zmq_rep_bind_address, recreate_sockets_on_timeout_of_sec=recreate_sockets_on_timeout_of_sec, username=username_rep, password=password_rep)
        self.sender = ZmqSender(zmq_req_endpoints=zmq_req_connect_addresses, username=username_req, password=password_req)

    def handle_incoming_message(self, socket, message):
        # Pass on the response from the forwarding socket.
        try:
            response_message = self.sender.send(message, time_out_waiting_for_response_in_sec=60)
            return self.create_response_message(status_code=200, status_message="OK", response_message=response_message)
        except Exception as e:
            return self.create_response_message(status_code=400, status_message="Error", response_message=e)


class ZmqProxyThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.proxy = None

    def last_received_message(self):
        if self.proxy:
            return self.proxy.last_received_message
        return None

    def run(self):
        if self.proxy:
            self.proxy.run()

    def stop(self):
        if self.proxy:
            self.proxy.stop()


class ZmqProxySub2ReqThread(ZmqProxyThread):
    def __init__(self, zmq_sub_connect_addresses=None, zmq_req_connect_addresses=None, recreate_sockets_on_timeout_of_sec=600, username_sub=None, password_sub=None, username_req=None, password_req=None):
        ZmqProxyThread.__init__(self)
        self.proxy = ZmqProxySub2Req(zmq_sub_connect_addresses=zmq_sub_connect_addresses, zmq_req_connect_addresses=zmq_req_connect_addresses, recreate_sockets_on_timeout_of_sec=recreate_sockets_on_timeout_of_sec, username_sub=username_sub, password_sub=password_sub, username_req=username_req, password_req=password_req)


class ZmqProxySub2PubThread(ZmqProxyThread):
    def __init__(self, zmq_sub_connect_addresses=None, zmq_pub_bind_address=None, recreate_sockets_on_timeout_of_sec=600, username_sub=None, password_sub=None, username_pub=None, password_pub=None):
        ZmqProxyThread.__init__(self)
        self.proxy = ZmqProxySub2Pub(zmq_sub_connect_addresses=zmq_sub_connect_addresses, zmq_pub_bind_address=zmq_pub_bind_address, recreate_sockets_on_timeout_of_sec=recreate_sockets_on_timeout_of_sec, username_sub=username_sub, password_sub=password_sub, username_pub=username_pub, password_pub=password_pub)


class ZmqProxyRep2PubThread(ZmqProxyThread):
    def __init__(self, zmq_rep_bind_address=None, zmq_pub_bind_address=None, recreate_sockets_on_timeout_of_sec=600, username_rep=None, password_rep=None, username_pub=None, password_pub=None):
        ZmqProxyThread.__init__(self)
        self.proxy = ZmqProxyRep2Pub(zmq_rep_bind_address=zmq_rep_bind_address, zmq_pub_bind_address=zmq_pub_bind_address, recreate_sockets_on_timeout_of_sec=recreate_sockets_on_timeout_of_sec, username_rep=username_rep, password_rep=password_rep, username_pub=username_pub, password_pub=password_pub)


class ZmqProxyRep2ReqThread(ZmqProxyThread):
    def __init__(self, zmq_rep_bind_address=None, zmq_req_connect_addresses=None, recreate_sockets_on_timeout_of_sec=600, username_rep=None, password_rep=None, username_req=None, password_req=None):
        ZmqProxyThread.__init__(self)
        self.proxy = ZmqProxyRep2Req(zmq_rep_bind_address=zmq_rep_bind_address, zmq_req_connect_addresses=zmq_req_connect_addresses, recreate_sockets_on_timeout_of_sec=recreate_sockets_on_timeout_of_sec, username_rep=username_rep, password_rep=password_rep, username_req=username_req, password_req=password_req)


# This proxy class uses a 'hidden' pub/sub socket to buffer any messages from REP to REQ socket 
# in case the REQ socket is offline.
class ZmqBufferedProxyRep2ReqThread(ZmqProxyThread):
    def __init__(self, zmq_rep_bind_address=None, zmq_req_connect_addresses=None, buffered_pub_address="tcp://*:59878", buffered_sub_address="tcp://localhost:59878", recreate_sockets_on_timeout_of_sec=600, username_rep=None, password_rep=None, username_req=None, password_req=None):
        ZmqProxyThread.__init__(self)
        self.proxy1 = ZmqProxyRep2PubThread(zmq_rep_bind_address=zmq_rep_bind_address, zmq_pub_bind_address=buffered_pub_address, recreate_sockets_on_timeout_of_sec=100000, username_rep=username_rep, password_rep=password_rep)
        self.proxy2 = ZmqProxySub2ReqThread(zmq_sub_connect_addresses=[buffered_sub_address], zmq_req_connect_addresses=zmq_req_connect_addresses, recreate_sockets_on_timeout_of_sec=recreate_sockets_on_timeout_of_sec, username_req=username_req, password_req=password_req)

    def start(self):
        self.proxy1.start()
        self.proxy2.start()
        super(ZmqProxyThread, self).start()

    def stop(self):
        self.proxy1.stop()
        self.proxy2.stop()

    def join(self):
        self.proxy1.join()
        self.proxy2.join()
        super(ZmqProxyThread, self).join()
