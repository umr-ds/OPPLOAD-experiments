#!/usr/bin/python3

import xmlrpc.client
import time
import sys

if len(sys.argv) == 1:
    print("USAGE: %s <server>" % sys.argv[0])
    sys.exit(0)

s = xmlrpc.client.ServerProxy('http://%s:8000' % sys.argv[1])

pre = time.time()
response = s.ping()
post = time.time()
diff = post - pre

print(pre,response,post,diff)

# Print list of available methods
#print(s.system.listMethods())