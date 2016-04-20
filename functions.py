# Sometimes, you need just a function. 

from Host import Host

def initHost(ip):
    print('Scanning', ip)
    host = Host(ip)
    host.getInterfaces()
    host.hasBridge()
    return host
