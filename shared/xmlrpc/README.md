# xmlrpc system

## server.py

execute `python3 server.py` on each node to start serving on port 8000.

## client_ping.py

execute `python3 client_ping <ip_of_server>` and get hostname plus timing information.

## mass_ping

execute `./mass_ping <host_list> and send requests to all hosts sequentially, exit if any request fails.

```
# ./mass_ping data/3_node.list 2>/dev/null
1535372952.4630406 n3 1535372952.5469158 0.08387517929077148
1535372952.6255186 n4 1535372952.7090645 0.08354592323303223
1535372952.7869601 n5 1535372952.8731215 0.08616137504577637
```

If host is unreachable or server not running then a generic error is logged.

```
# ./mass_ping data/3_node.list 2>/dev/null
1535372788.1022818 n3 1535372788.1898038 0.08752202987670898
Error @ 10.0.0.12
```