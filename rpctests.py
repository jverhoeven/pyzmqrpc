'''
Created on Mar 31, 2014

@author: Jan Verhoeven

@copyright: MIT license, see http://opensource.org/licenses/MIT

'''
from zmqrpc.ZmqProxy import ZmqProxyRep2PubThread, ZmqProxySub2ReqThread, ZmqProxyRep2ReqThread, ZmqProxySub2PubThread, ZmqBufferedProxyRep2ReqThread
from zmqrpc.ZmqReceiver import ZmqReceiverThread
from zmqrpc.ZmqSender import ZmqSender
from zmqrpc.ZmqRpcServer import ZmqRpcServerThread
from zmqrpc.ZmqRpcClient import ZmqRpcClient
import time
import unittest
import logging

logger = logging.getLogger('zmqrpc')
logger.setLevel(logging.DEBUG)

# Track state from invoking method in a special class since this is in global scope.
class TestState():
    def __init__(self):
        self.last_invoked_param1 = None

test_state = TestState()


def invoke_test(param1, param2):
    test_state.last_invoked_param1 = param1
    return "{0}:{1}".format(param1, param2)

def invoke_test_that_throws_exception(param1, param2):
    raise Exception("Something went wrong")


class TestZmqPackage(unittest.TestCase):
    def test_01_req_rep_sockets(self):
        # Basic send/receive over REQ/REP sockets
        print "Test if sending works over REQ/REP socket, includes a username/password"
        sender = ZmqSender(zmq_req_endpoints=["tcp://localhost:47000"], username="username", password="password")
        receiver_thread = ZmqReceiverThread(zmq_rep_bind_address="tcp://*:47000", username="username", password="password")
        receiver_thread.start()

        sender.send("test", time_out_waiting_for_response_in_sec=3)

        self.assertEquals(receiver_thread.last_received_message(), 'test')

        print "Test if sending wrong password over REP/REQ connection results in error (actually timeout)"
        sender = ZmqSender(zmq_req_endpoints=["tcp://localhost:47000"], username="username", password="wrongpassword")
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

    @unittest.skip("do not know why this does not work. Something with inproc address")
    def test_02_req_rep_sockets_over_inproc(self):
        # Basic send/receive over REQ/REP sockets
        print "Test if sending works over REQ/REP socket using inproc, includes a username/password"
        sender = ZmqSender(zmq_req_endpoints=["inproc://test"], username="username", password="password")
        receiver_thread = ZmqReceiverThread(zmq_rep_bind_address="inproc://test", username="username", password="password")
        receiver_thread.start()

        sender.send("test", time_out_waiting_for_response_in_sec=3)

        self.assertEquals(receiver_thread.last_received_message(), 'test')

        print "Test if sending wrong password over REP/REQ connection results in error (actually timeout)"
        sender = ZmqSender(zmq_req_endpoints=["inproc://test"], username="username", password="wrongpassword")
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

    def test_03_pub_sub_without_passwords(self):
        # Basic send/receive over PUB/SUB sockets
        print "Test if sending works over PUB/SUB sockets without passwords"
        sender = ZmqSender(zmq_pub_endpoint="tcp://*:47001")
        receiver_thread = ZmqReceiverThread(zmq_sub_connect_addresses=["tcp://localhost:47001"])
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

    @unittest.skip("do not know why this does not work. Something with inproc address")
    def test_04_pub_sub_without_passwords_over_inproc(self):
        # Basic send/receive over PUB/SUB sockets
        print "Test if sending works over PUB/SUB sockets without passwords"
        sender = ZmqSender(zmq_pub_endpoint="inproc://my_test")
        receiver_thread = ZmqReceiverThread(zmq_sub_connect_addresses=["inproc://my_test"])
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

    def test_05_rpc1_req_rep(self):
        # RPC invoke method over REQ/REP sockets
        print "Test if invoking a method works over REQ/REP RPC socket, includes a username/password"
        client = ZmqRpcClient(zmq_req_endpoints=["tcp://localhost:55000"], username="username", password="password")
        server_thread = ZmqRpcServerThread(zmq_rep_bind_address="tcp://*:55000", rpc_functions={"invoke_test": invoke_test}, username="username", password="password")
        server_thread.start()

        response = client.invoke(function_name="invoke_test", function_parameters={"param1": "value1", "param2": "value2"}, time_out_waiting_for_response_in_sec=3)

        server_thread.stop()
        server_thread.join()
        client.destroy()
        # Cleaning up sockets takes some time
        time.sleep(1)

        self.assertEquals(response, "value1:value2")

    def test_06_rpc1_req_rep_invalid_function(self):
        # RPC invoke method over REQ/REP sockets
        print "Test if invoking a non existing method throws proper error over REQ/REP RPC socket, includes a username/password"
        client = ZmqRpcClient(zmq_req_endpoints=["tcp://localhost:55000"], username="username", password="password")
        server_thread = ZmqRpcServerThread(zmq_rep_bind_address="tcp://*:55000", rpc_functions={"invoke_test": invoke_test}, username="username", password="password")
        server_thread.start()

        try:
            client.invoke(function_name="invoke_test_does_not_exist", function_parameters={"param1": "value1", "param2": "value2"}, time_out_waiting_for_response_in_sec=3)
        except Exception as e:
            self.assertEquals(e.message, "Function 'invoke_test_does_not_exist' is not implemented on server. Check rpc_functions on server if it contains the function name")

        server_thread.stop()
        server_thread.join()
        client.destroy()
        # Cleaning up sockets takes some time
        time.sleep(1)

    def test_07_rpc1_req_rep_exception_raised(self):
        # RPC invoke method over REQ/REP sockets
        print "Test if invoking an existing method that throws an exception over REQ/REP RPC socket, includes a username/password"
        client = ZmqRpcClient(zmq_req_endpoints=["tcp://localhost:55000"], username="username", password="password")
        server_thread = ZmqRpcServerThread(zmq_rep_bind_address="tcp://*:55000", rpc_functions={"invoke_test_that_throws_exception": invoke_test_that_throws_exception}, username="username", password="password")
        server_thread.start()

        try:
            client.invoke(function_name="invoke_test_that_throws_exception", function_parameters={"param1": "value1", "param2": "value2"}, time_out_waiting_for_response_in_sec=3)
        except Exception as e:
            self.assertEqual(e.message, "Exception raised when calling function invoke_test_that_throws_exception. Exception: Something went wrong ")
            
        server_thread.stop()
        server_thread.join()
        client.destroy()
        # Cleaning up sockets takes some time
        time.sleep(1)

    def test_08_rpc1_pub_sub(self):
        # RPC invoke method over REQ/REP sockets
        print "Test if invoking a method works over PUB/SUB RPC socket"
        client = ZmqRpcClient(zmq_pub_endpoint="tcp://*:54000")
        server_thread = ZmqRpcServerThread(zmq_sub_connect_addresses=["tcp://localhost:54000"], rpc_functions={"invoke_test": invoke_test}, username="username", password="password")
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

    def test_09_pub_sub_timeout(self):
        # Basic send/receive over PUB/SUB sockets
        print "Test a timeout"
        sender = ZmqSender(zmq_pub_endpoint="tcp://*:47001")
        receiver_thread = ZmqReceiverThread(zmq_sub_connect_addresses=["tcp://localhost:47001"], recreate_sockets_on_timeout_of_sec=3)
        receiver_thread.start()
        # Slow joiner
        time.sleep(0.1)

        first_socket = receiver_thread.receiver.sub_sockets[0].zmq_socket
        sender.send("test")
        # Take 2 seconds to see if it works in case of within the 3 seconds window. 
        time.sleep(2)

        self.assertEqual(receiver_thread.last_received_message(), 'test')
        
        # Now send another but with 2 seconds delay, which should be ok
        sender.send("test2")
        time.sleep(2)
        
        self.assertEqual(receiver_thread.last_received_message(), 'test2')
        self.assertEqual(receiver_thread.receiver.sub_sockets[0].zmq_socket, first_socket)

        # Now send another but with 4 seconds delay, which should restart the sockets, but message should arrive
        sender.send("test3")
        time.sleep(4)
        
        self.assertEqual(receiver_thread.last_received_message(), 'test3')
        second_socket = receiver_thread.receiver.sub_sockets[0].zmq_socket
        self.assertNotEqual(second_socket, first_socket)

        # Now send another but with 2 seconds delay, which should be ok
        sender.send("test4")
        time.sleep(2)
        
        self.assertEqual(receiver_thread.last_received_message(), 'test4')
        self.assertEqual(receiver_thread.receiver.sub_sockets[0].zmq_socket, second_socket)

        receiver_thread.stop()
        receiver_thread.join()
        sender.destroy()
        # Cleaning up sockets takes some time
        time.sleep(1)

    def test_10_pub_sub_timeout_per_socket(self):
        # Basic send/receive over PUB/SUB sockets
        print "Test a timeout per socket"
        sender = ZmqSender(zmq_pub_endpoint="tcp://*:47001")
        receiver_thread = ZmqReceiverThread(zmq_sub_connect_addresses=[("tcp://localhost:47001", 3)], recreate_sockets_on_timeout_of_sec=10)
        receiver_thread.start()
        # Slow joiner
        time.sleep(0.1)

        first_socket = receiver_thread.receiver.sub_sockets[0].zmq_socket
        sender.send("test")
        # Take 2 seconds to see if it works in case of within the 3 seconds window. 
        time.sleep(2)

        self.assertEqual(receiver_thread.last_received_message(), 'test')
        
        # Now send another but with 2 seconds delay, which should be ok
        sender.send("test2")
        time.sleep(2)
        
        self.assertEqual(receiver_thread.last_received_message(), 'test2')
        self.assertEqual(receiver_thread.receiver.sub_sockets[0].zmq_socket, first_socket)

        # Now send another but with 4 seconds delay, which should restart the sockets, but message should arrive
        sender.send("test3")
        time.sleep(4)
        
        self.assertEqual(receiver_thread.last_received_message(), 'test3')
        second_socket = receiver_thread.receiver.sub_sockets[0].zmq_socket
        self.assertNotEqual(second_socket, first_socket)

        # Now send another but with 2 seconds delay, which should be ok
        sender.send("test4")
        time.sleep(2)
        
        self.assertEqual(receiver_thread.last_received_message(), 'test4')
        self.assertEqual(receiver_thread.receiver.sub_sockets[0].zmq_socket, second_socket)

        receiver_thread.stop()
        receiver_thread.join()
        sender.destroy()
        # Cleaning up sockets takes some time
        time.sleep(1)

    def test_11_rpc1_req_rep_with_rep_req_proxy_without_password(self):
        # RPC invoke method over REQ/REP sockets with an extra rep/req proxy in between
        print "Test if invoking a method works over REQ/REP RPC socket, using an extra rep/req proxy"

        client = ZmqRpcClient(zmq_req_endpoints=["tcp://localhost:53000"])

        proxy_rep_req_thread = ZmqProxyRep2ReqThread(zmq_rep_bind_address='tcp://*:53000', zmq_req_connect_addresses=["tcp://localhost:53001"])
        proxy_rep_req_thread.start()

        server_thread = ZmqRpcServerThread(zmq_rep_bind_address="tcp://*:53001", rpc_functions={"invoke_test": invoke_test})
        server_thread.start()

        time.sleep(1)

        response = client.invoke(function_name="invoke_test", function_parameters={"param1": "value1", "param2": "value2"}, time_out_waiting_for_response_in_sec=3)

        server_thread.stop()
        server_thread.join()
        proxy_rep_req_thread.stop()
        proxy_rep_req_thread.join()
        client.destroy()
        # Cleaning up sockets takes some time
        time.sleep(1)

        self.assertEquals(response, "value1:value2")

    def test_12_rpc1_req_rep_with_rep_req_proxy(self):
        # RPC invoke method over REQ/REP sockets with an extra rep/req proxy in between
        print "Test if invoking a method works over REQ/REP RPC socket, includes a username/password and also an extra rep/req proxy"

        client = ZmqRpcClient(zmq_req_endpoints=["tcp://localhost:52000"], username="username", password="password")

        proxy_rep_req_thread = ZmqProxyRep2ReqThread(zmq_rep_bind_address='tcp://*:52000', zmq_req_connect_addresses=["tcp://localhost:52001"], username_rep="username", password_rep="password", username_req="username2", password_req="password2")
        proxy_rep_req_thread.start()

        server_thread = ZmqRpcServerThread(zmq_rep_bind_address="tcp://*:52001", rpc_functions={"invoke_test": invoke_test}, username="username2", password="password2")
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

    def test_13_rpc1_pub_sub_with_pub_sub_proxy(self):
        # RPC invoke method over PUB/SUB sockets and a PUB/SUB proxy
        print "Test if invoking a method works over PUB/SUB RPC socket and a PUB/SUB proxy in between"
        server_thread = ZmqRpcServerThread(zmq_sub_connect_addresses=["tcp://localhost:4567"], rpc_functions={"invoke_test": invoke_test})
        server_thread.start()

        proxy_pub_sub_thread = ZmqProxySub2PubThread(zmq_pub_bind_address="tcp://*:4567", zmq_sub_connect_addresses=['tcp://localhost:4566'])
        proxy_pub_sub_thread.start()

        client = ZmqRpcClient(zmq_pub_endpoint="tcp://*:4566")
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

    def test_14_proxy(self):
        # With proxy elements
        print "Add a proxy setup to the end to end chain pub->proxy.req->proxy.rep->pub->sub"
        sender = ZmqSender(zmq_pub_endpoint="tcp://*:57000")

        proxy_sub_req_thread = ZmqProxySub2ReqThread(zmq_sub_connect_addresses=['tcp://localhost:57000'], zmq_req_connect_addresses=["tcp://localhost:57001"], username_req="username", password_req="password")
        proxy_sub_req_thread.start()

        proxy_rep_pub_thread = ZmqProxyRep2PubThread(zmq_rep_bind_address='tcp://*:57001', zmq_pub_bind_address='tcp://*:57002', username_rep="username", password_rep="password")
        proxy_rep_pub_thread.start()

        receiver_thread = ZmqReceiverThread(zmq_sub_connect_addresses=["tcp://localhost:57002"])
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

    def test_15_rpc1_req_rep_with_rep_req_buffered_proxy(self):
        # RPC invoke method over REQ/REP sockets with an extra rep/req proxy in between
        print "Test if invoking a method works over Buffered REQ/REP RPC socket, includes a username/password"

        test_state.last_invoked_param1 = None
        client = ZmqRpcClient(zmq_req_endpoints=["tcp://localhost:51000"], username="username", password="password")

        buf_proxy_rep_req_thread = ZmqBufferedProxyRep2ReqThread(zmq_rep_bind_address='tcp://*:51000', zmq_req_connect_addresses=["tcp://localhost:51001"], buffered_pub_address="tcp://*:59878", buffered_sub_address="tcp://localhost:59878", username_rep="username", password_rep="password", username_req="username2", password_req="password2")
        buf_proxy_rep_req_thread.start()

        server_thread = ZmqRpcServerThread(zmq_rep_bind_address="tcp://*:51001", rpc_functions={"invoke_test": invoke_test}, username="username2", password="password2")
        server_thread.start()

        time.sleep(1)

        response = client.invoke(function_name="invoke_test", function_parameters={"param1": "value1viaproxy", "param2": "value2viaproxy"}, time_out_waiting_for_response_in_sec=30)

        time.sleep(1)

        self.assertEquals(response, None)
        self.assertEquals(test_state.last_invoked_param1, "value1viaproxy")

        #Now send a couple of messages while nothing is receiving to validate buffering is owrking fine
        server_thread.stop()
        server_thread.join()
        
        test_state.last_invoked_param1 = None
        response = client.invoke(function_name="invoke_test", function_parameters={"param1": "value1-2viaproxy", "param2": "value2viaproxy"}, time_out_waiting_for_response_in_sec=30)

        # Wait some time to be sure it has been processed and the system is retrying delivery.
        time.sleep(5)
        
        server_thread = ZmqRpcServerThread(zmq_rep_bind_address="tcp://*:51001", rpc_functions={"invoke_test": invoke_test}, username="username2", password="password2")
        server_thread.start()

        # Wait some time to be sure it has been processed and the system is retrying delivery. A retry cycle is max 1 sec.
        time.sleep(2)
        
        self.assertEquals(test_state.last_invoked_param1, "value1-2viaproxy")
        
        server_thread.stop()
        server_thread.join()
        buf_proxy_rep_req_thread.stop()
        buf_proxy_rep_req_thread.join()
        client.destroy()
        # Cleaning up sockets takes some time
        time.sleep(1)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s  %(message)s')
    logger = logging.getLogger("zmprpc")
    logger.setLevel(logging.DEBUG)
    unittest.main()
    