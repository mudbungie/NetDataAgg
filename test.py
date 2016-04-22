from Config import config
from Network import Network
from NetDB import NetDB

netDB = NetDB(config['databases']['netdata'])
yknet = Network(None) # Not passing a DB, this is just testing.
yknet.routerCommunity = 'fartknocker'
yknet.routers = netDB.getRouters()
yknet.routers['199.68.200.240'].getRoutingTable()
