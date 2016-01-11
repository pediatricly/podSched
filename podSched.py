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

    return {pyDate.isoformat() : outList}
###################################################################
### Read the CSV list from active dir
### This should contain shiftName, cleanRotName, quality, night
###################################################################

headers = []
rotsQualDict = {}
scoreDict = {
    'good' : 1,
    'ok' : 0,
    'bad' : -1,
    'impossible' : -2
}

csvIn = 'rotationsQual.csv'
fh = open(csvIn, 'rb')
csvreader = csv.reader(fh, quotechar=' ')
for i, row in enumerate(csvreader):
    if i == 0: headers = row
if headers[4] == '': headers.pop()
shiftName = headers[0]
cleanRotName = headers[1]
quality = headers[2]
night = headers[3]
score = 'score'
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
endDate = DT.date(2016,2,1)
startDate = DT.date.today()
tracker = startDate
days = (endDate - startDate)
increment = DT.timedelta(days=1)
print startDate + increment
while tracker < endDate:
    print tracker
    tracker = tracker + increment

allDays = {}
# Date range loop starts here:

'''
AmionNames = ['Sun-V', 'Wu-L']
baseUrl = "http://amion.com/cgi-bin/ocs"
AmionLogin = {"login" : "ucsfpeds"}
r = requests.post(baseUrl, data=AmionLogin)
# print(r.text) # This is outputting the html of the actual schedule landing page
html = r.content # And this stores that html as a string


lookUp = amionLookup(AmionNames, html)
data = lookUp.values()[0]
dayList = []
for resident in data:
    shifts = resident['shifts']
    try:
        for shift in shifts:
            shiftData = rotsQualDict[shift]
            shiftScore = 0
            shiftScore += shiftData[score]
        resident[score] = shiftScore
        resident['missing'] = 0
    except KeyError:
        resident[score] = 0
        resident['missing'] = 1
    dayList.append(resident)
dayScore = 0
for resident in dayList:
    dayScore += resident[score]
allDays[lookUp.keys()[0]] = {'dayScore' : dayScore, 'data' :dayList}
#print allDays
# {'2016-01-10': {'dayScore': -1, 'data': [{'shifts': ['UCW3-Day'], 'score': -1,
# 'AmionName': 'Sun-V', 'missing': 0}, {'shifts': ['Not Found'], 'score': 0,
# 'AmionName': 'Wu-L', 'missing': 1}]}}

nextDay = '<a href=".(\S+?)"><IMG SRC="../oci/frame_rt.gif" WIDTH=15 HEIGHT=14 BORDER=0 TITLE="Next day">'
se = re.findall(nextDay, html, re.M)
# print se[0]

# Functional code to iterate the next day:
r2 = requests.get(str(baseUrl + se[0]))
html2 = r2.content
# print html2

AmionName2 = 'Brim-R'
print amionLookup(AmionName2, html2)
'''



# Date range loop ends here















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

