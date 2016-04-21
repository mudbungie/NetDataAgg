from Config import config
from Network import Network

yknet = Network(None) # Not passing a DB, this is just testing.
yknet.routerCommunity = 'fartknocker'
yknet.routers = ['199.68.200.240']
hosts = yknet.getHosts()
for host in hosts.values():
    print(host.ip)
    for interface in host.interfaces:
        print(interface)
