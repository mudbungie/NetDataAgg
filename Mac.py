# Class for Mac addresses

import re

class Mac:
    def __init__(self, mac, encoding=None):
        # Usually, I'll be passing a string, but not always, so encodings.
        if not encoding:
            macstr = mac.lower().replace('-',':')
        elif encoding == 'utf-16':
            # The raw data is in hex. Whole nightmare.
            s = str(hexlify(value.encode('utf-16')))
            macstr = ':'.join([s[6:8], s[10:12], s[14:16], s[18:20], s[22:24],
                s[26:28]]).lower()
        macre = re.compile(r'([a-f0-9]{2}[:]?){6}')
        assert re.match(macre, mac)
        self.mac = macstr
    def __str__(self):
        return self.mac
