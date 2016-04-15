# Class for Mac addresses

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
            raise Exception('Not a MAC address:', macstr)

        return super(Mac, cls).__new__(cls, macstr)
