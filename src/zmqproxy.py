'''
Created on Mar 31, 2014

@author: Jan Verhoeven

@copyright: MIT license, see http://opensource.org/licenses/MIT

'''
import argparse
import signal
import sys
from zmqrpc.ZmqProxy import ZmqProxyRep2Pub, ZmqProxySub2Req

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Proxies message either from SUB->REQ or from REP->PUB.')
    parser.add_argument('--sub', nargs='+', required=False, help='The SUB endpoints')
    parser.add_argument('--pub', required=False, help='The PUB endpoint')
    parser.add_argument('--req', nargs='+', required=False, help='The REQ endpoint')
    parser.add_argument('--rep', required=False, help='The REP endpoint')
    parser.add_argument('--username_incoming', required=False, help='In case a username is needed for the incoming connection (sub, rep)')
    parser.add_argument('--password_incoming', required=False, help='In case a password is needed for the incoming connection (sub, rep)')
    parser.add_argument('--username_outgoing', required=False, help='In case a username is needed for the outgoing connection (req, pub)')
    parser.add_argument('--password_outgoing', required=False, help='In case a password is needed for the outgoing connection (req, pub)')

    args = parser.parse_args()
    print "Starting zmqproxy..."

    if (args.sub is None and args.pub is None) or (args.sub is not None and args.pub is not None):
        print "Fatal error: Either sub or pub must be supplied (and not both)"
    elif (args.req is None and args.rep is None) or (args.req is not None and args.rep is not None):
        print "Fatal error: Either req or rep must be supplied (and not both)"
    elif args.sub is not None and args.req is None:
        print "Fatal error: If sub is supplied, req is also expected. Proxy can only work sub->req OR req->pub"
    elif args.pub is not None and args.rep is None:
        print "Fatal error: If pub is supplied, rep is also expected. Proxy can only work sub->req OR rep->pub"
    else:

        # Handle OS signals (like keyboard interrupt)
        def signal_handler(signal, frame):
            print 'Ctrl+C detected. Exiting...'
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        if args.sub is not None:
            server = ZmqProxySub2Req(zmq_sub_connect_addresses=args.sub, zmq_req_connect_addresses=args.req, username_sub=args.username_incoming, password_sub=args.password_incoming, username_req=args.username_outgoing, password_req=args.password_outgoing)
            server.run()
        elif args.pub is not None:
            server = ZmqProxyRep2Pub(zmq_rep_bind_address=args.rep, zmq_pub_bind_address=args.pub, username_sub=args.username_incoming, password_sub=args.password_incoming, username_req=args.username_outgoing, password_req=args.password_outgoing)
            server.start()
    print "Stopped zmqproxy..."
