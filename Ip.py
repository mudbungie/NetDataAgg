# Class for an IP address, which is the only piece of network data that we 
# can actually expect to be unique.

import re

class Ip:
    def __init__(self, ip, encoding=None):
        # Usually, a string, but there are alternatives.
        if not encoding:
            ipstr = ip
        elif encoding == 'snmp':
            # The encoding for SNMP is all malformed.
            ipstr = '.'.join(value.split('.')[1:])    
        
        # Always validate!
        ipre = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}\
            (?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
        assert re.match(ipre, ipstr)
        self.ip = ipstr
   
   def __str__(self):
        return self.ip
