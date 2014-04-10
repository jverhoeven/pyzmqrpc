from setuptools import setup

setup(
    name='pyzmqrpc',
    packages=['zmqrpc'],
    version='0.1.1',
    description='A simple ZMQ RPC extension on ZeroMQ',
    author='J Verhoeven',
    author_email='jan@visity.nl',
    url='https://github.com/jverhoeven/pyzmqrpc',
    download_url='https://github.com/jverhoeven/pyzmqrpc/tarball/0.1.1',
    keywords=['zeromq', 'rpc', 'pyzmq'],
    install_requires=["pyzmq"],
    classifiers=[]
)
