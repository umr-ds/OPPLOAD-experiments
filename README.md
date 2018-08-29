# Topo tests
## Generate testfile:

```
dd if=/dev/urandom of=test.file bs=1M count=1
```

## Insert test.file to all instances

```
bash -c "servald rhizome add file $(servald id self | tail -1) test.file"
```

# Serval configs
servald config set rhizome.advertise.interval 2000
