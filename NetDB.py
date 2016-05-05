# Not mine
from datetime import datetime
import sqlalchemy as sqla
import os
import time
import re
import ipaddress
# Mine
from Database import Database
from Router import Router
from NetworkPrimitives import Mac, Ip
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
                    'routes',
                    'historicroutes',
                    ]

    def updateArp(self, arps):
        # Takes a lists of dictionaries in format ip, mac, source, and
        # commits them to the database.
        table = self.tables['arp']
        histTable = self.tables['historicarp']
        self.updateLiveAndHist(table, histTable, arps)
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

    def updateZabHosts(self, zabdb):
        hosts = zabdb.getHosts()
        self.updateTable(self.tables['zabhosts'], hosts)
        return True

    def arpLookup(self, query):
        t = self.initTable('arp')

        if type(query) == Ip:
            records = self.execute(t.select().where(t.c.ip == query))
        elif type(query) == Mac:
            records = self.execute(t.select().where(t.c.mac == query))
        else:
            raise Exception # Should never happen
        return self.recordsToListOfDicts(records)

    def getArps(self):
        table = self.tables['arp']
        arpRecords = self.execute(table.select())
        arps = []
        for record in arpRecords:
            # Make a little dict
            arps.append({'ip':record.ip,'mac':record.mac})
        return arps

    def radLookup(self, mac):
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

    def hostLookup(self, query):
        t = self.tables['hosts']
        if type(query) == Ip:
            records = self.execute(t.select().where(t.c.ip == query))
        elif type(query) == Mac:
            records = self.execute(t.select().where(t.c.mac == query))
        else:
            records = self.execute(t.select().where(t.c.hostname.\
                ilike('%'+query+'%')))
        return self.recordsToListOfDicts(records)

    def getBadUsernames(self):
        table = self.tables['bad_usernames']
        records = self.execute(table.select())
        badUsernames = self.recordsToListOfDicts(records)
        return badUsernames

    def updateAllRoutes(self, routers):
        for router in routers:
            self.updateRoutes(router)

    def updateRoutes(self, router):
        # Takes a dictionary from a Router, commits it to the Routes table,
        # and has a mapped dependent table for the destination, because that
        # relationship is one-to-many.
        t = self.tables['routes']
        ht = self.tables['historicroutes']
        now = datetime.now()
        routeraddr = router.ip
        newRoutes = router.routes
        q = t.select().where(t.c.router == routeraddr)
        oldRouteList = self.recordsToListOfDicts(self.execute(q))
        oldRoutes = {}
        # Make an index out of the relevant route data, so that lookups aren't
        # so expensive,
        for r in oldRouteList:
            oldRoutes[r['destination']+str(r['netmask'])+r['nexthop']] = r

        # We're going to depopulate the olds and expire anything that remains,
        # insert anything that wasn't there to expire, and ignore anything 
        # that occurs in both routing tables.
        new = 0
        old = 0
        expired = 0
        for key, route in newRoutes.items():
            try:
                # Means that we've seen it, do nothing.
                del oldRoutes[key]
                old += 1
            except KeyError:
                # It's new, insert it.
                self.insert(t, route)
                # Also, put it in the historic table.
                route['observed'] = now
                self.insert(ht, route)
                new += 1
        # Anything left in this list after the purge is outdated. Expire it!
        for r in oldRoutes.values():
            # Expire the historic record.
            q = ht.update().where(sqla.and_(ht.c.destination == r['destination'],
                ht.c.netmask == r['netmask'], ht.c.nexthop == r['nexthop'])).\
                values(expired=now)
            self.execute(q)
            # Delete the current record.
            q = t.delete().where(sqla.and_(t.c.destination == r['destination'],
                t.c.netmask == r['netmask'], t.c.nexthop == r['nexthop']))
            self.execute(q)
            expired += 1
        print('Router at',routeraddr,'corroborated',old,
            'previously known routes, and reported',new,
            'previously known routes.')
        print(expired,'unconfirmed routes have been expired from the database.')
        return new, old, expired

    def findRoutes(self, destination):
        # When given an address, find out how it would be routed.
        # Start off checking smaller routes, and grow larger.
        r = self.tables['routes']
        netmask = 32
        data = []
        while netmask >= 0:
            print('Checking netmask', netmask, 'destination', destination)
            q = r.select().where(sqla.and_(r.c.netmask == netmask,
                r.c.destination == destination))
            routes = self.execute(q)

            if routes.rowcount > 0:
                for route in routes:
                    datum = {'destination':route.destination,
                        'netmask':route.netmask,
                        'nexthop':route.nexthop,
                        'router':route.router}
                    data.append(datum)
                return data
                
            # If we didn't find it there, expand to the next smallest network.
            netmask -= 1
            destination = str(ipaddress.ip_network(destination).\
                supernet(new_prefix=netmask).network_address)

        return None

    def findValidRoutes(self, destination):
        # Return all routes for an address that the router can execute via ARP.
        routes = self.findRoutes(destination)
        # Get arps, and index them so that we can look them up.
        arpRecords = self.execute(self.tables['arp'].select())
        arps = {}
        for record in arpRecords:
            arps[record.source + record.ip] = record.mac
        # Then, add in MAC information to those routes that exist, and purge
        # anything that isn't arp-resolvable.
        validRoutes = []
        for route in routes:
            try:
                route['nexthopmac'] = arps[route['router'] +\
                    route['nexthop']]
                validRoutes.append(route)
            except KeyError:
                print(route)
                pass
        return validRoutes
