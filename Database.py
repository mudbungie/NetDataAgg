# Database classes

# db adapter
import sqlalchemy as sqla
import datetime

class Database:
    # Base class, don't use directly, build subclasses.
    def __init__(self, databaseConfig):
        # The reason for the microfunction is just mobility for child classes.
        self.initDB(databaseConfig)

    def initDB(self, config):
        # Read the config into attributes
        self.config = config
        self.connect()

    def initTable(self, tableName, autoload=True):
        table = sqla.Table(tableName, self.metadata, autoload=autoload,
            autoload_with=self.connection)
        return table

    def initTables(self, tablesNames):
        self.tables = {}
        for tableName in tableNames:
            self.tables[tableName] = self.initTable[tableName]

    def execute(self, query):
        # Just shorthand
        return self.connection.execute(query)
    
    def insert(self, data, table):
        # Take a dict of values and a table, find the keys that match columns,
        # insert into those columns. 

        # Iterate the columns, find matches
        values = {}
        for column in table.columns:
            # Table.columns is fully qualified; need just the name
            column = str(column).split('.')[1]
            # See what fits:
            try:
                values[column.lower[()] = data[column]
            except KeyError:
                # Non-matching data is discarded
                pass

        # Check that you're inserting something at all
        if len(values) == 0:
            raise Exception('Empty insert, probable table-value mismatch')
           
        # Compile the SQL
        insert = table.insert().values(**values)
        # Might as well return something
        pkey = self.connection.execute(insert).inserted_primary_key
        return pkey

    def updateLiveAndHist(liveTable, histTable, data):
        # liveTable and histTable == sqla.Table
        # data == list of dicts. Dicts should be column, value.

        # This is a generalized method for updating two tables at once, one of
        # which is live, and the other of which is historic. It records the
        # new information, timestamps the history, and adds a new historic
        # record for the new data

        # Pull the live data, because a single select is faster than hitting 
        # the DB for each record.
        liveq = liveTable.select()
        liveRecords = self.execute(liveq)
        # Read that data into a dictionary
        liveData = {}
        columns = liveTable.c.keys()
        pkey = liveTable.primary_key
        for record in liveRecords:
            row = {}
            for column in columns:
                row[column] = getattr(record, column)
            liveData[pkey] = row

        # Now, see which records are entirely new, and which need updates.
        for datum in data:
            try:
                # Get the active record that has the same pkey.
                relevantLiveData = liveData[datum[pkey]]
                # If the data matches, nothing to be done. Otherwise...
                if not datum == relevantLiveData:
                    # When data updates, so do we!
                    # First, update the live data.
                    liveUpdate = liveTable.update().\
                        where(liveTable.primary_key == data).\
                        values(data)
                    self.execute(liveUpdate)
                    # Then, update the history.
                    now = datetime.now()
                    # First, expire the current historical item.
                    histFilter = sqla.and_(histTable.c.expired != None,
                        histTable.primary_key == data[pkey])
                    histExpire = histTable.update().where(histFilter).\
                        values('expired'=now)
                    self.execute(histExpire)
                    # Now, make a new historic record
                    data['observed'] = now
                    histInsert = histTable.insert().values(data)
                    self.execute(histInsert)
                    
            except KeyError:
                # There's no matching record. This is new data, so insert it.
                insert = liveTable.insert(data)
                self.execute(insert)

