# Not mine
import sqlalchemy as sqla
from datetime import datetime
import os
import time
import re
# Mine
from Database import Database
from Router import Router
from Mac import Mac
from Ip import Ip
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
                    'zabhosts',
                    'hosts',
                    'bridged_hosts',
                    'bad_usernames',
                    ]

    def updateArp(self, community):
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
        self.updateTable(self.tables['zabhosts'], hosts)
        return True

    def arpLookup(self, ip=None, mac=None):
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

    def getArps(self):
        table = self.tables['arp']
        arpRecords = self.execute(table.select())
        arps = []
        for record in arpRecords:
            # Make a little dict
            arps.append({'ip':record.ip,'mac':record.mac})
        return arps

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
        q = 'select zabhosts.mac as zabmac, zabhosts.ip, arp.mac as arpmac from ' +\
                'zabhosts, arp where zabhosts.mac is not null and zabhosts.ip is not '+\
                'null and zabhosts.ip = arp.ip and zabhosts.mac != arp.mac;'
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

    def getNetworkHosts(self):
        # Checks Zabbix for registered IP addresses, and returns a list of host
        # objects.
        hostsTable = self.tables['zabhosts']
        q = hostsTable.select()
        hostRecords = self.execute(q)

        hosts = []
        for hostRecord in hostRecords:
            # Double check that there is a recorded address.
            if hostRecord.ip:
                # Make a network object out of them.
                host = Host(hostRecord.ip)
                hosts.append(host)
        return hosts

    def checkForBridgedHosts(self):
        # Get all known bridges
        bHostsTable = self.tables['bridged_hosts']
        q = bHostsTable.select()
        bridgeRecords = self.execute(q)
        knownBridges = {}
        for bridgeRecord in bridgeRecords:
            # Make it a dict
            knownBridges[bridgeRecord.ip] = bridgeRecord.mac
            
        hosts = self.getNetworkHosts()
        newPid = 0
        for host in hosts:
            # These scans are time-consuming, but simple, so fork.
            time.sleep(.1) # Don't flood so bad
            if newPid == 0: # If you're the parent
                try:
                    newPid = os.fork() 
                    if newPid != 0: # If you're not the parent
                        finished = False
                        while not finished:
                            # And scan their interfaces for redundant MAC addresses.
                            bridgedMac = host.hasBridge()
                            # Will be false if there are no bridges.
                            if bridgedMac:
                                liveBridge = {'ip':host.ip,'mac':bridgedMac}
                                try:
                                    if bridgedMac != knownBridges[host.ip]:
                                        # If it's changed, update.
                                        q = bHostsTable.update().\
                                            where(bhostsTable.c.ip == host.ip).\
                                            values(liveBridge)
                                        self.execute(q)
                                        knownBridges[host.ip] = bridgedMac
                                        finished = True
                                    else:
                                        # Unchanged: do nothing.
                                        finished = True
                                except KeyError:
                                    # It's a newly discovered bridged. Insert it.
                                    self.insert(bHostsTable, liveBridge)
                                    knownBridges[host.ip] = bridgedMac
                                    finished = True
                            else:
                                # It's not a bridge, gotta make sure that it's not hanging
                                # around in the table.
                                if host.ip in knownBridges:
                                    q = bHostsTable.delete().\
                                        where(bhostsTable.c.ip == host.ip)
                                    self.execute(q)
                                    finished = True
                except BlockingIOError:
                    # Means that the OS wouldn't let us spawn processes that fast.
                    # Just try again.
                    pass
        print('done')

    def updateBadUsernames(self):
        # Checks to see what hosts don't contain their radius username in their
        # hostname. 
        table = self.tables['hosts']
        hosts = self.execute(table.select())
        bad_usernames = []
        for host in hosts:
            # Extraneous text won't show up in the username.
            #custnum = ''.join(c for c in host.username if c.isdigit())
            custnum = re.match(r'^[0-9]*', host.username).group()
            # Test if it's missing the username, or username lacks numbers.
            if len(custnum) == 0 or not custnum in host.hostname:
                bad_username = {'hostname':host.hostname,
                    'username':host.username,
                    'ip':host.ip}
                bad_usernames.append(bad_username)
        self.updateTable(self.tables['bad_usernames'], bad_usernames)

    def getBadUsernames(self):
        table = self.tables['bad_usernames']
        records = self.execute(table.select())
        badUsernames = self.recordsToListOfDicts(records)
        return badUsernames
