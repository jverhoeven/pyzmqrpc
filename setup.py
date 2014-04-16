from setuptools import setup

setup(
    name='pyzmqrpc',
    packages=['zmqrpc'],
    version='0.1.7',
    include_package_data=True,
    description='A simple ZMQ RPC extension with JSON for message serialization',
    author='J Verhoeven',
    author_email='jan@visity.nl',
    url='https://github.com/jverhoeven/pyzmqrpc',
    download_url='https://github.com/jverhoeven/pyzmqrpc/tarball/0.1.7',
    keywords=['zeromq', 'rpc', 'pyzmq'],
    install_requires=["pyzmq>=14.1.0"],
    classifiers=[]
)
