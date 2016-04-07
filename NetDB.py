# Not mine
import sqlalchemy as sqla
from datetime import datetime
# Mine
from Database import Database
from Router import Router
from Mac import Mac

class NetDB(Database):
    # This is for the database of network data aggregation.
    # It's a postgresql DB, and the main ingestion point for all of the
    # various services on our network.

    # It's postgres.
    connectionProtocol = 'postgresql+psycopg2://'
    tableNames = [ 'arp',
                    'historicarp',
                    'dnslog',
                    'radius',
                    'historicradius',
                    'customers',
                    ]
    
    def insert(self, table, values):
        q = table.insert(values)
        try:
            return self.execute(q)
        except sqla.exc.IntegrityError as IntegrityError:
            # This shows up in the case of a redundant MAC address insert.
            # Those errors occur because Juniper Routers have an actual IP
            # stack implemented for internal routing, and the addresses used 
            # are not unique. We discard such exceptions.
            #print('##EXCEPTION MATCHED###')
            # If this is the second hex of the first octet, it's reserved.
            localMacs = ['2', '6', 'a', 'e']
            try:
                if values['mac'][1] in localMacs:
                    pass
                else:
                    #print('1')
                    #print(values['mac'])
                    raise IntegrityError
            except NameError:
                # Inserting something other than a MAC
                for key, value in values:
                    print(key, value)
                print('Primary key collision on something other than a MAC')
                raise IntegrityError
                

    def execute(self, query):
        # Shadowing the parent class' execute function is a great way to
        # handle DB exceptions without having to reimplement general methods
        return self.connection.execute(query)

    def updateArp(self, network, community):
        # Scan all the routers in the network, update arp data.
        table = self.tables['arp']
        histTable = self.tables['historicarp']

        # Also scan the network address, because it's not a real network, but 
        # an IP range.
        hosts = []
        #print('network address')
        #print(network.network_address)
        hosts.append(Router(network.network_address, community))

        for host in network.hosts():
            print(host)
            # Make a list of Router objects from the addresses.
            hosts.append(Router(host, community))
        arpTable = []
        for router in hosts:
            print(router.ip)
            # Pull the router's ARP table via SNMP
            # Returns a list of two-item dictionaries
            arpTable += router.getArpTable()
            print(len(arpTable))
        self.updateLiveAndHist(table, histTable, arpTable)
        return True

    def updateRadius(raddb):
        radData = raddb.fetchRadData()
        table = self.tables['radius']
        histTable = self.tables['historicradius']
        self.updateLiveAndHist(table, histTable, radData)

    def updateCustomers(zabdb):
        pass
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

