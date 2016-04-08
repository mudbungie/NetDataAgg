#!/usr/local/bin/python3

# This is the daemon that runs checks and updates data. 
# It forks operations on a timer.

from os import fork
from datetime import datetime

from Config import config
from NetDB import NetDB
from RadDB import RadDB
from ZabDB import ZabDB
from ipaddress import IPv4Network

if __name__ == '__main__':
    netdb = NetDB(config['databases']['netdata'])
    raddb = RadDB(config['databases']['radius'])
    zabdb = ZabDB(config['databases']['zabbix'])

    
    routers = IPv4Network(config['targets']['routers'])
    community = config['community']
    #netdb.updateArp(routers, community) # working, just not what I'm testing
    netdb.updateRadius(raddb)

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
