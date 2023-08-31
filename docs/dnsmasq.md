# dnsmasq configs

Example configs end explanation what the options mean, as those are ommited from the generated configs

## play VLAN

```
localise-queries

# don't read /etc/resolv.conf or any other
# file for getting upstream servers from
no-resolv

# add the host record for this subnet for lpos
host-record=onboarding.nlpt.network,192.168.123.8

# Define upstream DNS servers
server=192.168.123.1

# Add local-only domains here, queries in these domains are answered
# from /etc/hosts or DHCP only.
local=/nlpt.network/

# Never forward reverse-lookups of local IPs to the upstream server
bogus-priv

# Never forward shot-names
domain-needed

# DHCP delivers Gateway
dhcp-option=vlan3@eth0,3,192.168.123.1

# Static hosts in play network, one line per fully onboarded device
dhcp-host=vlan3@eth0,4c:d1:a1:d9:9d:a9,192.168.123.22,1h
dhcp-host=vlan3@eth0,44:74:6c:b5:13:db,192.168.123.35,1h
```

## onboarding VLANs

```
# add the host record for this subnet for lpos
# with a really low ttl of 10 seconds
host-record=onboarding.nlpt.network,172.16.101.1,10

# DHCP-Range for this onboarding network
dhcp-range=vlan4@eth0,172.16.101.2,172.16.101.99,10s
```

## additional options might helpt with Captive Portal

```
host-record=msftconnecttest.com,172.16.101.1,10
host-record=dns.msftncsi.com,172.16.101.1,10
dhcp-option=vlan4@eth0,160,http://onboarding.nlpt.network
dhcp-option=vlan4@eth0,114,http://onboarding.nlpt.network
```
