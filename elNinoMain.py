#! /usr/bin/python26

from allResStr import updated
from string import Template
from rotCashUpdate import rotCashUpdate
from allResStr import updated
################################################################################
### CGI Setup
################################################################################
import cgi
import cgitb
# cgitb.enable()
print 'Content-Type: text/html\r\n\r\n'
################################################################################
### Globals & Setup
################################################################################
try: version = os.path.basename(__file__)
except: version = 'elNinoMain.py'
title = 'Main'
subtitle = ''
frameTemplate = 'elNinoFrame.html'
htmlTemplate = 'elNinoMain.html'
################################################################################
### Output to html (or print to stdout)
################################################################################
templateVars = dict(rotCashUpdate=rotCashUpdate,
                    updated=updated,
                    )
main = ''
with open(htmlTemplate, 'r') as temp:
    htmlTemp = temp.read()
    main = Template(htmlTemp).safe_substitute(templateVars)

templateVars = dict(version=version, title=title, subtitle=subtitle, main=main)

with open(frameTemplate, 'r') as temp:
    htmlTemp = temp.read()
    finalHTML = Template(htmlTemp).safe_substitute(templateVars)
    print finalHTML
