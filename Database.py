# Database classes

# db adapter
import sqlalchemy as sqla
from datetime import datetime

class Database:
    # Base class, don't use directly, build subclasses.
    def __init__(self, databaseConfig):
        # The reason for the microfunction is just mobility for child classes.
        self.initDB(databaseConfig)

    def connect(self):
        # Construct a connection string out of the config dictionary passed
        # during init.

        # Define connectionProtocol and tableNames in child classes.
        connectionString = ''.join([    self.connectionProtocol,
                                        self.config['user'], ':',
                                        self.config['password'], '@',
                                        self.config['host'], '/',
                                        self.config['dbname']
                                        ])
        self.connection = sqla.create_engine(connectionString)
        self.metadata = sqla.MetaData(self.connection)

        # Initialize whatever tables this database uses
        self.initTables(self.tableNames)
        self.inspector = sqla.engine.reflection.Inspector
        return True

    def initDB(self, config):
        # Read the config into attributes
        self.config = config
        self.connect()

    def initTable(self, tableName, autoload=True):
        table = sqla.Table(tableName, self.metadata, autoload=autoload,
            autoload_with=self.connection)
        return table

    def initTables(self, tableNames):
        self.tables = {}
        for tableName in tableNames:
            self.tables[tableName] = self.initTable(tableName)

    def execute(self, query):
        # Just shorthand
        # Well, and it allows descendants to shadow for specific error handling
        return self.connection.execute(query)

    def insert(self, table, values):
        # Defined just to allow shadowing by child classes
        q = table.insert(values)
        return self.execute(q)

    def getPkey(self, table):
        pkey = self.inspector.from_engine(self.connection).\
            get_primary_keys(table)[0]
        return pkey

    def recordsToListOfDicts(self, records):
        columns = records.keys()
        data = []
        for record in records:
            datum = {}
            for column in columns:
                datum[column] = getattr(record, column)
            data.append(datum)
        return data
    
    def recordsToDictOfDicts(self, records, pkey):
        columns = records.keys()
        data = {}
        for record in records:
            datum = {}
            for column in columns:
                datum[column] = getattr(record, column)
            data[datum[pkey]] = datum
        return data

    def updateTable(self, table, newdata, pkey=None):
        # Takes the data from a table, compares it to a list of dicts by the
        # table's primary key, inserts new entries, updates changed entries.
        q = table.select()
        records = self.execute(q)
        if not pkey:
            pkey = self.getPkey(table)
        olddata = self.recordsToDictOfDicts(records, pkey)
        new = 0
        updated = 0
        unchanged = 0
        print('Corroborating', len(newdata), 'data points.')
        for newdatum in newdata:
            try:
                if not newdatum == olddata[newdatum[pkey]]:
                    # Means that we have that data, but it has changed.
                    upd = table.update().\
                        where(table.primary_key == newdatum[pkey]).\
                        values(newdatum)
                    self.execute(upd)
                    updated += 1
                else:
                    unchanged += 1
            except KeyError:
                # That's a new record, insert it.
                self.insert(table, newdatum)
                olddata[newdatum[pkey]] = newdatum
                new += 1
        print(new, 'new records.')
        print(updated, 'updated records.')
        print(unchanged, 'unchanged records.')

    def tableToDictOfDicts(self, table, pkey=None):
        # Makes all the records into dicts, puts them in a dict organized by
        # the table's pkey.
        q = table.select()
        r = self.execute(q, table)

        columns = table.c.keys()
        # So long as pkey wasn't defined, pull it from table metadata.
        if not pkey:
            pkey = self.getPkey(table)
        data = self.recordsToDictOfDicts(r, pkey)
        return data

    def updateLiveAndHist(self, currentTable, histTable, data, pkey=None):
        # currentTable and histTable == sqla.Table
        # data == list of dicts. Dicts should be column: value.

        # This is a generalized method for updating two tables at once, one of
        # which is live, and the other of which is historic. It records the
        # new information, timestamps the history, and adds a new historic
        # record for the new data

        # Pull the current data, because a single select is faster than hitting 
        # the DB for each record.
        currentq = currentTable.select()
        currentRecords = self.execute(currentq)
        # Read that data into a dictionary
        currentData = {}
        columns = currentTable.c.keys()
        # The pkey can be specified manually, but otherwise derive it.
        if not pkey:
            pkey = self.getPkey(currentTable)
        # Everything is easier with dictionaries...
        currentData = self.recordsToDictOfDicts(currentRecords, pkey)

        # Now, see which records are entirely new, and which need updates.
        print('Corroborating', len(data), 'data points.')
        new = 0
        updates = 0
        unchanged = 0
        for datum in data:
            try:
                # Get the active record that has the same pkey.
                relevantCurrentData = currentData[datum[pkey]]
                # If the data matches, nothing to be done. Otherwise...
                if not datum == relevantCurrentData:
                    updates += 1
                    # When data updates, so do we!
                    # First, update the history.
                    now = datetime.now()
                    # First, expire the current historical item.
                    histFilter = sqla.and_(histTable.c.expired == None,
                        getattr(histTable.c, pkey) == datum[pkey])
                    histExpire = histTable.update().where(histFilter).values({'expired':now})
                    self.execute(histExpire)
                    # Now, make a new historic record
                    # We do this in a memory inefficient manner, because in 
                    # case of failure, action condition is still met, because
                    # the current table hasn't been updated.
                    histDatum = datum.copy()
                    histDatum['observed'] = now
                    histInsert = histTable.insert().values(histDatum)
                    self.execute(histInsert)
                    # The, update the current data.
                    currentUpdate = currentTable.update().\
                        where(getattr(currentTable.c, pkey) == datum[pkey]).\
                        values(datum)
                    print(currentUpdate)
                    self.execute(currentUpdate)
                    # Finally, append the new record to the current records dict.
                    # so that we don't conflict with other records from the 
                    # same batch.
                    currentData[datum[pkey]] = datum
                    print('Updated data for:', currentData[datum[pkey]])
                else:
                    unchanged += 1
                    pass

            except KeyError:
                # There's no matching record. This is new data, so insert it.
                # Insert is often shadowed in child classes, because of error
                # handling.
                new += 1
                print('new: ' + str(datum))
                self.insert(currentTable, datum)
                # Finally, append the new record to the current records dict.
                # so that we don't conflict with other records from the 
                # same batch.
                currentData[datum[pkey]] = datum
        print(new, 'new records.')
        print(updates, 'updated records.')
        print(unchanged, 'unchanged records.')
