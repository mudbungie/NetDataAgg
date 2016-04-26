# This is the class for operating the network as a whole. It is not strictly
# subservient to the databases, but manages the network automation as a whole.

from Host import Host
from Router import Router
from Interface import Interface

class Network:
    def __init__(self):
        # It's just going to be clearer in terms of namespacing if the DB is 
        # attached.
        self.hosts = {}
        self.routers = {}
        self.globalArpTable = []
        self.globalRoutingTable = []

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

    def scanRouterArpTables(self):
        # Collects arp information on each router.
        print('Scanning ARP connections on', len(self.routers), 'routers.')
        for router in self.routers.values():
            # The router will keep the arp information locally, but it is also
            # returned, making this both an update and a query function.
            self.globalArpTable += router.getArpTable()
        return self.globalArpTable

    def scanRouterRoutingTables(self):
        # Routing data, unlike ARP, will step on itself, so it's a dict of 
        # dicts.
        for router in self.routers.values():
            # Router keeps the data in its local object, but we also aggregate.
            self.globalRoutingTable[router.ip] = router.getRoutingTable()
        return self.globalRoutingTable

    def getHosts(self):
        # We're going to iterate over all the arps, and turn them into hosts.
        for arp in self.globalArpTable:
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
            # Then, new or not, add the interface information.
            host.interfaces[mac] = interface
            host.arpNeighbors[ip] = source
        return self.hosts

    def correlateZabInfo(self, zabdb):
        #FIXME UNFINISHED
        #FIXME USE ZABBIX INTERFACE TABLE
        # Go through the Zabbix database, and attempt to crossreference info 
        # on each of the hosts, for ease of access.
        # First, grab the entire hosts table from from Zabbix.
        zabInterfaces = zabdb.getInterfaces()
        zabHosts = zabdb.getHosts()
        # Zabhosts isn't guaranteed to include IP information, but that's the
        # only way to search it.
        for host in self.hosts:
            pass
            

    def commitHosts(self, netdb):
        # Log the self.hosts object to the database.
        pass


    def initHost(ip):
        host = Host(ip)
        print(ip)
        host.getInterfaces()
        host.hasBridge()
        return host

    def getRoutes(self):
        # Scan the SNMP tables of all of the network's routers.
        self.routes = {}
        for router in self.routers.values():
            self.routes.update(router.getRoutingTable())
        print(len(routes))
        return self.routes
