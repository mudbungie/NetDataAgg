from Config import config
from Network import Network
from NetDB import NetDB

netDB = NetDB(config['databases']['netdata'])
yknet = Network(None) # Not passing a DB, this is just testing.
yknet.routerCommunity = 'fartknocker'
yknet.routers = netDB.getRouters()
hosts = yknet.getHosts()
for host in hosts.values():
    #print(host.ip)
    if len(host.interfaces) > 1:
        print(type(host))
        print(host)
