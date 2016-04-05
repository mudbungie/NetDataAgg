# Class for an IP address, which is the only piece of network data that we 
# can actually expect to be unique.

import re
from ipaddress import IPv4Address

class Ip:
    def __init__(self, ip, encoding=None):
        # If it's an ipaddress, that's fine. Otherwise, validate.
        if not encoding:
            self.ip = ip
        elif encoding == 'snmp':
            # The encoding for SNMP is all malformed.
            ipstr = '.'.join(value.split('.')[1:])    
            # If it's a string, we need to validate it.
            ipre = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}\
                (?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
            print(type(ipstr))
            if not ipre.match(ipstr):
                raise Exception('Not an IP address')
            self.ip = IPv4Address(ipstr)
  

    def __str__(self):
        return self.ip.__str__()
