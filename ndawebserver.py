#!/usr/local/bin/python3

# For giving easy access to the data

import bottle

from Config import config
from NetDB import NetDB
from NetworkPrimitives import Mac, Ip
import WebInterface

ndabottle = bottle.Bottle()
netdb = NetDB(config['databases']['netdata'])

# Index page, full of search bars.
@ndabottle.route('/')
def index():
    #with open('webserver/index.html', 'r') as indexhtml:
    #    return indexhtml.read()
    return WebInterface.mainPage()

# ARP lookups
@ndabottle.post('/arp-lookup')
def macToIp():
    # Exactly what it says on the box. Based on the DB's arp table.
    # Typecasting is for input validation.
    query = bottle.request.forms.get('query')
    print('Attempted ARP lookup for:', query)
    return WebInterface.arpLookup(query, netdb)

@ndabottle.get('/zabbix-arp-mismatches')
def getMismatches():
    print('Getting zabbix-arp')

@ndabottle.get('/bad-usernames')
def getBadUsernames():
    answers = netdb.getBadUsernames()
    print('There are', len(answers), 'bad usernames.')
    # Gonna make all the IP addresses into hyperlinks.
    for answer in answers:
        answer['ip'] = '<a href="http://'+answer['ip']+'">'+answer['ip']+'</a>'
    table = WebInterface.listToTable(['hostname', 'username', 'ip'], answers)
    return WebInterface.pageWrap(table)

@ndabottle.post('/host-lookup')
def hostLookupPage():
    pass

ndabottle.run(host='127.0.0.1', port=6001)

