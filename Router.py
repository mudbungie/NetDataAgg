# Class for a router, which will have ARP data for all attached devices.

# Not mine
from easysnmp import Session
import easysnmp.exceptions
from binascii import hexlify
from datetime import datetime
import re

# Mine
from Ip import Ip
from Mac import Mac

class Router:
    def __init__(self, ip, community):
        # First, double check that IP is actually an IP
        self.ip = Ip(ip)

        # Initiate SNMP
        self.session = Session(hostname=str(self.ip), community=community,
            version=1)

    def walk(self, mib):
        # Walks the specified mib
        try:
            responses = self.session.walk(mib)
            return responses
        except easysnmp.exceptions.EASYSNMPNoSuchNameError:
            # Probably meanas that you're hitting the wrong kind of device
            return False
        except easysnmp.exceptions.EasySNMPTimeoutError:
            # Either the community string is wrong, or you're pinging dead space
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
                    arpTable.append(values)
                except AssertionError:
                    pass
        return arpTable
            
