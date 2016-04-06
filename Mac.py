# Class for Mac addresses

import re
from binascii import hexlify

class Mac:
    def __new__(self, mac, encoding=None):
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
            #print(mac)
            raise Exception('Not a MAC address!')

        self.mac = macstr
        return macstr
    #def __str__(self):
    #    return self.mac.__str__()
