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

if __name__ == '__main__':
    netdb = NetDB(config['databases']['netdata'])
    raddb = RadDB(config['databases']['radius'])
    zabdb = ZabDB(config['databases']['zabbix'])
    fsdb  = FreesideDB(config['databases']['freeside'])
    
    routers = IPv4Network(config['targets']['routers'])
    community = config['snmp']['routercommunity']
    '''    
    print('###Updating all resources###')
    print('Updating Arp...')
    netdb.updateArp(routers, community)
    print('Updating Radius...')
    netdb.updateRadius(raddb)
    
    print('Updating Hosts...')
    netdb.updateHosts(zabdb)
   
    print('Updating Customers...')
    netdb.updateCustomers(fsdb)
    
    network = Network(netdb)
    # This will just core dump... haven't solved multithreading.
    #network.getHosts()

    #for host in network.hosts:
    #    print(host)
    
    print('Diagnosing Zabbix/Arp mismatches...')
    netdb.checkZabbixAgainstArp()
    '''
    print('Diagnosing Radius/Hostname mismatches...')
    netdb.updateBadUsernames()
    
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
