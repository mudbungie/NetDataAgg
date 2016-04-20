# Sometimes, you need just a function. 

from Host import Host

def initHost(ip):
    #print('Scanning', ip)
    host = Host(ip)
    host.getInterfaces()
    if host.online == False:
        #print('Host with ip', ip, 'offline!')
        print(ip)
    host.hasBridge()
    return host
