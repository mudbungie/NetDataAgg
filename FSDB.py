# Freeside is our billing and accounting system.

from Database import Database
from Ip import Ip

class FreesideDB(Database):
    connectionProtocol = 'postgresql+psycopg2://'
    tableNames = ['cust_main']

    def updateCustomers()


