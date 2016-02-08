#! /usr/bin/python26

from allResStr import block1split1
from allResStr import block1split23
from allResStr import updated
from string import Template
# import json
################################################################################
### CGI Setup
################################################################################
import cgi
import cgitb
cgitb.enable()
print 'Content-Type: text/html\r\n\r\n'
# print str(updated)
################################################################################
### Globals & Setup
################################################################################
try: version = os.path.basename(__file__)
except: version = 'updater.py'
htmlTemplate = 'updaterTemplate.html'
title = 'Updater'
subtitle = 'blockParse Input Form'
frameTemplate = 'elNinoFrame.html'
################################################################################
### Output to html (or print to stdout)
################################################################################
templateVars = dict(updated=updated,
                    block1split23=block1split23, block1split1=block1split1)
main = ''
with open(htmlTemplate, 'r') as temp:
    htmlTemp = temp.read()
    main = Template(htmlTemp).safe_substitute(templateVars)

templateVars = dict(version=version, title=title, subtitle=subtitle, main=main)

with open(frameTemplate, 'r') as temp:
    htmlTemp = temp.read()
    finalHTML = Template(htmlTemp).safe_substitute(templateVars)
    print finalHTML

