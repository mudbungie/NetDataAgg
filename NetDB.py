import sqlalchemy as sqla
from datetime import datetime

import Router
from Mac import Mac

class NetDB(Database):
    # This is for the database of network data aggregation.
    # It's a postgresql DB, and the main ingestion point for all of the
    # various services on our network.
    def connection(self):
        # Construct a connection string out of the config dictionary passed
        # during init.
        connectionString = ''.join([    'postgresql+psycopg2://',
                                        self.config['user'], ':',
                                        self.config['password'], '@',
                                        self.config['host'], '/',
                                        self.config['dbname']
                                        ])
        engine = sqla.create_engine(connectionString)
        self.metadata.create_all(engine)
   
        # Define all the tables of the DB, An attribute, self.tables{} is 
        # created.
        tableNames = [  'arp',
                        'historicarp'
                        'dnslog',
                        'radius',
                        'historicradius',
                        'customers',
                        ]
        self.inittables[tableNames]

    def updateArp(network):
        # Scan all the routers in the network, update arp data.
        table = self.tables['arp']
        histTable = self.tables['historicArp']

        # Also scan the network address, because it's not a real network, but 
        # an IP range.
        hosts = [Router(network.network_address)]
        for host in network.hosts():
            # Make a list of Router objects from the addresses.
            hosts.append(Router(network.network_address))
        for router in hosts:
            # Pull the router's ARP table via SNMP
            # Returns a list of two-item dictionaries
            arpTable = router.scanArp()
            for ipaddr, macaddr in arpTable:
                self.updateLiveAndHist()
        return True

        
    def updateRadius(raddb):
    def updateCustomers(zabdb):
    
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

