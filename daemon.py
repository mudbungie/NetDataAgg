#!/usr/local/bin/python3

# This is the daemon that runs checks and updates data. 
# It forks operations on a timer.

import subprocess

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
    netdb.updateArp(routers, community)
