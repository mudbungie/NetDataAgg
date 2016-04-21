# This is the class for operating the network as a whole. It is not strictly
# subservient to the databases, but manages the network automation as a whole.

from Host import Host
from Router import Router
from Interface import Interface

class Network:
    def __init__(self, netdb):
        # It's just going to be clearer in terms of namespacing if the DB is 
        # attached.
        self.netdb = netdb
        self.hosts = {}

    # Hosts are a dict by IP
    @property
    def hosts(self):
        return self.__hosts
    @hosts.setter
    def hosts(self, hosts):
        self.__hosts = hosts
    @property
    def routerCommunity(self):
        return self.__routerCommunity
    @routerCommunity.setter
    def routerCommunity(self, routerCommunity):
        self.__routerCommunity = routerCommunity
    # Routers are also a dict by IP, but they need SNMP creds on init.
    @property
    def routers(self):
        return self.__routers
    @routers.setter
    def routers(self, ips):
        self.__routers = {}
        for ip in ips:
            router = Router(ip, self.routerCommunity)
            self.__routers[ip] = router
            # Any router is also a host.
            self.hosts[ip] = router

    def getHosts(self):
        # First, collect all of the ARP data from each of the routers.
        arpTable = []
        for router in self.routers.values():
            # Tack together their routing tables.
            arpTable += router.getArpTable()

        # We're going to iterate over all the arps, and turn them into hosts.
        for arp in arpTable:
            ip = arp['ip']
            mac = arp['mac']
            source = self.routers[arp['source']]
            interface = Interface(mac)
            interface.ip = ip
            try:
                # Assuming that this host exists.
                host = self.hosts[ip]
            except KeyError:
                # If it doesn't, then add it in.
                host = Host(ip)
                self.hosts[ip] = host
            host.interfaces[mac] = interface
            host.arpNeighbors[ip] = source
        return self.hosts


    def initHost(ip):
        host = Host(ip)
        print(ip)
        host.getInterfaces()
        host.hasBridge()
        return host
    '''
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
    '''
