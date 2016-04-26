# Sometimes, you need just a function. 

from Host import Host
import unicodedata

def initHost(ip):
    #print('Scanning', ip)
    host = Host(ip)
    host.getInterfaces()
    if host.online == False:
        #print('Host with ip', ip, 'offline!')
        print(ip)
    host.hasBridge()
    return host

def sanitizeString(dirty):
    try:
        clean = unicodedata.normalize('NFKD', dirty).encode('ascii', 'ignore')
    except TypeError:
        if dirty == None:
            return dirty
        else:
            raise
    return clean
