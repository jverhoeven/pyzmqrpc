# Introduction
This Python package adds basic Remote Procedure Call functionalities to ZeroMQ. It does not do advanced serializing, but simply uses JSON call and response structures. 
# Install
pip install pyzmqrpc
# Usage
Implement a function on the server that can be invoked:

    def test_method(param1, param2):
		return param1 + param2
		
Create a ZeroMQ server:

	server = ZmqRpcServerThread(zmq_rep_bind_address="tcp://*:30000",
            rpc_functions={"test_method": test_method})
    server.start()
    
Create a client that connects to that server endpoint:

	client = ZmqRpcClient(zmq_req_endpoints=["tcp://localhost:30000"])
	
Have the client invoke the function on the server:

	client.invoke(function_name="test_method",
            function_parameters={"param1": "Hello", "param2": " world"})

More examples below and are included in the repository. A unit test is also included.

# Rationale
Working with ZeroMQ is great. It is fun, fast and simply works. I use it right now for routing timeseries samples from all sorts of sampling devices to a central location on the internet. All samplers use PUB sockets. The samples are collected using a proxy app that bridges the internet to a remote host via a password protected REQ/REP socket. From there the samples are exposed via a PUB socket again.

I found I was repeating the same code over and over, so decided to make a module.
# Requirements

1. It should be possible to create a network by simply starting apps and configure them with the location of the end-points. The apps will typically be started on a process level, however, threading should also be supported.
2. Must have support for PUB/SUB (non-reliable, whoever is listening) and REQ/REP sockets (reliable). The latter should have support for time outs and automatic recreation of a REQ socket if no message is received in the time out period.
3. If somewhere in the network there is connection failing, messages should be automatically queued up to a certain queue size. Right now, this has been implemented on the PUB/SUB interface.
4. Password protection is important when traversing non-secure networks. However, no CURVE based protection is needed for now, just simple username/password. The fact that a network can be sniffed is not relevant for my specific use case.
5. Since I use a lot of Raspberry devices, it shall be able to work around a bug (ARM only) that stops listening on SUB sockets when another device connected via SUB disconnected. This particular bug seems fixed in ZeroMQ 4.x, but not tested by me. Leaving the code in for now.

# Components
## ZmqReceiver
Starts a loop listening via a SUB or REP socket for new messages. Multiple SUB end-points may be provided. If a message is received it calls 'HandleNewMessage' which can be overridden by any subclassed implementation.
## ZmqClient
Upon creation it starts a PUB socket and/or creates a REQ socket. The REQ socket may point to multiple end-points, which then use round-robin message delivery. The ZmqClient implements a 'send' method that sends a message.
## ZmqProxy
Forwards messages from a SUB --> REQ socket or from a PUB --> REP socket.
## ZmqRpcClient
Invokes a remotely implemented method over a PUB or REQ socket. For PUB sockets no response messages can be expected.
## ZmqRpcServer
Implements a method that can be remotely invoked. Uses ZmqReceiver functionality to listen for messages on a REP or SUB socket, deserialize the message and invoke them.

# Example
This example is from demo_pub_sub.py. It should be relatively self explanatory. It starts an RPC server thread, registers a function, then creates an RPC client and invokes the registered function.

    from zmqrpc.ZmqRpcClient import ZmqRpcClient
    from zmqrpc.ZmqRpcServer import ZmqRpcServerThread
    import time
    
    
    def test_method(param1, param2):
        print "test_method invoked with params '{0}' and '{1}'".format(param1, param2)
    
    if __name__ == '__main__':
        client = ZmqRpcClient(
            zmq_pub_endpoint="tcp://*:30000",
            username="test",
            password="test")
    
        server = ZmqRpcServerThread(
            zmq_sub_connect_addresses=["tcp://localhost:30000"],    # Must be a list
            rpc_functions={"test_method": test_method},             # Dict
            username="test",
            password="test")
    
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
        
Example with invoking method in REP/REQ. The difference with PUB/SUB is that this will return a response message:

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

## New since 1.5.0 - Per socket heartbeats
In order to detect silently disconnected SUB sockets (network failures or otherwise), it is now possible to (optionally) define a heartbeat timeout per SUB socket. Updated example:

        server = ZmqRpcServerThread(
            zmq_sub_connect_addresses=[("tcp://localhost:30000", 60)],
            rpc_functions={"test_method": test_method},
            username="test",
            password="test")

Per SUB socket address a tuple can be specified that holds the address as the first element and the heartbeat timeout as the second. Note that that the responsibility to send an heartbeat 

# Available standard proxies
A number of already provided proxies are available:
* REQ to REQ by means of ZmqProxySub2ReqThread

* SUB to PUB by means of ZmqProxySub2PubThread
* REP to PUB by means of ZmqProxyRep2PubThread
* REP to REQ by means of ZmqProxyRep2ReqThread
* Buffered REP to REQ via ZmqBufferedProxyRep2ReqThread

Each of these proxies will take a message from the input format/socket and proxy it to the output socket. One model could be to collect all samples from all subprocesses on a site and multiplex them via the proxy in a reliable manner over a REP/REQ socket.

Note that when a PUB/SUB connection is used, there is no return message or in case of method invocation, any function response is discarded.

The buffered REP/REQ proxy quietly uses a PUB/SUB socket to introduce a means to buffer messages and method invocations.

# Known issues
* Serialization is very limited and only supports types that can be serialized over JSON.
* Only localhost type of testing done with passwords. Not sure if auth works over remote connections

# Notes
Please note that this implementation is very pre-mature, although it works fine for me in my own project and has operated stable for months.

# Change log
## Version 1.5.0
* Improved ability to use heartbeats to avoid silently failing ZMQ sockets. Timeouts can now be set per SUB socket. Before this version a reset would be for all addresses in the SUB address list provided. This would allow a single socket to get disconnected and never reconnected because the other SUB sockets were still getting messages.
* Replace * with 0.0.0.0 in socket.unbind, which seems no longer supported.

## Version 1.0.1
Central logging for entire zmqrpc facility. Also logs exceptions for easier debugging.

## Version 1.0.0
Added a buffered REQ/REQ proxy which uses PUB/SUB internally. Bumped version number to stable release number since the library worked fine for months and code and tests are now at a more mature level.

## Version 0.1.9 and before
Internal testing.