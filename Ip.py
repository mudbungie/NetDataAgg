# Class for an IP address, which is the only piece of network data that we 
# can actually expect to be unique.

from Mac import Mac
import ipaddress
import re

class IP:
    def __init__(self, ip):
        # You should be passing a string
        # First, always authenticate!
        ipre = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}\
            (?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
        if re.match(ipre, ip):
            self.ip = ip
        else:
            raise TypeError('String passed was not an valid IPv4 address')

    def getMac(self, arpTable):
        self.mac = arpTable.getMacByIP(self.ip)
        return self.mac


