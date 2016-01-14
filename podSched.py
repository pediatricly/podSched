#! /usr/bin/python

'''
Build plan:
    - list of names to AmionLookup
    - score looker-upper

    Ready for this step:
    - date iteration - write a loop that goes through the Amion process &
    appends output to allDays list. Updates the request url at end of loop to
    feedback at the top.
    Maybe a while loop that runs while date < endDate
    Will actually need to have 2 separate request commands. First gets today's
    sched (which can probably throw away) & finds the url for tomorrow.
    That tomorrow url is what gets fed into the start of the loop.
    - vacation adjuster
    - rank & output

11jan16: It all works!
'''

#===============================================================================
import requests
import re
import csv
import os.path
import urllib
import string
import datetime as DT
###################################################################
### Define Globals Before Main try block
###################################################################
try: version = os.path.basename(__file__)
except: version = 'podSched1'


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

csvIn = 'rotationsQual.csv'
csvOut = 'candidates.csv'
#################################################################################
endDate = DT.date(2016,3,31)
startDate = DT.date.today() # Default to search from today, can make raw-input
weekendsOK = 0
AmionNames = ['Sun-V', 'Emmott-M', 'Steinberg-E']
candidates = 20
vacationInput = '(5/9,5/12) (1/30,2/14) (1/30,2/14)' # Will want to make this raw_input

###### Basic Date Calculations ##################################################
today = DT.date.today()
fallYear = 2013
springYear = 2014
if today.month > 6:
    fallYear = int(today.year)
    springYear = fallYear + 1
else:
    springYear = int(today.year)
    fallYear = springYear -1
tracker = startDate
days = (endDate - startDate)
increment = DT.timedelta(days=1)


#################################################################################
#####   Scraper Module
##### Look up the schedule in Amion and put rotations in a list
#################################################################################

def amionLookup(AmName, htmli):
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
        outList.append(nameDict)

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

    # Sample output:
    # ['2016-01-10', 'Sun, Jan 10, 2016', [{'shifts': ['UCW3-Day'], 'AmionName':
    # 'Sun-V'}, {'shifts': ['Not Found'], 'AmionName': 'Wu-L'}]]

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
baseUrl = "http://amion.com/cgi-bin/ocs"
AmionLogin = {"login" : "ucsfpeds"}
req0 = requests.post(baseUrl, data=AmionLogin)
# print(r.text) # This is outputting the html of the actual schedule landing page

html = req0.content # And this stores that html as a string
nextDay = '<a href=".(\S+?)"><IMG SRC="../oci/frame_rt.gif" WIDTH=15 HEIGHT=14 BORDER=0 TITLE="Next day">'

# This finds suffix of Next Day link from Amion landing page. Returns a list,
# hopefully len=1, so stores index 0 to pass into the while loop:
nextLink = re.findall(nextDay, html, re.M)[0]

#################################################################################
### Loop through Amion lookups day-by-day from tomorrow till endDate
#################################################################################
while tracker < endDate:
    reqI = requests.get(baseUrl + nextLink)
    htmlI = reqI.content
    nextLink = re.findall(nextDay, htmlI, re.M)[0] # Find the next day link again for iteration
    lookUp = amionLookup(AmionNames, htmlI) # Lookup date & shift given AmionNames

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

for day in allDays:
    print allDays[day]['postCall']
######### End Loop ##############################################################

# print allDays
# {'2016-01-10': {'dayScore': -1, 'data': [{'shifts': ['UCW3-Day'], 'score': -1,
# 'AmionName': 'Sun-V', 'missing': 0}, {'shifts': ['Not Found'], 'score': 0,
# 'AmionName': 'Wu-L', 'missing': 1}]}}

# In case you need it for offline work:
# allDaysSample = {'2016-01-13': {'dayScore': -1, 'data': [{'shifts': ['ORANGE3-Day'], 'score': -1, 'AmionName': 'Sun-V', 'missing': 0}, {'shifts': ['Not Found'], 'score': 0, 'AmionName': 'Wu-L', 'missing': 1}]}, '2016-01-12': {'dayScore': -1, 'data': [{'shifts': ['ORANGE3-Day'], 'score': -1, 'AmionName': 'Sun-V', 'missing': 0}, {'shifts': ['Not Found'], 'score': 0, 'AmionName': 'Wu-L', 'missing': 1}]}, '2016-01-15': {'dayScore': -2, 'data': [{'shifts': ['UCW3-Nite'], 'score': -2, 'AmionName': 'Sun-V', 'missing': 0}, {'shifts': ['Not Found'], 'score': 0, 'AmionName': 'Wu-L', 'missing': 1}]}, '2016-01-14': {'dayScore': -1, 'data': [{'shifts': ['ORANGE3-Day'], 'score': -1, 'AmionName': 'Sun-V', 'missing': 0}, {'shifts': ['Not Found'], 'score': 0, 'AmionName': 'Wu-L', 'missing': 1}]}}

#################################################################################
### Count & score the next day for post-call residents
#################################################################################
for day in allDays:
    postCallDay = 0
    postDay = day + increment
    try:
        for i in range(len(AmionNames)):
            if allDays[day][dataN][i][nightN] == 1:
                postCallDay += 1
                print allDays[day][dataN][i]['shifts']
                print postDay
        if postCallDay > 0:
            print postCallDay
            allDays[postDay][dayScoreN] += (scoreDict[postCallN] * postCallDay)
            allDays[postDay][postCallN] = postCallDay
    except KeyError: pass
#################################################################################
### Score impossible for vacation days
#################################################################################

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

#################################################################################
### Rank by score, write to csv
#################################################################################
fh = open(csvOut, 'wb')
csvwriter = csv.writer(fh, quotechar=' ')
outHeaders = ['date', 'dayOfWeek', dayScoreN, postCallN]
for res in AmionNames: outHeaders.append(res)
csvwriter.writerow(outHeaders)
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
                    shiftStr += shift
                row.append(shiftStr)
            print row
            csvwriter.writerow(row)
        counter +=1
fh.close()

'''
allDaysSample[day][dayScoreN] returns the score
'''









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

