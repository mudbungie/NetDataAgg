# Class for a router, which will have ARP data for all attached devices.

# Not mine
from easysnmp import Session
import easysnmp
from binascii import hexlify
from datetime import datetime
import re

# Mine
from NetworkPrimitives import Ip, Mac, Netmask
from Host import Host

class Router(Host):
    def __init__(self, ip, community):
        # Do the normal things for any network object.
        self.hostinit(ip)
        # Initiate SNMP
        self.session = Session(hostname=str(self.ip), community=community,
            version=1)

    @property
    def routes(self):
        return self.__routes
    @routes.setter
    def routes(self, data):
        print('route set on', self.ip)
        self.__routes = data

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
        mib = 'ipCidrRouteTable'
        responses = self.walk(mib)
        errors = 0
        routes = {} # Internally, we'll want to do lookups, so dict.
        print('Recieved', len(responses), 'SNMP responses from', self.ip)
        for r in responses:
            try:
                # An assumption is that the destinations come first.
                if r.oid == 'ipCidrRouteDest':
                    # Introduce the route.
                    routes[r.oid_index] = {'destination':Ip(r.value),
                                                'router':self.ip}
                # The other conditions just add values.
                elif r.oid == 'ipCidrRouteMask':
                    routes[r.oid_index]['netmask'] = Netmask(r.value)
                elif r.oid == 'ipCidrRouteNextHop':
                    routes[r.oid_index]['nexthop'] = Ip(r.value)
            except KeyError:
                # Would mean that a value came in without our seeing the
                # destination first.
                errors += 1
        # The index on this is useless outside of populating the routes. 
        # I'm going to do a single pass to make a more useful index.
        self.routes = {}
        for r in routes.values():
            self.routes[r['destination']+str(r['netmask'])+r['nexthop']] = r
        print('Parsed', len(self.routes), 'routes.')
        return self.routes

