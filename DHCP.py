# Pulls data in from a dhcpd.leases file, compares to git readable information
# about what is assigned.

from functions import getRemoteFile
import TimeStamps
from Config import config
import datetime
import os

def getLeases():
    now = datetime.datetime.now()
    leasePath = getRemoteFile(config['dhcp']['remote_string'])
    leases = set()
    with open(leasePath) as leaseFile:
        leaseFileLines = leaseFile.read().split('\n')
        for line in leaseFileLines:
            line = line.strip() # Clear whitespace.
            if line.startswith('lease '):
                ip = line.split(' ')[1].strip()
            elif line.startswith('ends '):
                # Check that it ends in the future.
                expires = TimeStamps.convertDate(line.split(' ')[2], line.split(' ')[3])
                try:
                    if expires > now:
                        leases.add(ip)
                except TypeError:
                    # Means that convertDate got bad data
                    print('This line didn\'t work:')
                    print(line)
    return leases
                    
if __name__ == '__main__':
    #print(getLeases())
    getLeases()
