# Data formatting functions to give nice strings back to the webserver.

from NetworkPrimitives import Ip, Mac

def pageWrap(content):
    # Gives back an HTML body with standard head data.
    with open('webserver/htmlbase.html', 'r') as htmlbase:
        html = htmlbase.read()
    html = html.replace('%%%CONTENT%%%', content)
    return html

def mainPage():
    with open('webserver/htmlbase.html', 'r') as htmlbase:
        html = htmlbase.read()
    with open('webserver/index.html') as contentFile:
        content = contentFile.read()
    return html.replace('%%%CONTENT%%%', content)

def hostLookup(query, netdb):
    # Takes a string, determines what it is, and then returns basic 
    # information about the connection.
    try:
        # If it's a Mac...
        query = Mac(query)
    except ValueError:
        try:
            # Or an Ip...
            query = Ip(query)
        except ValueError:
            # Otherwise, assume customer name.
            pass 
    hosts = netdb.hostLookup(query)
    for host in hosts:
        # Make the IPs hyperlinks 'cause why not.
        host['ip'] = hyperLinkString(host['ip'])
    return pageWrap(listToTable(['hostname', 'ip', 'mac'], hosts))

def arpLookup(query, netdb):
    # More limited version of hostLookup, just checks for ARP.
    try:
        # If it's a Mac...
        query = Mac(query)
    except ValueError:
        try:
            # Or an Ip...
            query = Ip(query)
        except ValueError:
            # Otherwise, assume customer name.
            return 'Please enter an IP or MAC address.'
    hosts = netdb.arpLookup(query)
    for host in hosts:
        # Make the IPs hyperlinks 'cause why not.
        host['ip'] = hyperLinkString(host['ip'])
    return pageWrap(listToTable(['ip', 'mac'], hosts))

def routeLookup(query, netdb):
    try:
        # Validate...
        query = Ip(query)
    except ValueError:
        return 'IP addresses only.'
    routes = netdb.findValidRoutes(query)
    return pageWrap(listToTable(['destination', 'netmask', 'nexthop', 
        'router', 'nexthopmac'], routes))

def getDisabledHosts(zabdb):
    hosts = zabdb.getDisabledHosts()
    print('Reporting', len(hosts), 'disabled hosts.')
    return pageWrap(listToTable(['hostname'], hosts))

def listToTable(columns, data):
    # Make an HTML table out of a bunch of items. 
    # Columns should be a list of strings. 
    html = '<table>'
    html += '<tr>'
    for column in columns:
        html += '<td>' + column + '</td>'
    html += '</tr>\n'

    for datum in data:
        html += '<tr>'
        # If it's a string or string-descendant, it's single-column.
        if type(datum) == str or issubclass(type(datum),str):
            html += '<td>' + datum + '</td>'
        # If it's a list, multiple columns.
        elif type(datum) == list or issubclass(type(datum),list):
            for item in datum:
                html += '<td>' + item + '</td>'
        # If it's a dict, do matching to the column names.
        elif type(datum) == dict or issubclass(type(datum),dict):
            for i in range(len(columns)):
                html += '<td>' + str(datum[columns[i]]) + '</td>'
        html += '</tr>\n'
    html += '</table>'
    return html

def hyperLinkString(string):
    return '<a href="http://'+string+'">'+string+'</a>'
