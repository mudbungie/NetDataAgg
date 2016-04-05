from Database import Database

class ZabDB(Database):
    connectionProtocol = 'postgresql+psycopg2://'
    tableNames = ['hosts']
