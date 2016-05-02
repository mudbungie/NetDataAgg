# Not mine
import sqlalchemy as sqla
from datetime import datetime
import os
import time
import re
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
                    'nexthops',
                    ]

    def updateArp(self, arps):
        # Takes a lists of dictionaries in format ip, mac, source, and
        # commits them to the database.
        table = self.tables['arp']
        histTable = self.tables['historicarp']
        self.updateLiveAndHist(table, histTable, arps)
        return True
    
    def updateRoutes(self, routingtables):
        # Takes list of dicts in format address, netmask, nexthop, router, key,
        # and commits them to the database.
        table = self.tables['routes']
        histTable = self.tables['historicroutes']
        for routingtable in routingtables:  
            self.updateLiveAndHist(table, histTable, routingtable)
    
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

    def updateRoutes(self, router):
        # Takes a dictionary from a Router, commits it to the Routes table,
        # and has a mapped dependent table for the destination, because that
        # relationship is one-to-many.
        routesTable = self.tables['routes']
        nextHopTable = self.tables['nexthops']
        routeraddr = router.ip
        routingdata = router.routingTable
        
        # We'll start by just pulling both tables so that they're easier to 
        # work with.
        # The routes table has a info on other routers, which we don't want.
        oldRoutesQuery = routesTable.select().\
            where(routesTable.c.router == routeraddr)
        r = self.recordsToDictOfDicts(self.execute(oldRoutesQuery), 'address')
        oldRoutes = self.GetDependentRecords(r, nextHopTable, 'routeid')
        print('Retrieved', len(oldRoutes), 'old routes.')

        # Now that the old routes are normalized, we'll check for updates and
        # new records. 
        newRoutes = 0
        stableRoutes = 0
        purgedRoutes = 0
        updatedRoutes = 0
        newHops = 0
        stableHops = 0
        purgedHops = 0 
        self.updateTableAndDep(routingdata, oldRoutes, routesTable, nextHopTable)
        '''
        # Hops don't get updated.
        for route in routingdata.values():
            try:
                # This line fails if the route is new, and we insert.
                oldRoute = oldRoutes[route['address']]
                index = oldRoute['routeid']
                if route['netmask'] != oldRoute['netmask']:
                    # For updates, we need to match id.
                    iroute = route.copy()
                    iroute['routeid'] = index
                    del iroute['nexthops']
                    self.update(routesTable, route)
                    updatedRoutes += 1
                else:
                    stableRoutes += 1
                
                currenthops = route['nexthops']
                try:
                    oldhops = oldRoute['nexthops']
                except KeyError:
                    # Means that an old route has no hops, which means it is
                    # defunct. Should be purged.
                    self.delete(routesTable, oldRoute['routeid'])
                    purgedRoutes += 1
                    oldhops = []

                # Add in new hops...
                for hop in currenthops:
                    if hop not in oldhops:
                        self.insert(nextHopTable, {'routeid':index,'nexthop':hop})
                        newHops += 1
                    else:
                        stableHops += 1
                # and purge the old.
                for hop in oldhops:
                    if hop not in currenthops:
                        self.deleteHop(hop['routeid'], hop['nexthop'])
                        purgedHops += 1

            except KeyError:
                index = self.insertRoute(route)
                newRoutes += 1
                newHops += len(route['nexthops'])

        # Don't forget to purge old routes!
        for route in oldRoutes.values():
            try:
                # If the old record isn't in the new records.
                routingdata[route['address']]
            except KeyError:
                self.delete(routesTable, route['routeid'])
                purgedRoutes += 1
                # And orphaned hops!
                q = nextHopTable.delete().\
                    where(nextHopTable.c.routeid == route['routeid'])
                self.execute(q)
                

        print('Recorded', newRoutes, 'new routes, updated', updatedRoutes,
            'old routes, and purged', purgedRoutes, 'defunct routes.')
        print(stableRoutes, 'consistent routes were unaffected.')
        print('Recorded', newHops, 'new nexthops, purged', purgedHops,
            'defunct nexthops.')
        print(stableHops, 'consistent hops were unaffected.')
        '''

    def insertRoute(self, route):
        routesTable = self.tables['routes']
        nextHopTable = self.tables['nexthops']
        # We need to take the hops out, and handle them separately. We insert
        # the route, then takes its primary key as an id to index the routes.
        hops = route['nexthops']
        iroute = route.copy()
        del iroute['nexthops']
        index = self.insert(routesTable, iroute).inserted_primary_key[0]
        inserts = 0
        for hop in hops:
            self.insert(nextHopTable, {'routeid':index,'nexthop':hop})
            inserts += 1
        return inserts

    def deleteHop(self, routeid, nexthop):
        #FIXME Generalize this and put it into Database.py.
        t = self.tables['nexthops']
        q = t.delete().where(sqla.and_(t.c.routeid == routeid, t.c.nexthop == nexthop))
        self.execute(q)
