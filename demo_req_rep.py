'''
Created on Apr 8, 2014

@author: Jan Verhoeven

@copyright: MIT license, see http://opensource.org/licenses/MIT
'''
from zmqrpc.ZmqRpcClient import ZmqRpcClient
from zmqrpc.ZmqRpcServer import ZmqRpcServerThread
import time


def test_method(param1, param2):
    print "test_method invoked with params '{0}' and '{1}'".format(param1, param2)
    return "test_method response text"

if __name__ == '__main__':
    client = ZmqRpcClient(
        zmq_req_endpoints=["tcp://localhost:30000"],            # List
        username="test",
        password="test")

    server = ZmqRpcServerThread(
        zmq_rep_bind_address="tcp://*:30000",
        rpc_functions={"test_method": test_method},             # Dict
        username="test",
        password="test")
    server.start()

    # Wait a bit since sockets may not have been connected immediately
    time.sleep(2)

    # REQ/REQ sockets can carry a response
    response = client.invoke(
        function_name="test_method",
        function_parameters={"param1": "param1", "param2": "param2"})   # Must be dict

    print "response: {0}".format(response)

    # Wait a bit to make sure message has been received
    time.sleep(2)

    # Clean up
    server.stop()
    server.join()
