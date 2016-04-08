import sqlalchemy as sqla

from Database import Database
from Mac import Mac

class RadDB(Database):
    # The only thing this class does is dump the entire RADIUS database.
    # That's because it has a completely prohibitive 1.5s latency on all 
    # queries, so we just want to extricate that data.
    connectionProtocol = 'mysql+pymysql://'
    tableNames = ['radacct']

    def fetchRadData(self):
        # Pull the entire table. 
        table = self.tables['radacct']
        radQuery = table.select()
        radRecords = self.connection.execute(radQuery)

        radData = {}
        for radRecord in radRecords:
            radDatum = {}
            # The usernames refer to zabbix userids. but sometimes have extra
            # alpha characters, because of multiple links.
            radDatum['username'] = radRecord.username
            radDatum['startDate'] = radRecord.acctstarttime
            # We use the mac as an index, trust me this is clearer.
            mac = Mac(radRecord.callingstationid)
            radDatum['mac'] = mac
            # All lookups will be based on the actual zabbix id, which is an 
            # integer, so we want to index by that.
            try: 
                zabId = int(''.join(c for c in radRecord.username if \
                c.isdigit()))
            except ValueError:
                # Means there are no numbers in the username; somebody fucked 
                # up and didn't set it.
                #print(radRecord)
                zabId = 0
            # Then we save that into the dict
            radDatum['zabid'] = zabId
            # Which we append to the list.
            # Now, this data is from an accounting table, so it doesn't purge
            # old info. Therefore, we take only the most recent instance.
            try:
                if radData[mac]['startDate'] < radDatum['startDate']:
                    #print(type(radDatum))
                    radData[mac] = radDatum
            except KeyError:
                # Means that it's the first instance of the record.
                radData[mac] = radDatum

        # Now, we don't actually want the timestamps, and the ingestion system
        # doesn't take dicts, so...
        radList = []
        for radDatum in radData.items():
                r = radDatum[1]
                del r['startDate']
                radList.append(r)
        return radList
