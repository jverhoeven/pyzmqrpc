'''
Created on Apr 8, 2014

@author: Jan Verhoeven

@copyright: MIT license, see http://opensource.org/licenses/MIT
'''
import json
import logging
from ZmqSender import ZmqSender

logger = logging.getLogger("zmqrpc")


# The ZmqRpcClient class implements a ZmqSender class but extends it with the ability
# to invoke a method on a remote server. Method invocation is implemented by providing
# a function name to invoke (function_name) and the function_parameters as a dict.
# The constructor of the class requires the ZMQ endpoints to be provided as well as
# (optionally) a username/password to 'secure' the connection.
class ZmqRpcClient(ZmqSender):
    def __init__(self, zmq_req_endpoints=None, zmq_pub_endpoint=None, username=None, password=None):
        ZmqSender.__init__(self, zmq_req_endpoints, zmq_pub_endpoint, username, password)

    def serialize_function_call(self, function_name, function_parameters):
        if function_parameters is not None:
            message = {"function": function_name, "parameters": function_parameters}
        else:
            message = {"function": function_name}
        try:
            return json.dumps(message)
        except Exception as e:
            raise Exception("Cannot wrap parameters in json format. Exception: {0}".format(e))

    # Invokes a function on a remote ZeroMQ process and returns the result of calling the function in case of a REQ socket. Parameters should be a dict.
    # time_out_waiting_for_response_in_sec indicates the time to wait for a response of the server. If none is received in the given time
    # the system does not try again and will discard the message, never knowing if it was received by the server or not.
    def invoke(self, function_name, function_parameters=None, time_out_waiting_for_response_in_sec=600):

        # Try to serialize. If it fails, throw an error and exit.
        message_json = self.serialize_function_call(function_name, function_parameters)
        return self.send(message_json, time_out_waiting_for_response_in_sec)
