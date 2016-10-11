# Sometimes, you need just a function. 

from Host import Host
import unicodedata
import subprocess
import os

def initHost(ip):
    #print('Scanning', ip)
    host = Host(ip)
    host.getInterfaces()
    if host.online == False:
        #print('Host with ip', ip, 'offline!')
        print(ip)
    host.hasBridge()
    return host

def sanitizeString(dirty):
    try:
        clean = unicodedata.normalize('NFKD', dirty).encode('ascii', 'ignore')\
            .decode('ascii')
    except TypeError:
        if dirty == None:
            return dirty
        else:
            raise
    return clean

# Uses scp, presumes that an SSH key is installed.
def getRemoteFile(remote_string):
    destination = os.path.dirname(os.path.abspath(__file__)) + '/incoming/'

    try:
        os.mkdir(destination)
    except FileExistsError:
        pass
    command = ['scp', remote_string, destination]
    p = subprocess.call(command)
    if '/' in remote_string:
        filename = remote_string.split('/')[-1]
    else:
        filename = remote_string.split(':')[-1]
    # I figure the most useful thing from this function is the path to the file.
    return destination + filename

