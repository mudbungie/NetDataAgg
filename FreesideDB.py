# Freeside is our billing and accounting system.

from Database import Database
from NetworkPrimitives import Ip
from functions import sanitizeString

class FreesideDB(Database):
    connectionProtocol = 'postgresql+psycopg2://'
    tableNames = ['cust_main']

    def getCustomers(self):
        q = self.tables['cust_main'].select()
        records = self.execute(q)
        custs = []
        for record in records:
            cust = {}
            cust['custnum'] = record.custnum
            cust['name'] = sanitizeString(' '.join([record.first, record.last]))
            cust['company'] = sanitizeString(record.company)
            cust['payname'] = sanitizeString(record.payname)
            custs.append(cust)
        return custs

