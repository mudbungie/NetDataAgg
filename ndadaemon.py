#!/usr/bin/env python3

# This is the daemon that runs checks and updates data. 
# It forks operations on a timer.
#FIXME No it doesn't, but it should.

from os import fork
from datetime import datetime

from Config import config
from NetDB import NetDB
from RadDB import RadDB
from ZabDB import ZabDB
from FreesideDB import FreesideDB
from ipaddress import IPv4Network
from Network import Network

initdbs = True
initnet = True
scanarp = True
scanroutes = True
pullforeigndbs = True
verifyarp = True
verifyusernames = True
updatedhcp = True
scannetwork = False
scanhostbridges = True # Currently doesn't even write to a database...

if __name__ == '__main__':
    if initdbs:
        netdb = NetDB(config['databases']['netdata'])
        raddb = RadDB(config['databases']['radius'])
        zabdb = ZabDB(config['databases']['zabbix'])
        fsdb  = FreesideDB(config['databases']['freeside'])

    if initnet:
        yknet = Network()
        yknet.routerCommunity = config['snmp']['routercommunity']
        yknet.radioCommunity = config['snmp']['radiocommunity']
        yknet.routers = netdb.getRouters()
        
    if scanarp:
        print('Updating Arp...')
        yknet.scanRouterArpTables()
        netdb.updateArp(yknet.globalArpTable)

    if scanroutes:
        print('Updating Routing Table...')
        yknet.scanRouterRoutingTables()
        netdb.updateAllRoutes(yknet.routers.values())

    if pullforeigndbs:
        print('Updating Radius...')
        netdb.updateRadius(raddb)
        print('Updating Zabbix Hosts...')
        netdb.updateZabHosts(zabdb)
        print('Updating Customers...')
        netdb.updateCustomers(fsdb)
    
    if verifyarp:
        print('Diagnosing Zabbix/Arp mismatches...')
        netdb.checkZabbixAgainstArp()
    
    if verifyusernames:
        print('Diagnosing Radius/Hostname mismatches...')
        netdb.updateBadUsernames()
    
    if scannetwork:
        print('Scanning all known hosts...')
        # This will just core dump... haven't solved multithreading.
        yknet.getHosts()

    if scanhostbridges:
        print('Scanning hosts for bridged interfaces...')
        yknet.getBridgedHosts()
    
    if updatedhcp:
        print('Updating DHCP leases...')
        netdb.updateDHCP(config['dhcp']['remote_string'])

		print('done!')
    #for host in network.hosts:
    #    print(host)
    
    # Also core dumps; multithreading...
    #print('Checking for bridged connections...')
    #netdb.checkForBridgedHosts()
    

    '''
    # Main loop
    while True:
        timestamp = datetime.now()
        # Indicates that this is the parent process
        pid = 0

        # Once per minute, check the routers
        if timestamp.second == 0:
            if pid = 0:
                pid = os.fork()
                if pid != 0:
    '''
