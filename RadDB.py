from Database import Database

class RadDB(Database):
    # The only thing this class does is dump the entire RADIUS database.
    # That's because it has a completely prohibitive 1.5s latency on all 
    # queries, so we just want to extricate that data.
    def connection(self):
        # Construct a connection string out of the config dictionary passed
        # during init.
        connectionString = ''.join([    'mysql+pymysql://',
                                        self.user, ':'
                                        self.password, '@'
                                        self.host, '/'
                                        self.dbname,
                                        ])
        engine = sqla.create_engine(connectionString)
        self.metadata.create_all(engine)

        # There's really just the one table that we access.
        tableNames = ['username_mac']
        self.initTables(tableNames)

    def fetchRadData(self):
        # Pull the entire table. 
        table = self.tables['username_mac']
        radQuery = table.select()
        radRecords = self.connection.execute(radQuery)

        radData = []
        for radrecord in radRecords:
            # The usernames refer to zabbix userids. but sometimes have extra
            # alpha characters, because of multiple links.
            username = radRecord.username
            # Do even fucking ask where that column name came from
            mac = radRecord.Name_exp_2
            # All lookups will be based on the actual zabbix id, which is an 
            # integer, so we want to index by that.
            zabId = int(''.join(c for c in radRecord.username if \
                c.isdigit()))
            # Then we save that into a dict
            radDatum = {}
            radDatum['zabId'] = zabId
            radDatum['mac'] = mac
            radDatum['username'] = username
            # Which we append to the list.
            radData.append(radDatum)
        return radData
