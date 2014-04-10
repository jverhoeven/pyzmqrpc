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

if __name__ == '__main__':
    client = ZmqRpcClient(
        zmq_pub_endpoint="tcp://*:30000")

    server = ZmqRpcServerThread(
        zmq_sub_connect_addresses=["tcp://localhost:30000"],    # Must be a list
        rpc_functions={"test_method": test_method})             # Dict

    server.start()

    # Wait a bit since sockets may not have been connected immediately
    time.sleep(2)

    client.invoke(
        function_name="test_method",
        function_parameters={"param1": "param1", "param2": "param2"})   # Must be dict

    # Wait a bit to make sure message has been received
    time.sleep(2)

    # Clean up
    server.stop()
    server.join()
