# Subscripting a string for IP validation, because (jingle) always validate...
# your input!

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
            raise AssertionError('Improper string submitted for IP address')

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
