# Sometimes, you need just a function. 

from Host import Host
import unicodedata
import subprocess
import os
import threading
import time
from queue import Queue

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

# I don't know why this isn't how the standard libraries are written anyhow.
# Arguments must be a list of tuples. Returns a list of returned values.
def parallelize(function, arguments, limit=0):
	# Only belongs in this namespace.
	def task_wrapper(q, function, arg):
		q.put(function(*arg))

	q = Queue()
	threads = []
	for arg in arguments:
		time.sleep(0.1) # Prevent thrashing.
		t = threading.Thread(target=task_wrapper, args=(q, function, arg))
		t.start()
		threads.append(t)
	for thread in threads:
		thread.join() # Prevents the execution from advancing until they are all done. 

	return [q.get() for _ in range(len(arguments))]
