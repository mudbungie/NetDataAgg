#!/usr/local/bin/python3

from Config import config
from Network import Network
from NetDB import NetDB

netDB = NetDB(config['databases']['netdata'])
yknet = Network() # Not passing a DB, this is just testing.
yknet.routerCommunity = 'fartknocker'
yknet.routers = netDB.getRouters()
yknet.scanRouterArpTables()
yknet.getHosts()
yknet.scanRouterRoutingTables()
