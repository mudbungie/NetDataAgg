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
from Route import Route

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
        print('Scanning ARP table for router at:', self.ip)

        # MIB for ARP tables
        mib = 'ipNetToMediaPhysAddress'
        responses = self.walk(mib)
        arpTable = []
        self.arpByMac = {}
        self.arpByIp = {}
        # Conditional, so that we don't error on empty responses
        if responses:
            ignored = 0
            errors = 0
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
                    if values['mac'][1] in localMacs:
                        ignored += 1
                    else:
                        arpTable.append(values)
                        self.arpByMac[mac] = ip
                        self.arpByIp[ip] = mac
                except AssertionError:
                    # Malformed input is to be ignored.
                    errors += 1
                    pass
        print('Recorded', len(arpTable), 'ARP values with', 
            errors, 'errors, ignoring', ignored, 'virtual MAC addresses.')
        return arpTable

    def getRoutingTable(self):
        print('Scanning routing table for router at:', self.ip)
        # Walk the routing table
        # I'm just running the direct oid
        mib = '1.3.6.1.2.1.4.24.4.1'
        responses = self.walk(mib)
        self.routingTable = {}
        self.singleHostRoutes = {} # Same data, but for just direct connections.
        self.directRoutes = {}
        # The SNMP routing table is not logical, Have to deduplicate it.
        seen = set()
        errors = 0
        for response in responses:
            if response.oid_index not in seen:
                seen.add(response.oid_index)
                # Function returns only success or failure; it interacts with 
                # the routing table directly.
                if not self.processSNMPRoute(response):
                    errors += 1
        print('Recorded', len(self.routingTable), 'routes with',
            errors, 'errors.')

    def processSNMPRoute(self, response):
        # Take messy SNMP and make a Route dictionary in the self namespace.
        # Malformed data provokes no action.
        index = response.oid_index.split('.')
        try:
            nexthop = Ip('.'.join(index[9:13]))
            try:
                self.arpByIp[nexthop]
            except KeyError:
                # There isn't an ARP entry for the route, means it's 
                # non-actionable, and we won't record it.
                return False
            # The first four octets should be a destination IP.
            address = Ip('.'.join(index[0:4]))
            # The bits function does bit-math, and returns a CIDR int.
            netmask = Ip('.'.join(index[4:8])).bits()
        except AssertionError:
            # Raised by the IP encoding. Indicates a malformed address. 
            print(response.oid_index, response.value)
            pass
        # Now that everything has passed verification, make it a dictionary.
        route = {'address':address,'netmask':netmask,'nexthop':nexthop,
            'router':self}
        # Add it to the routing table! This is really the whole point.
        self.routingTable[address] = route
        return True
