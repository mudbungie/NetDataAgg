# Pulls data in from a dhcpd.leases file, compares to git readable information
# about what is assigned.

from functions import getRemoteFile
import TimeStamps
from Config import config
import time
import os

# Pulls and scans a dhcpd.leases file, returns a dictionary indexed by IP,
# with each element being a list in the format of [mac, starts, ends]
def getLeases(remote_string):
    now = time.time()
    # Pull the remote file. Function returns the destination path.
    leasePath = getRemoteFile(remote_string)
    #leasePath = getRemoteFile(config['dhcp']['remote_string'])
    leases = {}
    with open(leasePath) as leaseFile:
        leaseFileLines = leaseFile.read().split('\n')
        for line in leaseFileLines:
            line = line.strip() # Clear whitespace.
            if '{' in line:
                # If there is an open brace, clear everything.
                ip, mac, start, ends = False, False, False, False
            if line.startswith('lease '):
                ip = line.split(' ')[1].strip()
            elif line.startswith('hardware ethernet'):
                mac = line.split(' ')[-1].rstrip(';')
            elif line.startswith('starts'):
                starts = TimeStamps.strToInt(line)
            elif line.startswith('ends '):
                ends = TimeStamps.strToInt(line)
            if line.startswith('abandoned'):
                pass # Let it loop again. This can be ignored.
            elif '}' in line:
                if ip and mac and ends:
                    # Take only current 
                    if ends > now:
                        if ip in leases.keys():
                            # Something is wrong. It shouldn't appear twice.
                            print('Conflict found in valid leases:')
                            print('New data:', ip, mac, starts, ends)
                            print('Old data:', ip, leases[ip])
                        else:
                            leases[ip] = {'ip':ip, 'mac':mac, 
                                'starts':starts,'ends':ends}
                else:
                    print('bad data found for', ip, mac, starts, ends)
    # Convert to a list, because that's what the ingestor takes.
    leases = list(leases.values())
    return leases
                    
if __name__ == '__main__':
    #print(getLeases())
    getLeases()
