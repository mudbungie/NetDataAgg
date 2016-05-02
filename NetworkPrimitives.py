# Subscripting a string for validation, because (jingle) always validate...
# your input!

from Exceptions import InputError
import re
from binascii import hexlify

class Mac(str):
    def __new__(cls, mac, encoding=None):
        # Usually, I'll be passing a string, but not always, so encodings.
        if not encoding:
            macstr = mac.lower().replace('-',':')
        elif encoding == 'utf-16':
            # The raw data is in hex. Whole nightmare.
            s = str(hexlify(mac.encode('utf-16')))
            #print(s)
            macstr = ':'.join([s[6:8], s[10:12], s[14:16], s[18:20], s[22:24],
                s[26:28]]).lower()
            #print(macstr)
        else:
            # Should never happen, means that an unsopported encoding was
            # specified.
            raise Exception('Unsopported encoding ' + encoding)

        # Validate!
        macre = re.compile(r'([a-f0-9]{2}[:]?){6}')
        if not macre.match(macstr):
            raise InputError('Not a MAC address:', macstr)

        return super(Mac, cls).__new__(cls, macstr)


class Ip(str):
    def __new__(cls, address, encoding=None):
        # Figure out what we're being passed, convert anything to strings.
        if not encoding:
            # For just strings
            pass
        elif encoding == 'snmp':
            # Returns from SNMP come with a leading immaterial number.
            address = '.'.join(address.split('.')[1:])
        else:
            # Means invalid encoding passed.
            raise Exception('Improper encoding passed with IP address')

        # Now validate!
        # Split the address into its four octets
        ipBytes = [int(b) for b in address.split('.')]
        # Throw out anything that isn't a correct octet.
        ipBytes = [b for b in ipBytes if 0 <= b < 256]
        ipStr = '.'.join([str(b) for b in ipBytes])
        # Make sure that it has four octets, and that we haven't lost anything.
        if len(ipBytes) != 4 or ipStr != address:
            raise InputError('Improper string submitted for IP address')

        # Sound like everything's fine!
        return super(Ip, cls).__new__(cls, address)

    def bits(self):
        # For converting the IP to bits, usually for CIDR notation.
        octets = self.split('.')
        # Start high and count down, so that we can use efficient bitwise ops.
        bits = 32
        for octet in octets:
            # Invert it, because netmask is backwards.
            octet = 255 - int(octet)
            while octet > 0:
                bits -= 1
                # Bitwise left-shift the octet.
                octet = octet >> 1
        return bits
