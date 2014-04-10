'''
Created on Apr 8, 2014

@author: Jan Verhoeven

@copyright: MIT license, see http://opensource.org/licenses/MIT
'''
from ZmqReceiver import ZmqReceiver
from ZmqSender import ZmqSender
from threading import Thread


# This class implements a simple message forwarding from a PUB/SUB connection to a
# REQ/REP connection.
class ZmqProxySub2Req(ZmqReceiver):
    # Note, at the moment username/password only protects the REQ-REP socket connection
    def __init__(self, zmq_sub_connect_addresses, zmq_req_connect_addresses, recreate_sockets_on_timeout_of_sec=60, username_sub=None, password_sub=None, username_req=None, password_req=None):
        ZmqReceiver.__init__(self, zmq_sub_connect_addresses=zmq_sub_connect_addresses, recreate_sockets_on_timeout_of_sec=recreate_sockets_on_timeout_of_sec, username=username_sub, password=password_sub)
        self.sender = ZmqSender(zmq_req_endpoints=zmq_req_connect_addresses, username=username_req, password=password_req)

    def handle_incoming_message(self, socket, message):
        # We don't care for the response, since we cannot pass it back via the pub socket or we got none from a pub socket
        self.sender.send(message, time_out_waiting_for_response_in_sec=60)
        return None


# This class implements a simple message forwarding from a REQ/REP connection to a
# PUB/SUB connection.
class ZmqProxyRep2Pub(ZmqReceiver):
    # Note, at the moment username/password only protects the REQ-REP socket connection
    def __init__(self, zmq_rep_bind_address, zmq_pub_bind_address, recreate_sockets_on_timeout_of_sec=60, username_rep=None, password_rep=None, username_pub=None, password_pub=None):
        ZmqReceiver.__init__(self, zmq_rep_bind_address=zmq_rep_bind_address, recreate_sockets_on_timeout_of_sec=recreate_sockets_on_timeout_of_sec, username=username_rep, password=password_rep)
        self.sender = ZmqSender(zmq_req_endpoints=None, zmq_pub_endpoint=zmq_pub_bind_address, username=username_pub, password=password_pub)

    def handle_incoming_message(self, socket, message):
        self.sender.send(message, time_out_waiting_for_response_in_sec=60)
        # Pub socket does not provide response message, so return OK message
        return self.create_response_message(200, "OK", None)


class ZmqProxySub2ReqThread(Thread):
    def __init__(self, zmq_sub_connect_addresses=None, zmq_req_connect_addresses=None, recreate_sockets_on_timeout_of_sec=60, username_sub=None, password_sub=None, username_req=None, password_req=None):
        Thread.__init__(self)
        self.proxy = ZmqProxySub2Req(zmq_sub_connect_addresses=zmq_sub_connect_addresses, zmq_req_connect_addresses=zmq_req_connect_addresses, recreate_sockets_on_timeout_of_sec=recreate_sockets_on_timeout_of_sec, username_sub=username_sub, password_sub=password_sub, username_req=username_req, password_req=password_req)

    def last_received_message(self):
        return self.proxy.last_received_message

    def run(self):
        self.proxy.run()

    def stop(self):
        self.proxy.stop()


class ZmqProxyRep2PubThread(Thread):
    def __init__(self, zmq_rep_bind_address=None, zmq_pub_bind_address=None, recreate_sockets_on_timeout_of_sec=60, username_rep=None, password_rep=None, username_pub=None, password_pub=None):
        Thread.__init__(self)
        self.proxy = ZmqProxyRep2Pub(zmq_rep_bind_address=zmq_rep_bind_address, zmq_pub_bind_address=zmq_pub_bind_address, recreate_sockets_on_timeout_of_sec=recreate_sockets_on_timeout_of_sec, username_rep=username_rep, password_rep=password_rep, username_pub=username_pub, password_pub=password_pub)

    def last_received_message(self):
        return self.proxy.last_received_message

    def run(self):
        self.proxy.run()

    def stop(self):
        self.proxy.stop()
