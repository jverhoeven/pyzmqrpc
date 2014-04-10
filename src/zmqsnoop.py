'''
Created on Mar 31, 2014

@author: Jan Verhoeven

@note: This utility prints all messages published on a PUB endpoint by connecting
       a SUB socket to it. All message are line split and prefixed with a '>' character.

@copyright: MIT license, see http://opensource.org/licenses/MIT

'''
import zmq
import argparse
import sys
import signal


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Reads and prints messages from a remote pub socket.')
    parser.add_argument('--sub', nargs='+', required=True, help='The PUB endpoint')

    args = parser.parse_args()
    print "Starting zmqsnoop..."

    # Handle OS signals (like keyboard interrupt)
    def signal_handler(signal, frame):
        print 'Ctrl+C detected. Exiting...'
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        context = zmq.Context()

        # Subscribe to all provided end-points
        sub_socket = context.socket(zmq.SUB)
        sub_socket.setsockopt(zmq.SUBSCRIBE, '')
        for sub in args.sub:
            sub_socket.connect(sub)
            print "Connected to {0}".format(sub)
        while True:
            # Process all parts of the message
            try:
                message_lines = sub_socket.recv().splitlines()
            except Exception as e:
                print "Error occured with exception {0}".format(e)
            for line in message_lines:
                print ">" + line
    except Exception as e:
        print "Connection error {0}".format(e)

    # Never gets here, but close anyway
    sub_socket.close()

    print "Exiting zmqsnoop..."
