#!/usr/local/bin/python3

# For giving easy access to the data

import bottle

from Config import config
from NetDB import NetDB
from Mac import Mac
from Ip import Ip
import WebInterface

ndabottle = bottle.Bottle()
netdb = NetDB(config['databases']['netdata'])

# Index page, full of search bars.
@ndabottle.route('/')
def index():
    with open('webserver/index.html', 'r') as indexhtml:
        return indexhtml.read()

# ARP lookups
@ndabottle.post('/arp-mac')
def macToIp():
    # Exactly what it says on the box. Based on the DB's arp table.
    # Typecasting is for input validation.
    print('Attempted ARP lookup for:', bottle.request.forms.get('mac'))
    try:
        mac = Mac(bottle.request.forms.get('mac'))
    except ValueError:
        return 'Invalid MAC address entered.'
    # Gives a list, because there can technically be multiple answers. FML.
    answers = netdb.arpLookup(mac=mac)
    if len(answers) == 0:
        return 'No matches for that MAC address.'
    table = WebInterface.listToTable(['IP'], answers)
    return WebInterface.pageWrap(table)
@ndabottle.post('/arp-ip')
def ipToMac():
    # Same as the last function, but backwards
    print('Attempted ARP lookup for:', bottle.request.forms.get('ip'))
    try:
        ip = Ip(bottle.request.forms.get('ip'))
    except ValueError:
        return 'Invalid IP address entered.'
    answers = netdb.arpLookup(ip=ip)
    if len(answers) == 0:
        return 'No matches for that IP address.'
    table = WebInterface.listToTable(['MAC'], answers)
    return WebInterface.pageWrap(table)
@ndabottle.get('/zabbix-arp-mismatches')
def getMismatches():
    print('Getting zabbix-arp')
    

ndabottle.run(host='127.0.0.1', port=6001)

