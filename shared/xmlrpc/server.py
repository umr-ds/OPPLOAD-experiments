#!/usr/bin/python3

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

import platform

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

# Create server
with SimpleXMLRPCServer(('0.0.0.0', 8000),
                        requestHandler=RequestHandler) as server:
    server.register_introspection_functions()
    
    def pong_function():
        return platform.node()
    server.register_function(pong_function, 'ping')

    # Run the server's main loop
    server.serve_forever()