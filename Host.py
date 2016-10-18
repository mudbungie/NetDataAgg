# Class for a network object. 

from NetworkPrimitives import Ip, Mac
from Interface import Interface
from Config import config
import easysnmp
import requests
from requests.exceptions import *
import json

# Disable security warnings.
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Host:
    def __init__(self, ip):
        self.hostinit(ip)

    def hostinit(self, ip):
        # A host needs at least an IP address.
        # Which I'll pass two a string subclass for validation.
        self.ip = Ip(ip)
        self.interfaces = {}
        self.arpNeighbors = {}
    
    def __str__(self):
        return self.ip

    def snmpInit(self):
        self.session = easysnmp.Session(hostname=self.ip,
            community=config['snmp']['radiocommunity'], version=1, timeout=0.5)

    def snmpwalk(self, mib):
        # Walks specified mib
        self.snmpInit()
        try:
            responses = self.session.walk(mib)
            return responses
        except easysnmp.exceptions.EasySNMPNoSuchNameError:
            # Probably means that you're hitting the wrong kind of device.
            return False
        except easysnmp.exceptions.EasySNMPTimeoutError:
            # Either the community string is wrong, or the address is dead.
            return False

    # Set during init
    @property
    def interfaces(self):
        return self.__interfaces
    @interfaces.setter
    def interfaces(self, interfaces):
        self.__interfaces = interfaces

    # Set during init
    @property
    def arpNeighbors(self):
        return self.__arpNeighbors
    @arpNeighbors.setter
    def arpNeighbors(self, arpNeighbors):
        self.__arpNeighbors = arpNeighbors

    # This info is set mostly through zabbix data, though it can be derived
    # from a properly configured host.
    @property
    def hostname(self):
        return self.__hostname
    @hostname.setter
    def hostname(self, hostname):
        self.__hostname = hostname
    @property
    def hostid(self):
        return self.__hostname
    @hostid.setter
    def hostid(self, hostid):
        self.__hostid = hostid


    def getRouter(self):
        routers = (host for host in arpNeighbors.items() if type(host) == Router)

    def getInterfaces(self):
        # Use SNMP to retrieve info about the interfaces.
        #mib = 'iso.org.dod.internet.mgmt.mib_2.interfaces.ifTable.ifEntry.ifPhysAddress'
        macmib = 'ifPhysAddress'
        snmpmacs = self.snmpwalk(macmib)
        descmib = 'ifDescr'
        ifnames = self.snmpwalk(descmib)
        if snmpmacs:
            self.online = True
            #print('ON:', self.ip)
            for snmpmac in snmpmacs:
                # Filter out empty responses.
                if len(snmpmac.value) > 0:
                    mac = Mac(snmpmac.value, encoding='utf-16')
                    print(mac)
                    interface = (Interface(mac))
                    for ifname in ifnames:
                        # Get the associated name of the interface.
                        if ifname.oid_index == snmpmac.oid_index:
                            label = ifname.value
                    interface.label = label
                    #print(interface, interface.label)
                    self.interfaces[mac] = interface
            return self.interfaces
        else:
            self.online = False
            #print('OFF:', self.ip)
            return None

    # Attempts HTTP authentication, using all known credentials.
    def getAuthenticatedSession(self):
        print('Authenticating with', self.ip, end='')
        session = requests.Session()
        url = 'https://' + self.ip + '/login.cgi'
        statusurl = 'https://' + self.ip + '/status.cgi'
        creds = []
        # If this host already has known credentials, use them.
        try:
            creds.append({'uname':self.username,'pword':self.password})
        except AttributeError:
            pass
        creds += config['radios'].values()

        for cred in creds:
            print('.', end='')
            payload = {'username':cred['uname'], 'password':cred['pword']}
            try:
                session.get(url, verify=False, timeout=1)
                session.post(url, data=payload, verify=False, timeout=1)
                p = session.get(statusurl, verify=False, timeout=1)
                # Attempt to JSON-decode the result.
                try:
                    p.json()
                    # If that succeeded, then we've logged in.
                    self.username = payload['username']
                    self.password = payload['password']
                    print()
                    return session
                except ValueError:
                    # Content didn't come back as a JSON. Login failed.
                    try:
                        # Purge any saved credentials.
                        del self.username, self.password
                    except AttributeError:
                        pass
            except (ConnectTimeout, ConnectionError, ReadTimeout):
                print('\nConnection timed out with', self.ip)
                return False
        print('\nLogin failed with responsive host at', self.ip)
        return False
    
    def getStatusPage(self, page=None):
        # Take the 
        with requests.Session() as websess:
            payload = { 'username':config['radios']['unames'],
                        'password':config['radios']['pwords']}
            loginurl = 'https://' + self.ip + '/login.cgi?url=/status.cgi'
            try:
                statusurl = 'https://' + self.ip + page
            except TypeError:
                statusurl = 'https://' + self.ip + '/status.cgi'
            # Open the session, to get a session cookie
            websess.get(loginurl, verify=False, timeout=2)
            # Authenticate, which makes that cookie valid
            p = websess.post(loginurl, data=payload, verify=False, timeout=2)
            # Get ze data
            g = websess.get(statusurl, verify=False, timeout=2)
            # It all comes back as JSON, so parse it.
            try:
                self.status = json.loads(g.text)
            except ValueError:
                # When the json comes back blank
                print('Failed to connect with:', self.ip)
                return None
        return self.status

    def profile(self):
        try:
            status = self.getStatusPage()
            self.online = True
            # This should match what we have in Zabbix.
            self.hostname = status['host']['hostname']
            self.model = status['host']['devmodel']
            self.ap = status['wireless']['essid']
            self.distance = status['wireless']['distance']
            self.rf = {}
            self.rf['signal'] = status['wireless']['signal']
            self.rf['rssi'] = status['wireless']['rssi']
            self.rf['noisef'] = status['wireless']['noisef']
            for entry in status['interfaces']:
                raise
                interface = Interface(Mac(entry['hwaddr']))
                interface.label = entry['ifname']
                interface.speed = entry['status']['speed']

        except ConnectionError:
            self.online = False

    def hasMac(self, mac):
        # Simple. Just find out if this host has a given hwaddr.
        matchingInterfaces = []
        for interface in self.interfaces.values():
            if interface.mac == mac:
                matchingInterfaces.append(interface.label)
        if len(matchingInterfaces) > 0:
            #print('Matching interface found on', ', '.join(matchingInterfaces))
            return True
        #print('No match')
        return False

    def getInfoJson(self, urn):
        session = self.getAuthenticatedSession()
        if not session:
            return False
        try:
            p = session.get('https://' + self.ip + urn)
        except (ConnectionError, ReadTimeout):
            print('Connection failed with previously responsive host', self.ip)
        try:
            return p.json()
        except ValueError:
            # It's not JSON
            print('Non-JSON return in informational page.')
            return False

    # Pull the bridge table, return None or mac address of eth0.
    def hasBridge(self, check=False):
        # Try the cache.
        if not check:
            try:
                return self.bridge
            except AttributeError:
                pass
        # If there is no cache, or if the check is off, query actual radio.
        bridgeTable = self.getInfoJson('/brmacs.cgi?brmacs=y')
        try:
            bridgeTable = bridgeTable['brmacs']
            for interface in bridgeTable:
                if interface['port'] == 'eth0':
                    mac = Mac(interface['hwaddr'])
                    print(self.ip, 'has bridged interface ', mac)
                    return mac
            print('Host has non-eth0 bridges:', bridgeTable)
        except TypeError:
            # Means that the host is not bridged.
            return False

# testing
if __name__ == '__main__':
    a = Host('172.20.36.11') # Host with a bridged radio.
    #a.snmpInit(config['snmp']['radiocommunity'])
    #a.getInterfaces()
    a.hasBridge()
