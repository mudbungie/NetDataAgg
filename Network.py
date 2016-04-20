# This is the class for operating the network as a whole. It is not strictly
# subservient to the databases, but manages the network automation as a whole.

from multiprocessing import Pool
from operator import itemgetter
import re

from Host import Host
from Interface import Interface
import functions

class Network:
    def __init__(self, netdb):
        self.netdb = netdb

    def initHost(ip):
        host = Host(ip)
        print(ip)
        host.getInterfaces()
        host.hasBridge()
        return host
    
    def getHosts(self):
        #FIXME BROKEN, WILL CORE DUMP. MULTITHREADING:HARD
        # Go through the ARP records in the netDB, and make host objects.
        # Also, I'm assuming that any connection in the network is known
        # to the routers that I scan. Let's hope THAT'S true.

        # Returns a list
        arps = self.netdb.getArps()
        # Sort the list. There is no functional reason for this, but it makes
        # observation of scan-time idiosyncrasies easier. 
        arps = sorted(arps,key=lambda a: a['ip'])
        
        interfaces = {} # We'll use this to corroborate data.
        ips = []
        print('There are', len(arps), 'hosts in the network.')
        inaccessibleNets = ['172.3','172.1','172.20','10.22','199.68','20','10.2','10.3']
        for arp in arps:
            # Some parts of the network are dead space.
            checkIt = True
            for net in inaccessibleNets:
                if arp['ip'].startswith(net):
                    checkIt = False
            if checkIt:
                interface = Interface(arp['mac'])
                interface.ip = arp['ip']
                interfaces[interface.ip] = interface
                ips.append(interface.ip)
            else:
                print(arp['ip'], 'not scanned.')

        pool = Pool(50)
        # We have to invoke an external function because of multithreading 
        # weirdness.
        self.hosts = pool.map(functions.initHost, ips)
        return self.hosts

