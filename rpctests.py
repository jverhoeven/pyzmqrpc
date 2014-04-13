'''
Created on Mar 31, 2014

@author: Jan Verhoeven

@copyright: MIT license, see http://opensource.org/licenses/MIT

'''
from zmqrpc.ZmqProxy import ZmqProxyRep2PubThread, ZmqProxySub2ReqThread, ZmqProxyRep2ReqThread, ZmqProxySub2PubThread
from zmqrpc.ZmqReceiver import ZmqReceiverThread
from zmqrpc.ZmqSender import ZmqSender
from zmqrpc.ZmqRpcServer import ZmqRpcServerThread
from zmqrpc.ZmqRpcClient import ZmqRpcClient
import time
import unittest


# Track state from invoking method in a special class since this is in global scope.
class TestState():
    def __init__(self):
        self.last_invoked_param1 = None

test_state = TestState()


def invoke_test(param1, param2):
    test_state.last_invoked_param1 = param1
    return "{0}:{1}".format(param1, param2)


class TestZmqPackage(unittest.TestCase):
    def testReqRepSockets(self):
        # Basic send/receive over REQ/REP sockets
        print "Test if sending works over REQ/REP socket, includes a username/password"
        sender = ZmqSender(zmq_req_endpoints=["tcp://localhost:7000"], username="username", password="password")
        receiver_thread = ZmqReceiverThread(zmq_rep_bind_address="tcp://*:7000", username="username", password="password")
        receiver_thread.start()

        sender.send("test", time_out_waiting_for_response_in_sec=3)

        self.assertEquals(receiver_thread.last_received_message(), 'test')

        print "Test if sending wrong password over REP/REQ connection results in error (actually timeout)"
        sender = ZmqSender(zmq_req_endpoints=["tcp://localhost:7000"], username="username", password="wrongpassword")
        try:
            sender.send("test", time_out_waiting_for_response_in_sec=3)
            print "Error. Did get answer from remote system which was not expected"
        except:
            # Could not send message, which is ok in this case
            print "Success."

        receiver_thread.stop()
        receiver_thread.join()
        sender.destroy()
        # Cleaning up sockets takes some time
        time.sleep(1)

    def test_pub_sub_without_passwords(self):
        # Basic send/receive over PUB/SUB sockets
        print "Test if sending works over PUB/SUB sockets without passwords"
        sender = ZmqSender(zmq_pub_endpoint="tcp://*:7000")
        receiver_thread = ZmqReceiverThread(zmq_sub_connect_addresses=["tcp://localhost:7000"])
        receiver_thread.start()
        # Take 0.5 second for sockets to connect to prevent 'slow joiner' problem
        time.sleep(0.5)

        sender.send("test")
        # Sleep for pub/sub not guaranteed to be done on completing send_pub_socket
        time.sleep(0.1)

        self.assertEqual(receiver_thread.last_received_message(), 'test')

        receiver_thread.stop()
        receiver_thread.join()
        sender.destroy()
        # Cleaning up sockets takes some time
        time.sleep(1)

    def test_proxy(self):
        # With proxy elements
        print "Add a proxy setup to the end to end chain pub->proxy.req->proxy.rep->pub->sub"
        sender = ZmqSender(zmq_pub_endpoint="tcp://*:7000")

        proxy_sub_req_thread = ZmqProxySub2ReqThread(zmq_sub_connect_addresses=['tcp://localhost:7000'], zmq_req_connect_addresses=["tcp://localhost:7001"], username_req="username", password_req="password")
        proxy_sub_req_thread.start()

        proxy_rep_pub_thread = ZmqProxyRep2PubThread(zmq_rep_bind_address='tcp://*:7001', zmq_pub_bind_address='tcp://*:7002', username_rep="username", password_rep="password")
        proxy_rep_pub_thread.start()

        receiver_thread = ZmqReceiverThread(zmq_sub_connect_addresses=["tcp://localhost:7002"])
        receiver_thread.start()
        # Take 0.5 second for sockets to connect to prevent 'slow joiner' problem
        time.sleep(0.5)

        sender.send("test")
        # Sleep for pub/sub not guaranteed to be done on completing send_pub_socket
        time.sleep(1)
        print "last received message by proxy_sub_req_thread: {0}".format(proxy_sub_req_thread.last_received_message())
        print "last received message by proxy_rep_pub_thread: {0}".format(proxy_rep_pub_thread.last_received_message())
        print "last received message by receiver_thread: {0}".format(receiver_thread.last_received_message())

        self.assertEqual(receiver_thread.last_received_message(), 'test')

        receiver_thread.stop()
        receiver_thread.join()
        proxy_sub_req_thread.stop()
        proxy_sub_req_thread.join()
        proxy_rep_pub_thread.stop()
        proxy_rep_pub_thread.join()
        sender.destroy()
        # Cleaning up sockets takes some time
        time.sleep(1)

    def test_rpc1_req_rep(self):
        # RPC invoke method over REQ/REP sockets
        print "Test if invoking a method works over REQ/REP RPC socket, includes a username/password"
        client = ZmqRpcClient(zmq_req_endpoints=["tcp://localhost:7000"], username="username", password="password")
        server_thread = ZmqRpcServerThread(zmq_rep_bind_address="tcp://*:7000", rpc_functions={"invoke_test": invoke_test}, username="username", password="password")
        server_thread.start()

        response = client.invoke(function_name="invoke_test", function_parameters={"param1": "value1", "param2": "value2"}, time_out_waiting_for_response_in_sec=3)

        server_thread.stop()
        server_thread.join()
        client.destroy()
        # Cleaning up sockets takes some time
        time.sleep(1)

        self.assertEquals(response, "value1:value2")

    def test_rpc1_pub_sub(self):
        # RPC invoke method over REQ/REP sockets
        print "Test if invoking a method works over PUB/SUB RPC socket"
        client = ZmqRpcClient(zmq_pub_endpoint="tcp://*:7000")
        server_thread = ZmqRpcServerThread(zmq_sub_connect_addresses=["tcp://localhost:7000"], rpc_functions={"invoke_test": invoke_test}, username="username", password="password")
        server_thread.start()

        # Wait a bit to avoid slow joiner...
        time.sleep(1)

        response = client.invoke(function_name="invoke_test", function_parameters={"param1": "value1sub", "param2": "value2pub"}, time_out_waiting_for_response_in_sec=3)

        # Wait a bit to make sure message is sent...
        time.sleep(1)

        server_thread.stop()
        server_thread.join()
        client.destroy()
        # Cleaning up sockets takes some time
        time.sleep(1)

        # Response should be empty with PUB/SUB
        self.assertEquals(response, None)
        self.assertEquals(test_state.last_invoked_param1, "value1sub")

    def test_rpc1_req_rep_with_rep_req_proxy(self):
        # RPC invoke method over REQ/REP sockets with an extra rep/req proxy in between
        print "Test if invoking a method works over REQ/REP RPC socket, includes a username/password and also an extra rep/req proxy"

        client = ZmqRpcClient(zmq_req_endpoints=["tcp://localhost:7000"], username="username", password="password")

        proxy_rep_req_thread = ZmqProxyRep2ReqThread(zmq_rep_bind_address='tcp://*:7000', zmq_req_connect_addresses=["tcp://localhost:7001"], username_rep="username", password_rep="password", username_req="username2", password_req="password2")
        proxy_rep_req_thread.start()

        server_thread = ZmqRpcServerThread(zmq_rep_bind_address="tcp://*:7001", rpc_functions={"invoke_test": invoke_test}, username="username2", password="password2")
        server_thread.start()

        response = client.invoke(function_name="invoke_test", function_parameters={"param1": "value1", "param2": "value2"}, time_out_waiting_for_response_in_sec=3)

        server_thread.stop()
        server_thread.join()
        proxy_rep_req_thread.stop()
        proxy_rep_req_thread.join()
        client.destroy()
        # Cleaning up sockets takes some time
        time.sleep(1)

        self.assertEquals(response, "value1:value2")

    def test_rpc1_pub_sub_with_pub_sub_proxy(self):
        # RPC invoke method over PUB/SUB sockets and a PUB/SUB proxy
        print "Test if invoking a method works over PUB/SUB RPC socket and a PUB/SUB proxy in between"
        server_thread = ZmqRpcServerThread(zmq_sub_connect_addresses=["tcp://localhost:7001"], rpc_functions={"invoke_test": invoke_test})
        server_thread.start()

        proxy_pub_sub_thread = ZmqProxySub2PubThread(zmq_pub_bind_address="tcp://*:7001", zmq_sub_connect_addresses=['tcp://localhost:7000'])
        proxy_pub_sub_thread.start()

        client = ZmqRpcClient(zmq_pub_endpoint="tcp://*:7000")
        # Wait a bit to avoid slow joiner...
        time.sleep(1)

        response = client.invoke(function_name="invoke_test", function_parameters={"param1": "value2sub", "param2": "value2pub"}, time_out_waiting_for_response_in_sec=3)

        # Wait a bit to make sure message is sent...
        time.sleep(1)

        server_thread.stop()
        server_thread.join()
        proxy_pub_sub_thread.stop()
        proxy_pub_sub_thread.join()
        client.destroy()
        # Cleaning up sockets takes some time
        time.sleep(1)

        # Response should be empty with PUB/SUB
        self.assertEquals(response, None)
        self.assertEquals(test_state.last_invoked_param1, "value2sub")

if __name__ == '__main__':
    unittest.main()
