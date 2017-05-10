from setuptools import setup

setup(
    name='pyzmqrpc',
    packages=['zmqrpc'],
    version='2.0.0',
    include_package_data=True,
    description='A simple ZMQ RPC extension with JSON for message serialization',
    author='J Verhoeven',
    author_email='jan@captive.nl',
    url='https://github.com/jverhoeven/pyzmqrpc',
    download_url='https://github.com/jverhoeven/pyzmqrpc/tarball/2.0.0',
    keywords=['zeromq', 'rpc', 'pyzmq'],
    install_requires=["pyzmq>=15.0.0", "future>=0.15.0"],
    classifiers=[]
)
