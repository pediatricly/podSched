#! /usr/bin/python26

from allResStr import updated
from string import Template
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
except: version = 'confForm.py'
title = 'Conference Attendance'
subtitle = 'Input Form'
frameTemplate = 'elNinoFrame.html'
htmlTemplate = 'confFormTemplate.html'
filesInF = 'filesIn.txt'
with open(filesInF, 'rb') as fileF:
    filesIn = fileF.read()
################################################################################
### Output to html (or print to stdout)
################################################################################

templateVars = dict(updated=updated, filesIn=filesIn, filesInF=filesInF,
                    )
main = ''
with open(htmlTemplate, 'r') as temp:
    htmlTemp = temp.read()
    main = Template(htmlTemp).safe_substitute(templateVars)

templateVars = dict(version=version, title=title, subtitle=subtitle, main=main
                    )
with open(frameTemplate, 'r') as temp:
    htmlTemp = temp.read()
    finalHTML = Template(htmlTemp).safe_substitute(templateVars)
    print finalHTML

