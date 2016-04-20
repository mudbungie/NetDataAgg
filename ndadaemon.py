#!/usr/local/bin/python3

# This is the daemon that runs checks and updates data. 
# It forks operations on a timer.

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
scanrouters = False
updatedbs = False
checkarp = False
checkusernames = False
scannetwork = True

if __name__ == '__main__':
    if initdbs:
        netdb = NetDB(config['databases']['netdata'])
        raddb = RadDB(config['databases']['radius'])
        zabdb = ZabDB(config['databases']['zabbix'])
        fsdb  = FreesideDB(config['databases']['freeside'])
        
    if scanrouters:
        print('Updating Arp...')
        community = config['snmp']['routercommunity']
        netdb.updateArp(community)

    if scanrouters:
        print('Updating Radius...')
        netdb.updateRadius(raddb)
        print('Updating Hosts...')
        netdb.updateHosts(zabdb)
        print('Updating Customers...')
        netdb.updateCustomers(fsdb)
    
    if checkarp:
        print('Diagnosing Zabbix/Arp mismatches...')
        netdb.checkZabbixAgainstArp()
    
    if checkusernames:
        print('Diagnosing Radius/Hostname mismatches...')
        netdb.updateBadUsernames()
    
    if scannetwork:
        network = Network(netdb)
        # This will just core dump... haven't solved multithreading.
        network.getHosts()
        #netdb.checkForBridgedHosts()

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
