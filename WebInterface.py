# Data formatting functions to give nice strings back to the webserver.

def pageWrap(content):
    # Gives back an HTML body with standard head data.
    with open('webserver/htmlbase.html', 'r') as htmlbase:
        html = htmlbase.read()
    html = html.replace('%%%CONTENT%%%', content)
    return html

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
                html += '<td>' + datum[columns[i]] + '</td>'
        html += '</tr>\n'
    html += '</table>'
    return html
