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
        self.inspector = sqla.engine.reflection.Inspector.from_engine(self.connection)
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
        return self.connection.execute(query)

    def insert(self, table, values):
        # Defined just to allow shadowing by child classes
        q = table.insert(values)
        return self.execute(q)

    def updateLiveAndHist(self, liveTable, histTable, data):
        # liveTable and histTable == sqla.Table
        # data == list of dicts. Dicts should be column: value.

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
        #pkey = liveTable.get_pk_constraint
        pkey = sqla.engine.reflection.Inspector.from_engine(self.connection).get_primary_keys(liveTable)[0]
        for record in liveRecords:
            row = {}
            for column in columns:
                row[column] = getattr(record, column)
                #print(column, row[column])
            # We're going to address these by pkey later, so dicts
            liveData[row[pkey]] = row
        # Now, see which records are entirely new, and which need updates.
        print('Corroborating', len(data), 'data points.')
        new = 0
        updates = 0
        for datum in data:
            try:
                # Get the active record that has the same pkey.
                relevantLiveData = liveData[datum[pkey]]
                # If the data matches, nothing to be done. Otherwise...
                if not datum == relevantLiveData:
                    updates += 1
                    # When data updates, so do we!
                    # First, update the history.
                    now = datetime.now()
                    # First, expire the current historical item.
                    histFilter = sqla.and_(histTable.c.expired != None,
                        histTable.primary_key == datum[pkey])
                    histExpire = histTable.update().where(histFilter).values({'expired':now})
                    self.execute(histExpire)
                    # Now, make a new historic record
                    # We do this in a memory inefficient manner, because in 
                    # case of failure, action condition is still met, because
                    # the live table hasn't been updated.
                    histDatum = datum.copy()
                    histDatum['observed'] = now
                    histInsert = histTable.insert().values(histDatum)
                    self.execute(histInsert)
                    # The, update the live data.
                    liveUpdate = liveTable.update().\
                        where(liveTable.primary_key == datum[pkey]).\
                        values(datum)
                    self.execute(liveUpdate)
                    # Finally, append the new record to the live records dict.
                    # so that we don't conflict with records from other routers
                    liveData[datum[pkey]] = datum
                    print('Updated data for:', liveData[datum[pkey]])
                else:
                    #print('pkey ' + datum[pkey] + ' already seen')
                    pass

            except KeyError:
                # There's no matching record. This is new data, so insert it.
                # Insert is often shadowed in child classes, because of error
                # handling.
                new += 1
                print('new: ' + str(datum))
                self.insert(liveTable, datum)
        print(new, 'new records.')
        print(updates, 'updated records.')
