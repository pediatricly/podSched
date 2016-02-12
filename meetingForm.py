#! /usr/bin/python26

from allResStr import updated
from allResStr import allRes as allRes # Local stored dict of whole block sched
from string import Template
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
except: version = 'meetingForm.py'
title = 'Meeting Planner'
subtitle = 'Input Form'
frameTemplate = 'elNinoFrame.html'
htmlTemplate = 'meetingFormTemplate.html'


# Put a loop here to read allRes and output checkboxes for AmionNames by pgy
# call fields namesIn
checkboxes = {1: [], 2: [], 3: []}
htmlStr = '<input type="checkbox" name="namesIn" value="%s">'
for res in sorted(allRes):
    if '-' in res:
        boxStr = '<label>%s <input type="checkbox" name="namesIn" value="%s"> </label>|   ' % (res, res)
        checkboxes[allRes[res]['pgy']].append(boxStr)

AmNamesForm = ''
for box in checkboxes:
    AmNamesForm += '<br><br>R%ss: <br>' % box
    for i, res in enumerate(checkboxes[box]):
        AmNamesForm += res
        if i >= 4 and i % 4 == 0: AmNamesForm += '<br>'

################################################################################
### Output to html (or print to stdout)
################################################################################

templateVars = dict(updated=updated, AmNamesForm=AmNamesForm
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

