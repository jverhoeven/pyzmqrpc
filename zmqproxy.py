'''
Created on Mar 31, 2014

@author: Jan Verhoeven

@copyright: MIT license, see http://opensource.org/licenses/MIT

'''
import argparse
import signal
import sys
import logging
from zmqrpc.ZmqProxy import ZmqProxyRep2Pub, ZmqProxySub2Req, ZmqProxyRep2Req, ZmqProxySub2Pub


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Proxies message either from SUB->REQ, SUB->PUB, REP->PUB or REP->REQ.')
    parser.add_argument('--sub', nargs='+', required=False, help='The SUB endpoints')
    parser.add_argument('--pub', required=False, help='The PUB endpoint')
    parser.add_argument('--req', nargs='+', required=False, help='The REQ endpoint')
    parser.add_argument('--rep', required=False, help='The REP endpoint')
    parser.add_argument('--username_incoming', required=False, help='In case a username is needed for the incoming connection (sub, rep)')
    parser.add_argument('--password_incoming', required=False, help='In case a password is needed for the incoming connection (sub, rep)')
    parser.add_argument('--username_outgoing', required=False, help='In case a username is needed for the outgoing connection (req, pub)')
    parser.add_argument('--password_outgoing', required=False, help='In case a password is needed for the outgoing connection (req, pub)')

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("zmqproxy")
    logger.setLevel(logging.DEBUG)

    logger.info("Starting zmqproxy...")
    if args.sub is not None and args.rep is not None:
        logger.error("Fatal error: Proxy cannot listen to both SUB and REP at the same time")
    elif args.pub is not None and args.req is not None:
        logger.error("Fatal error: Proxy cannot send messages over both PUB and REQ sockets at the same time")
    elif (args.sub is not None or args.rep is not None) and (args.pub is not None or args.req is not None):

        # Handle OS signals (like keyboard interrupt)
        def signal_handler(_, __):
            logger.info('Ctrl+C detected. Exiting...')
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        if args.sub is not None and args.req is not None:
            server = ZmqProxySub2Req(zmq_sub_connect_addresses=args.sub, zmq_req_connect_addresses=args.req, username_sub=args.username_incoming, password_sub=args.password_incoming, username_req=args.username_outgoing, password_req=args.password_outgoing)
            server.run()
        elif args.rep is not None and args.pub is not None:
            server = ZmqProxyRep2Pub(zmq_rep_bind_address=args.rep, zmq_pub_bind_address=args.pub, username_rep=args.username_incoming, password_rep=args.password_incoming, username_pub=args.username_outgoing, password_pub=args.password_outgoing)
            server.run()
        elif args.sub is not None and args.pub is not None:
            server = ZmqProxySub2Pub(zmq_sub_connect_addresses=args.sub, zmq_pub_bind_address=args.pub, username_sub=args.username_incoming, password_sub=args.password_incoming, username_pub=args.username_outgoing, password_pub=args.password_outgoing)
            server.run()
        elif args.rep is not None and args.req is not None:
            server = ZmqProxyRep2Req(zmq_rep_bind_address=args.rep, zmq_req_connect_addresses=args.req, username_rep=args.username_incoming, password_rep=args.password_incoming, username_req=args.username_outgoing, password_req=args.password_outgoing)
            server.run()
    logger.info("Stopped zmqproxy...")
