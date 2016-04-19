# Zabbix is a network management database

from Database import Database
from Ip import Ip

import re

class ZabDB(Database):
    connectionProtocol = 'postgresql+psycopg2://'
    tableNames = ['hosts', 'host_mac']

    def getHostMac(self, hostid):
        table = self.tables['host_mac']
        q = table.select().\
            where(table.c.hostid == hostid)
        try:
            mac = self.execute(q).fetchone().mac
        except AttributeError:
            # Means that we didn't get any matching records; Zabbix doesn't
            # know a mac address for this host.
            return None
        return mac

    def getIpFromDirtyString(self, string):
        regex = re.compile(r'(?:[0-9]{1,3}\.){3}[0-9]{1,3}')
        ip = self.searchDirtyString(regex, string)
        return ip

    def getFSIdFromDirtyString(self, string):
        regex = re.compile(r'C[0-9]{1,5}')
        fsid = self.searchDirtyString(regex, string)
        if fsid:
            return int(fsid.replace('C',''))
        else:
            # Null return
            return fsid

    def getPkgnumFromDirtyString(self, string):
        regex = re.compile(r'P[0-9]{1,6}')
        pkgnum = self.searchDirtyString(regex, string)
        if pkgnum:
            return int(pkgnum.replace('P',''))
        else:
            # Null return
            return pkgnum

    def searchDirtyString(self, regex, string):
        try:
            return regex.findall(string)[0]
        except IndexError:
            # In the event that nothing is found, just return an empty string.
            return None
        
    def getHosts(self):
        q = self.tables['hosts'].select()
        records = self.execute(q)
        hosts = []
        for record in records:
            host = {}
            host['hostid'] = record.hostid
            host['hostname'] = record.name
            host['mac'] = self.getHostMac(host['hostid'])
            # This field is so dirty
            host['ip'] = self.getIpFromDirtyString(record.host)
            host['fsid'] = self.getFSIdFromDirtyString(record.host)
            host['pkgnum'] = self.getPkgnumFromDirtyString(record.host)
            hosts.append(host)
        return hosts
