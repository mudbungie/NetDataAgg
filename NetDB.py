# Not mine
import sqlalchemy as sqla
from datetime import datetime
# Mine
from Database import Database
from Router import Router
from Mac import Mac
from Host import Host

class NetDB(Database):
    # This is for the database of network data aggregation.
    # It's a postgresql DB, and the main ingestion point for all of the
    # various services on our network.

    # It's postgres.
    connectionProtocol = 'postgresql+psycopg2://'
    tableNames = [  'arp',
                    'historicarp',
                    'dnslog',
                    'radius',
                    'historicradius',
                    'customers',
                    'routers',
                    'hosts',
                    'bridged_hosts',
                    ]

    def updateArp(self, network, community):
        # Scan all the routers in the network, update arp data.
        table = self.tables['arp']
        histTable = self.tables['historicarp']

        # Also scan the network address, because it's not a real network, but 
        # an IP range.
        hosts = self.getRouters()
        #print('network address')
        #print(network.network_address)
        #hosts.append(Router(network.network_address, community))

        for host in hosts:
            # Make a list of Router objects from the addresses.
            router = Router(host, community)
            # Pull the router's ARP table via SNMP
            # Returns a list of dictionaries
            arpTable = router.getArpTable()
            print(router.ip, 'has', len(arpTable), 'arp entries.')
            self.updateLiveAndHist(table, histTable, arpTable)
        return True

    def updateRadius(self, raddb):
        radData = raddb.fetchRadData()
        table = self.tables['radius']
        histTable = self.tables['historicradius']
        self.updateLiveAndHist(table, histTable, radData)
        return True

    def updateCustomers(self, fsdb):
        customers = fsdb.getCustomers()
        self.updateTable(self.tables['customers'], customers)
        return True

    def updateHosts(self, zabdb):
        hosts = zabdb.getHosts()
        self.updateTable(self.tables['hosts'], hosts)
        return True

    def arpLookup(ip=None, mac=None):
        table = self.initTable('arp')

        if ip:
            # Get matching ARP data
            q = table.select().where(table.c.ip == ip)
            macs = []
            # Go through all matching records
            for record in self.connection.execute(q):
                # Instantiate results
                mac = Mac(record.mac)
                macs.append(mac)
            return macs
        elif mac:
            # Get matching ARP data
            q = table.select().where(table.c.mac == mac)
            ips = []
            # Go through all matching records
            for record in self.connection.execute(q):
                # Instantiate results
                ip = Ip(record.ip)
                ips.append(ip)
            return ips
        else:
            # Gotta give one or the other
            return False

    def radLookup(mac):
        table = self.initTable('radius')

        q = table.select().where(table.c.mac == mac)
        # This table should be unique by MAC address, because redundant records
        # are expunged to historicarp.
        record = self.connection.execute(q).fetchone()
        username = record.username
        return username

    def getRouters(self):
        table = self.tables['routers']
        self.routers = []
        q = table.select()
        rows = self.execute(q)
        routers = []
        for row in rows:
            routers.append(row.managementip)
        return routers
    
    def checkZabbixAgainstArp(self):
        # When Zabbix and ARP think that an address is registered to a
        # different MAC address, that can be cause for alarm.

        #FIXME Use the ORM
        q = 'select hosts.mac as zabmac, hosts.ip, arp.mac as arpmac from ' +\
                'hosts, arp where hosts.mac is not null and hosts.ip is not '+\
                'null and hosts.ip = arp.ip and hosts.mac != arp.mac;'
        mismatches = self.execute(q)
        offline = []
        unknown = []
        differentLink = []
        if mismatches:
            for mismatch in mismatches:
                #print(mismatch.ip)
                # Make a host, get the data from the host.
                host = Host(mismatch.ip)
                host.getInterfaces()
                if host.online:
                    # See if the address is among its interfaces.
                    if host.hasMac(mismatch.zabmac):
                        differentLink.append(mismatch) 
                    else:
                        print(mismatch.ip, 'mismatched for unknown reasons.')
                        unknown.append(mismatch)
                        #print(len(unknown))
                else:
                    offline.append(mismatch)
        else:
            print('There are no mismatched addresses.')

        print('There are', len(offline), 'offline hosts.')
        print('There are', len(differentLink), 'hosts that were simply',
            'detected on a different link.')
        print('There are', len(unknown), 'undiagnosed hosts.')

    def checkForBridgedHosts(self):
        # Get all known bridges
        bHostsTable = self.tables['bridged_hosts']
        q = bHostsTable.select()
        bridgeRecords = self.execute(q)
        knownBridges = {}
        for bridgeRecord in bridgeRecords:
            # Make it a dict
            knownBridges[bridgeRecord.ip] = bridgeRecord.mac
            
        # Get all hosts
        hostsTable = self.tables['hosts']
        q = hostsTable.select()
        hostRecords = self.execute(q)
        for hostRecord in hostRecords:
            # Double check that there is a recorded address.
            if hostRecord.ip:
                # Make a network object out of them.
                host = Host(hostRecord.ip)
                # And scan their interfaces for redundant MAC addresses.
                bridgedMac = host.hasBridge()
                # Will be false if there are no bridges.
                if bridgedMac:
                    print(1)
                    liveBridge = {'ip':host.ip,'mac':bridgedMac}
                    try:
                        if bridgedMac != knownBridges[host.ip]:
                            # If it's changed, update. Otherwise, do nothing.
                            q = bHostsTable.update().\
                                where(bhostsTable.c.ip == host.ip).\
                                values(liveBridge)
                            self.execute(q)
                            knownBridges[host.ip] = bridgedMac
                    except KeyError:
                        # It's a newly discovered bridged. Insert it.
                        self.insert(bHostsTable, liveBridge)
                        knownBridges[host.ip] = bridgedMac
                else:
                    # It's not a bridge, gotta make sure that it's not hanging
                    # around in the table.
                    if host.ip in knownBridges:
                        q = bHostsTable.delete().\
                            where(bhostsTable.c.ip == host.ip)
                        self.execute(q)
