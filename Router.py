# Class for a router, which will have ARP data for all attached devices.

# Not mine
from easysnmp import Session
import easysnmp
from binascii import hexlify
from datetime import datetime
import re

# Mine
from Ip import Ip
from Mac import Mac
from Host import Host

class Router(Host):
    def __init__(self, ip, community):
        # Do the normal things for any network object.
        self.hostinit(ip)
        # Initiate SNMP
        self.session = Session(hostname=str(self.ip), community=community,
            version=1)


    def walk(self, mib):
        # Walks the specified mib
        try:
            responses = self.session.walk(mib)
            return responses
        except easysnmp.exceptions.EasySNMPNoSuchNameError:
            # Probably means that you're hitting the wrong kind of device
            print('nosuchname')
            return False
        except easysnmp.exceptions.EasySNMPTimeoutError:
            # Either the community string is wrong, or you're pinging dead space
            print('timeout')
            return False

    def getArpTable(self):
        # A walk of the ARP table, gives list of dicts

        # MIB for ARP tables
        mib = 'ipNetToMediaPhysAddress'
        responses = self.walk(mib)
        arpTable = []
        # Conditional, so that we don't error on empty responses
        if responses:
            for response in responses:
                try:
                    # Validation occurs in the decoding, just move on if they
                    # throw assertion errors.
                    mac = Mac(response.value, encoding='utf-16')
                    ip = Ip(response.oid_index, encoding='snmp')
                    #print('MAC: ' + str(mac) + ' IP: ' + str(ip))
                    values = {}
                    values['mac'] = str(mac)
                    values['ip'] = str(ip)
                    # We also want to know where the ARP record came from.
                    values['source'] = str(self.ip)
                    # We ignore data points that have to do with locally 
                    # administered MAC addresses.
                    localMacs = ['2', '6', 'a', 'e']
                    if values['mac'][1] not in localMacs:
                        arpTable.append(values)
                except AssertionError:
                    pass
        return arpTable

    def getRoutingTable(self):
        # Walk the routing table
        # I'm just running the direct oid
        mib = '1.3.6.1.2.1.4.24.4.1'
        responses = self.walk(mib)
        routingTable = []
        for response in responses:
            try:
                # Always validate, but just pass on exceptions.
                route = {}
                # The first four octets should be a destination IP.
                index = response.oid_index.split('.')
                route['target'] = Ip('.'.join(index[0:3]))
                route['netmask'] = Ip('.'.join(index[4:7]).bits())
                route['destination'] = Ip('.'.join(index[9:12]))
                print('target', route['target'], 'netmask', route['netmask'], 'destination', route['destination'])

                #print(response.oid_index, response.value)
            except AssertionError:
                print(response.oid_index, response.value)

