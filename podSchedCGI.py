#! /usr/bin/python26

'''
Marks:
    a - globals
    b - scraper module
    c - csv read in
    d - loop through Amion scrape-crawl
    e - score
    f - rank and output

Basic Flow:
    - list of names to AmionLookup
    - score looker-upper
    - date iteration - loop through the Amion process & appends output to
    allDays list. Updates the request url at end of loop to
    feedback at the top.
    while loop that runs while date < endDate
    Will actually need to have 2 separate request commands. First gets today's
    sched (which can probably throw away) & finds the url for tomorrow.
    That tomorrow url is what gets fed into the start of the loop.
    - vacation adjuster
    - rank & output

11jan16: It all works!
19jan16: Just made way more awesome using the allRes dict. This is a locally
stored dict of the year's entire Amion schedule (cf blockParse.py). Using this,
I updated AmionLookup to grab the block from that dict as well & output it to
candidates.csv
10feb16: Updated to score for vacation days using blockParse / allRes data
instead of having to input those dates manually.
'''

#===============================================================================
import requests
import re
import csv
import os.path
import urllib
import string
import datetime as DT
from allResStr import allRes as allRes # Local stored dict of whole block sched
from allResStr import updated
###################################################################
### Define Globals Before Main try block
###################################################################
try: version = os.path.basename(__file__)
except: version = 'podSchedCGI.py'

fieldnames = ['AmionRot', 'cleanRotName', 'Milestone Map Label']
residentD = {}
rotationsDict = {}

headers = []
rotsQualDict = {}
scoreDict = {
    'good' : 1,
    'ok' : 0,
    'bad' : -1,
    'impossible' : -2,
    'postCall' : -1
}
allDays = {}
dayScoreN = 'dayScore'
dataN = 'data'
score = 'score'
nightN = 'night'
postCallN = 'postCall'
vacation = 'VAC'

csvIn = 'rotationsQual.csv'
csvOut = 'candidates.csv'
baseUrl = "http://amion.com/cgi-bin/ocs"
AmionLogin = {"login" : "ucsfpeds"}
dateTar = '&nbsp;(\w\w\w, \w\w\w \d\d, \d\d\d\d) &nbsp;'
nextDay = '<a href=".(\S+?)"><IMG SRC="../oci/frame_rt.gif" WIDTH=15 HEIGHT=14 BORDER=0 TITLE="Next day">'
testInput = 'http://pediatricly.com/cgi-bin/elNino/podSchedCGI.py?'
### HTML Setup Here ############################
title = 'Meeting Planner'
subtitle = 'Results Form'
frameTemplate = 'elNinoFrame.html'
htmlTemplate = 'podSchedTemplate.html'
#################################################################################
### CGI Inputs and Setup All Go Here ############################
#################################################################################
message = ''
errMessage = ''
AmionNames = []

try:
    import cgi; import cgitb
    # cgitb.enable()
    form = cgi.FieldStorage()
except:
    errMessage += 'Whoa! Something went wrong with the CGI initialization.'
print 'Content-Type: text/html\r\n\r\n'

try:
    namesIn = form.getlist('namesIn')
    message += 'Used these input Amion names: '
    for AmName in namesIn:
        AmionNames.append(cgi.escape(AmName))
        message += AmName + ', '
    message = message[:-2] + '<br>'
except: errMessage += 'Whoa! Something went wrong with the Amion Names input.'

try:
    startDateIn = form.getfirst('startDate', '')
    startDateIn = cgi.escape(startDateIn)
    # HTML form brings the whole ISO date format. This strips to just the date.
    startDateIn = startDateIn[:10]
    startDateIn = DT.datetime.strptime(startDateIn, '%Y-%m-%d')
    startDate = startDateIn.date()
    message += 'Used the entered startDate, %s<br>' % startDate
except:
    startDate = DT.date.today() # Default to search from today
    message += 'Used the default startDate, %s<br>' % startDate

try:
    endDateIn = form.getfirst('endDate', '')
    endDateIn = cgi.escape(endDateIn)
    # HTML form brings the whole ISO date format. This strips to just the date.
    endDateIn = endDateIn[:10]
    endDateIn = DT.datetime.strptime(endDateIn, '%Y-%m-%d')
    endDate = endDateIn.date()
    message += 'Used the entered endDate, %s<br>' % endDate
except:
    endDateIn = DT.datetime.now() + DT.timedelta(days=60) # Default to search for 2 mo
    endDate = endDateIn.date()
    message += 'Used the default endDate, %s<br>' % endDate

try:
    weekendsIn = form.getfirst('weekends')
    weekendsIn = cgi.escape(weekendsIn)
    if weekendsIn == '1':
        weekendsOK = 1
        message += 'Used the entered weekends parameter, %s (0=ignore weekends)<br>' % weekendsOK
    else: weekendsOK = 0
except:
    weekendsOK = 0
    message += 'Used the default weekends parameter, 0 (0=ignore weekends)<br>'

try:
    candIn = form.getfirst('candidates', '')
    candidates = int(cgi.escape(candIn))
    message += 'Used the entered candidates, %s<br>' % candidates
except:
    candidates = 15
    message += 'Used the default candidates, %s<br>' % candidates
###### END CGI Setup ##################################################
# print message
# print errMessage

###### Basic Date Calculations ##################################################
today = DT.date.today()
fallYear = 2013 # Just initializes the variable, reset to the current year below
springYear = 2014 # Just initializes the variable, reset to the current year below
if today.month > 6:
    fallYear = int(today.year)
    springYear = fallYear + 1
else:
    springYear = int(today.year)
    fallYear = springYear -1
tracker = startDate
# days = (endDate - startDate)
increment = DT.timedelta(days=1)


#################################################################################
#####   Scraper Module
##### Look up the schedule in Amion and put rotations in a list
#################################################################################

def amionLookup(AmName, htmli, resDict):
    fullTable1 = re.findall("^<TR><td>([\w\s&-;]+?)<.*<nobr>(.*)</b></a>", htmli, re.M)
    fullTable2 = re.findall("^<TR class=grbg><td>([\w\s&-;]+?)<.*<nobr>(.*)</b></a>", htmli, re.M)
    fullTable3 = re.findall("^<TR><td></font><font color=#\w\w\w\w\w\w>([\w\s&-;]+?)<.*<nobr>(.*)</b></a>", htmli, re.M)

    listofTables = [fullTable1, fullTable2, fullTable3]
    resRotList =  []
    for subTable in listofTables:
        for rotation, resident in subTable:
            rotation = re.sub(r'&nbsp;', '', rotation)
            resident = re.sub(r'[=\*\+]', '', resident)
            tempList = [rotation, resident]
            resRotList.append(tempList)
    # [['KWInt-Long', 'Steinberg-E'], ['RedBMT-Day', 'Emmott-M']...]

    # This section re finds the date from the Amion html then parses it into a
    # Python date so it sorts/compares reliably.
    dTar = '\w\w\w, \w\w\w \d+, \d\d\d\d'
    dStr = re.findall(dTar, htmli, re.M)
    dParts = str(dStr[0]).split()
    dPartsClean = []
    for part in dParts:
        out = part.translate(string.maketrans("",""), string.punctuation)
        try: out = int(out)
        except: pass
        dPartsClean.append(out)
    monLetters = dPartsClean[1]
    pyDate = DT.date(dPartsClean[3], DT.datetime.strptime(monLetters, '%b').month,
                    dPartsClean[2])
    isoDate = pyDate.isoformat()

    outList = [] # [{'shifts': ['UCW3-Day'], 'AmionName': 'Sun-V'}, {'shifts': ['Not Found']...}]
    for name in AmName:
        shifts = [] # Shifts as a list for rare cases when names twice in 1 day
        currRot = 'Not Found'
        nameDict = {'AmionName' : name}
        for resRotPair in resRotList:
            if name == resRotPair[1]:
                currRot = resRotPair[0] # Update currRot to the shift if found
                shifts.append(currRot)
        if len(shifts) == 0: shifts.append(currRot) # 1 copy of default if not found
        nameDict['shifts'] = shifts # {'shifts': ['UCW3-Day'], 'AmionName': 'Sun-V'}, {'shifts'

        block = ''
        blockSched = resDict[name]['schedule']
        for rotation in blockSched:
            if isoDate >= rotation['startDate'] and isoDate <= rotation['stopDate']:
                block = rotation['rotation']
        nameDict['block'] = block

        outList.append(nameDict)

    # Sample output:
    # ['2016-01-10', 'Sun, Jan 10, 2016', [{'shifts': ['UCW3-Day'], 'AmionName':
    # 'Sun-V', 'block': 'ORANGE3'}, {'shifts': ['Not Found'], 'AmionName': 'Wu-L'}]]

    return {pyDate : outList}
###################################################################
### Read the CSV list from active dir
### This should contain shiftName, cleanRotName, quality, night
###################################################################

fh = open(csvIn, 'rb')
csvreader = csv.reader(fh, quotechar=' ')
for i, row in enumerate(csvreader):
    if i == 0: headers = row
if headers[4] == '': headers.pop()
shiftName = headers[0]
cleanRotName = headers[1]
quality = headers[2]
night = headers[3]
fh.close()

fh = open(csvIn, 'rb')
csvreader = csv.reader(fh, quotechar=' ')
for i, row in enumerate(csvreader):
    if i != 0:
        qualI = row[2]
        rotsQualDict[row[0]] = {quality : qualI, night : row[3],
                                score: scoreDict[qualI]}
fh.close()
# print rotsQualDict
# rotsQualDict is a dict of dicts with keys = shift names
# {'Pacific Sr-Nite': {'score': -2, 'quality': 'impossible', 'night': '1'},
# PURPLE1-Day': {'score': -1, 'quality': 'bad', 'night': ''},}

#################################################################################
### Setup Amion loop by going to landing page & finding first Next Day link
#################################################################################
req0 = requests.post(baseUrl, data=AmionLogin)
# print(r.text) # This is outputting the html of the actual schedule landing page

html = req0.content # And this stores that html as a string

# This finds suffix of Next Day link from Amion landing page. Returns a list,
# hopefully len=1, so stores index 0 to pass into the while loop:
nextLink = re.findall(nextDay, html, re.M)[0]

#################################################################################
### Loop through Amion lookups day-by-day from tomorrow till endDate
#################################################################################
while tracker < endDate:
    # Skip this loop if before startDate
    if tracker < startDate:
        tracker = tracker + increment # Don't lose. Tracks date, break while loop.
        continue
    else:
        reqI = requests.get(baseUrl + nextLink)
        htmlI = reqI.content
        nextLink = re.findall(nextDay, htmlI, re.M)[0] # Find the next day link again for iteration
        lookUp = amionLookup(AmionNames, htmlI, allRes) # Lookup date & shift given AmionNames

#################################################################################
# This section sets up the data analysis & is what changes for different
# applications of AmionLookup.
# In general, by day, it looks up the shift the database (read from csv above)
# and outputs some dict with data
# Could rewrite just to store the daily data & do the lookup in a separate loop.
# I thought the single loop might be a little fast for big searches.
# Other uses: lookup conference expectations by shift & store by resident / by
# month for conference tracker
        data = lookUp.values()[0]
        dayList = []
        for resident in data:
            shifts = resident['shifts']
            try:
                for shift in shifts:
                    shiftData = rotsQualDict[shift]
                    shiftScore = 0
                    shiftScore += shiftData[score]
                    if shiftData[nightN] == '1': resident[nightN] = 1
                    else: resident[nightN] = 0
                resident[score] = shiftScore
                resident['missing'] = 0
            except KeyError:
                resident[score] = 0
                resident['missing'] = 1
                resident[nightN] = 0
            dayList.append(resident)
        dayScore = 0
        for resident in dayList:
            dayScore += resident[score]
        allDays[lookUp.keys()[0]] = {dayScoreN : dayScore, postCallN : 0, 'data' :dayList}
#################################################################################

        tracker = tracker + increment # Don't lose. Tracks date, break while loop.

# for day in allDays:
    # print allDays[day]
######### End Loop ##############################################################

# print allDays
# {'2016-01-10': {'dayScore': -1, 'data':
    # [{'shifts': ['UCW3-Day'], 'score': -1, 'AmionName': 'Sun-V', 'missing': 0, 'block': 'ORANGE3'},
     # {'shifts': ['Not Found'], 'score': 0, 'AmionName': 'Wu-L', 'missing': 1, 'block': 'DB'}
     # ]
    # }
  # }

# In case you need it for offline work (not updated for block lookup):
# allDaysSample = {'2016-01-13': {'dayScore': -1, 'data': [{'shifts': ['ORANGE3-Day'], 'score': -1, 'AmionName': 'Sun-V', 'missing': 0}, {'shifts': ['Not Found'], 'score': 0, 'AmionName': 'Wu-L', 'missing': 1}]}, '2016-01-12': {'dayScore': -1, 'data': [{'shifts': ['ORANGE3-Day'], 'score': -1, 'AmionName': 'Sun-V', 'missing': 0}, {'shifts': ['Not Found'], 'score': 0, 'AmionName': 'Wu-L', 'missing': 1}]}, '2016-01-15': {'dayScore': -2, 'data': [{'shifts': ['UCW3-Nite'], 'score': -2, 'AmionName': 'Sun-V', 'missing': 0}, {'shifts': ['Not Found'], 'score': 0, 'AmionName': 'Wu-L', 'missing': 1}]}, '2016-01-14': {'dayScore': -1, 'data': [{'shifts': ['ORANGE3-Day'], 'score': -1, 'AmionName': 'Sun-V', 'missing': 0}, {'shifts': ['Not Found'], 'score': 0, 'AmionName': 'Wu-L', 'missing': 1}]}}

#################################################################################
### Count & score the next day for post-call residents
### Also, score impossible when block == 'VAC'
#################################################################################
for day in allDays:
    postCallDay = 0
    postDay = day + increment
    try:
        for i in range(len(AmionNames)):
            if allDays[day][dataN][i][nightN] == 1:
                postCallDay += 1
        if postCallDay > 0:
            allDays[postDay][dayScoreN] += (scoreDict[postCallN] * postCallDay)
            allDays[postDay][postCallN] = postCallDay
    except KeyError: pass

    # Score impossible for vacation days - v2 using the block lookUp
    data = allDays[day]['data'] #List of dicts: [{'missing': 0, 'AmionName': 'Sun-V', 'shifts': ['UCW3-Nite'], 'score': -2, 'night': 1, 'block': 'ORANGE3'},
    # {'missing': 1, 'AmionName': 'Brim-R', 'shifts': ['Not Found'], 'score': 0,
    # 'night': 0, 'block': 'JEOP'},...]
    # Score impossible for vacation days
    for resDict in data:
        if resDict['block'] == vacation:
            allDays[day][dayScoreN] += scoreDict['impossible']

#################################################################################
### Rank by score, write to csv
#################################################################################
candidatesTable = '<tr><th>Rank</th>'
fh = open(csvOut, 'wb')
csvwriter = csv.writer(fh, quotechar=' ')
outHeaders = ['date', 'dayOfWeek', dayScoreN, postCallN]
for res in AmionNames: outHeaders.append(res)
csvwriter.writerow(outHeaders)
for item in outHeaders:
    candidatesTable += '<th>' + item + '</th>'
candidatesTable += '</tr>'
counter = 0
for day in sorted(allDays.items(), key=lambda x: x[1][dayScoreN],
                  reverse=True):
    if counter >= candidates:
        break
    else:
        if weekendsOK == 0 and day[0].weekday() > 4:
                continue
        else:
            row = [day[0].isoformat(), day[0].strftime('%a'), day[1][dayScoreN],
                   day[1][postCallN]]
            for i in range(len(AmionNames)):
                # row.append(day[1]['data'][i]['AmionName'])
                shiftStr = ''
                for shift in day[1]['data'][i]['shifts']:
                    block = day[1]['data'][i]['block'] #Add block to output
                    increment = shift + '/' + block + ' '
                    shiftStr += increment
                row.append(shiftStr)
            # print row
            csvwriter.writerow(row)
            candidatesTable += '<tr><td>' + str(counter + 1) + '</td>'
            for item in row:
                candidatesTable += '<td>' + str(item) + '</td>'
            candidatesTable += '</tr>'
        counter +=1
fh.close()

# allDaysSample[day][dayScoreN] returns the score

# try:
################################################################################
### Output to html (or print to stdout)
################################################################################
if errMessage == '': errMessage = 'No errors - hooray!'
templateVars = dict(message=message, csvIn=csvIn, updated=updated,
                    csvOut=csvOut, errMessage=errMessage,
                    candidates=candidates, candidatesTable=candidatesTable
                    )
main = ''
with open(htmlTemplate, 'r') as temp:
    htmlTemp = temp.read()
    main = string.Template(htmlTemp).safe_substitute(templateVars)
# Careful! Don't copy this to other scripts as this script imports the whole
# string module so this syntax is different from those that from string import
# Template.

templateVars = dict(version=version, title=title, subtitle=subtitle, main=main
                )
with open(frameTemplate, 'r') as temp:
    htmlTemp = temp.read()
    finalHTML = string.Template(htmlTemp).safe_substitute(templateVars)
    print finalHTML

# except:
    # print '<h1>Whoa! Something went wrong with the data output!</h1>'
    # print '<h1>If you are seeing this message, please double check any dates you entered, the output summary below (resident names, etc) and try again. If you still get this error, contact Mike. :(</h1>'




#################################################################################
### Old bits of code
#################################################################################

'''
Archive of working bits for re etc:

# HTML around the date at top of table. Single-digit dates are single char:
</SELECT>
&nbsp;Sun, Jan 10, 2016 &nbsp; &nbsp; &nbsp; <

# Experimental snippets for re to get the Next Day link from Amion
nextLink = 'http://amion.com/cgi-bin/ocs?File=!12dc666chucsf_peds&Page=OnSh&Fsiz=-2&Jdo=1&Sbcid=6'
target = '<a href="./ocs?File=..."><img src="../oci/frame_rt.gif"...title="Next day">'
tar1 = '<a href="(.*)">.*<img.*title="Next day">'
tar2 = 'Next day'
tar3 = '<a href="./ocs?File=!52dc6d6blwaudangbu&Page=OnSh&Fsiz=-2&Jdo=1&Sbcid=6"><IMG SRC="../oci/frame_rt.gif" WIDTH=15 HEIGHT=14 BORDER=0 TITLE="Next day">'
'''

#################################################################################
### Score impossible for vacation days
# This was the old way to score for vacation days before I built blockParse to
# lookup the block schedule (in addition to the daily shift). Vacations were
# lost in that original approach and so vacation dates had to be added manually.
# With blockParse storing the whole Amion block schedule now, it's really easy
# to adjust the score for vacations. This is done above in the same loop that
# scores for post-call. I keep this code here for historical storage.
#################################################################################
'''
Obsolete but a nice exercise in form parsing. This is no longer needed as I
updated podSched to use the allRes / blockParse data to score vacation days
automatically.
vacTupules = []
try:
    vacStartsIn = form.getlist('vacStart')
    vacStopsIn = form.getlist('vacStop')
    assert (len(vacStartsIn) == len(vacStopsIn))
    for i, start in enumerate(vacStartsIn):
        assert (start < vacStopsIn[i])
        startI = cgi.escape(start)
        startI = startI[:10]
        startI = DT.datetime.strptime(startI, '%Y-%m-%d')
        startD = startI.date()

        stopI = cgi.escape(vacStopsIn[i])
        stopI = stopI[:10]
        stopI = DT.datetime.strptime(stopI, '%Y-%m-%d')
        stopD = stopI.date()
        vacTupule = (startD, stopD)
        vacTupules.append(vacTupule)
except:
    errMessage += 'Whoa! Something went wrong with vacation date entry, e.g., not all were entered as start/stop pairs or start date after stop date.<br>'

print vacTupules
print '<br>'
'''

'''
vacationInput = '(5/9,5/12) (1/30,2/14) (1/30,2/14)' # Will want to make this raw_input
vacInputGroups = re.findall('\((.*?)\)', vacationInput, re.M)
vacTupules = []
for vac in vacInputGroups:
    startDate = vac[:vac.find(',')]
    moStart = int(startDate[:startDate.find('/')])
    dayStart = int(startDate[vac.find('/')+1:])
    endDate = vac[vac.find(',')+1:]
    moEnd = int(endDate[:endDate.find('/')])
    dayEnd = int(endDate[endDate.find('/')+1:])
    if moStart > 6: yearStart = fallYear
    else: yearStart = springYear
    if moEnd > 6: yearEnd = fallYear
    else: yearEnd = springYear
    startDate = DT.date(yearStart, moStart, dayStart)
    endDate = DT.date(yearEnd, moEnd, dayEnd)
    dateTupule = (startDate, endDate)
    vacTupules.append(dateTupule)

for vac in vacTupules:
    for day in allDays:
        if day > vac[0] and day <= vac[1]:
            allDays[day][dayScoreN] += -2
'''
