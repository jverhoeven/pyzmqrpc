from setuptools import setup

setup(
    name='pyzmqrpc',
    packages=['zmqrpc'],
    version='1.0.1',
    include_package_data=True,
    description='A simple ZMQ RPC extension with JSON for message serialization',
    author='J Verhoeven',
    author_email='jan@visity.nl',
    url='https://github.com/jverhoeven/pyzmqrpc',
    download_url='https://github.com/jverhoeven/pyzmqrpc/tarball/1.0.0',
    keywords=['zeromq', 'rpc', 'pyzmq'],
    install_requires=["pyzmq>=14.1.0"],
    classifiers=[]
)
