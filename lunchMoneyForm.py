#! /usr/bin/python26

from allResStr import updated
from string import Template
from rotCashUpdate import rotCashUpdate
################################################################################
### CGI Setup
################################################################################
import cgi
import cgitb
cgitb.enable()
print 'Content-Type: text/html\r\n\r\n'
################################################################################
### Globals & Setup
################################################################################
try: version = os.path.basename(__file__)
except: version = 'lunchMoneyForm.py'
htmlTemplate = 'lunchFormTemplate.html'
################################################################################
### Output to html (or print to stdout)
################################################################################
templateVars = dict(version=version, rotCashUpdate=rotCashUpdate,
                    updated=updated,
                    )
with open(htmlTemplate, 'r') as temp:
    htmlTemp = temp.read()
    finalHTML = Template(htmlTemp).safe_substitute(templateVars)
    print finalHTML

