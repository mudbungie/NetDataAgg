# This is the class for operating the network as a whole. It is not strictly
# subservient to the databases, but manages the network automation as a whole.

from Host import Host
from Interface import Interface
from multiprocessing import Pool
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
        
        interfaces = {} # We'll use this to corroborate data.
        ips = []
        for arp in arps:
            interface = Interface(arp['mac'])
            interface.ip = arp['ip']
            interfaces[interface.ip] = interface
            ips.append(interface.ip)

        pool = Pool(50)
        # We have to invoke an external function because of multithreading 
        # weirdness.
        self.hosts = pool.map(functions.initHost, ips)
        return hosts

