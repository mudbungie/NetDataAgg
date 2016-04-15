# Class for a network object. 

from Ip import Ip
from Mac import Mac
from Interface import Interface
from Config import config
import easysnmp
import requests
import json

# Disable security warnings.
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Host:
    def __init__(self, ip):
        # A host needs at least an IP address.
        # Which I'll pass two a string subclass for validation.
        self.ip = Ip(ip)
        self.interfaces = []
    
    def __str__(self):
        return self.ip

    def snmpInit(self):
        self.session = easysnmp.Session(hostname=self.ip,
            community=config['snmp']['radiocommunity'], version=1)

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

    def getInterfaces(self):
        # Use SNMP to retrieve info about the interfaces.
        #mib = 'iso.org.dod.internet.mgmt.mib_2.interfaces.ifTable.ifEntry.ifPhysAddress'
        macmib = 'ifPhysAddress'
        snmpmacs = self.snmpwalk(macmib)
        descmib = 'ifDescr'
        ifnames = self.snmpwalk(descmib)
        if snmpmacs:
            self.online = True
            for snmpmac in snmpmacs:
                # Filter out empty responses.
                if len(snmpmac.value) > 0:
                    mac = Mac(snmpmac.value, encoding='utf-16')
                    interface = (Interface(mac))
                    for ifname in ifnames:
                        # Get the associated name of the interface.
                        if ifname.oid_index == snmpmac.oid_index:
                            label = ifname.value
                    interface.label = label
                    #print(interface, interface.label)
                    self.interfaces.append(interface)
        else:
            self.online = False
    
    def getStatusPage(self):
        # Take the 
        with requests.Session() as websess:
            payload = { 'username':config['radios']['unames'],
                        'password':config['radios']['pwords']}
            loginurl = 'https://' + self.ip + '/login.cgi?url=/status.cgi'
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
                print(self.ip)
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

        except requests.exceptions.ConnectionError:
            self.online = False

    def hasMac(self, mac):
        # Simple. Just find out if this host has a given hwaddr.
        matchingInterfaces = []
        for interface in self.interfaces:
            if interface.mac == mac:
                matchingInterfaces.append(interface.label)
        if len(matchingInterfaces) > 0:
            #print('Matching interface found on', ', '.join(matchingInterfaces))
            return True
        #print('No match')
        return False

    def hasBridge(self):
        # Pull the interface list if it's not already done.
        if len(self.interfaces) != 0:
            self.getInterfaces()
        print(len(self.interfaces))
        # We'll be comparing different classes of interfaces.
        ath = []
        eth = []
        br = []
        for interface in self.interfaces:
            # Split out the aths and eths.
            if interface.label[0:3] == 'ath':
                ath.append(interface.mac)
            elif interface.label[0:3] == 'eth':
                eth.append(interface.mac)
            elif interface.label[0:2] == 'br':
                br.append[interface.mac]
        # Oddness for efficiency.
        print('ath',ath)
        print('eth',eth)
        print('br',br)
        intersection = [mac for mac in ath if mac in set(eth + br)]
        if len(intersection) > 0:
            # If there are any matches, send the bridged MAC address.
            return intersection[0]
        else:
            return False

# testing
if __name__ == '__main__':
    a = Host('172.24.5.26')
    a.snmpInit('godaddy')
    a.getInterfaces()
