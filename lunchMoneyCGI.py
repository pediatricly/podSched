#! /usr/bin/python26

'''
import allRes

Read in the rotCash data like this:
    {rotation : $/wk,
    rotation2 : $/wk...}

Find the first Monday of the year
Look up the first rotation of the year (ie before that Monday)
increment = TD.timedelta(days=7)
tracker = 1st mon
endDate = 30 Jun 16

data = {
    resName :
          {
            1 : $
            2 : $
            }}

for res in allRes:
    Do the first week calculation
    while tracker < endDate:
        return the rotation on tracker
        return the block on tracker
        rotCash = look up from dict of weekly cash by rotation
        data[res][block] += rotCash

output:
    resName | Block # | Block 2
    name    |  money  | money

Can then add that up by whatever chunks they want
'''
import os.path
import csv
import datetime as DT
from string import Template
from allResStr import allRes
from allResStr import blockStarts23
from allResStr import blockStops23
from allResStr import blockStarts1
from allResStr import blockStops1
from allResStr import updated
from blockUtils import blockLookup
from rotCashUpdate import rotCashUpdate
#########################################################
### Define Globals
##########################################################
try: version = os.path.basename(__file__)
except: version = 'lunchMoneyCGI.py'
# Parameters
firstBlock = 1
lastBlock = 13
classes = [1, 2, 3] # Gives option to break up by class year
rotCashcsv = 'foodCashByWeek.csv' # csv file for the $ by rotation
rotCashUpdateFile = 'rotCashUpdate.py'
# Should look like:
# Rotation, cashByWk (header row, doesn't matter what they're called)
# 'ADOL','24' (rows by rotation, second column needs to be a number. It's read
# as a string but will be converted to float below)
csvOutFile = 'lunchMoneyOut.csv'
errFile = 'lunchMoneyErrors.txt'
title = 'Lunch Money'
subtitle = 'Results Form'
frameTemplate = 'elNinoFrame.html'
htmlTemplate = 'lunchMoneyTemplate.html'
errRots = set()
errRes = set()
###############################################################################
### CGI Setup
################################################################################
import cgi
import cgitb
print 'Content-Type: text/html\r\n\r\n'
cgitb.enable()
form = cgi.FieldStorage() # instantiate only once!

# try:
    # Get the split dates from CGI, default to previous if none entered
firstBlockIn = form.getfirst('firstBlock', '')
lastBlockIn = form.getfirst('lastBlock', '')
classesIn = form.getlist('classI')
# except:
    # print '<h1>Whoa! Something went wrong with the data entry!</h1>'
    # print '<h1>If you are seeing this message, please double the data you entered, the output summary below and try again. If you still get this error, contact Mike. :(</h1>'
    # Avoid script injection escaping the user input

if firstBlockIn != '':
    firstBlock = int(cgi.escape(firstBlockIn))
if lastBlockIn != '':
    lastBlock = int(cgi.escape(lastBlockIn))

if len(classesIn) > 0:
    classes = []
    for classI in classesIn:
        classI = int(cgi.escape(classI))
        classes.append(classI)

############  File Upload ###################################
fileitem = form['foodCashNew']

# Test if the file was uploaded
if fileitem.filename:

    # strip leading path from file name
    # to avoid directory traversal attacks
    fn = os.path.basename(fileitem.filename)
    open(rotCashcsv, 'wb').write(fileitem.file.read())
    message = ('The file "' + fn + '" was uploaded successfully and saved as '
               + rotCashcsv)
    rotCashUpdate = DT.date.today().isoformat()
    with open(rotCashUpdateFile, 'wb') as out:
        out.write("rotCashUpdate = '" + str(rotCashUpdate) + "'\n")
        # print "rotCashUpdate = '" + str(rotCashUpdate) + "'\n"
else:
    message = 'No new cash by rotations file was uploaded - used the version uploaded on %s' % rotCashUpdate

##########################################################
# Setup the basic intake data
increment = DT.timedelta(7) # Counts up money going by weeks
cashData = {}
data = {}
fh = open(rotCashcsv, 'rb')
reader = csv.DictReader(fh)
for row in reader:
    rot = row['Rotation']
    cashWk = row['cashWk']
    cashData[rot] = float(cashWk)
# print cashData
# {'PIC': '0', 'SFO2': '0', 'FLEX': '0', 'E-Ophtho': '24', ...}

blocks = [x for x in range(firstBlock, lastBlock+1)]
headers = ['AmionName']
for block in blocks:
    headers.append(block)

#########################################################
### Main
##########################################################
# This loop just sets up the dict with $ = 0
for res in allRes:
    resDict = {}
    for block in blocks:
        resDict[block] = 0
    if allRes[res]['pgy'] in classes:
        data[res] = resDict
##########################################################
# Open the error file so you can write failures in this loop somewhere
# These failures are usually missing schedule data. Eg. super senior have many
# empty blocks in Amion and that produces an error in the try blocks below
errHandler = open(errFile, 'wb')

# This does the actual rotation lookup & adds up cash going week by week
# (Mondays) through the given date range.
classesStr = ''
for pgyYr in classes:
    classesStr = classesStr + str(pgyYr) + ', '
    if pgyYr == 1:
        starts = blockStarts1
        stops = blockStops1
    else:
        starts = blockStarts23
        stops = blockStops23

    day1 = DT.datetime.strptime(starts[firstBlock], '%Y-%m-%d')
    firstMon = day1 + DT.timedelta(days=(7-day1.weekday()))# - increment
    endDay = DT.datetime.strptime(stops[lastBlock], '%Y-%m-%d')
    # print day1
    # print firstMon

    for res in allRes:
        if allRes[res]['pgy'] == pgyYr:
            if day1.weekday() != 0: #If day1 is not Monday, grab that first partial week as it if were whole, then proceed
                tupule = blockLookup(day1, res, allRes)
                block = tupule[0]
                rotation = tupule[1]
                try: cashRot = cashData[rotation]
                except:
                    cashRot = 0
                    # print tracker
                    # print res, tupule, '<br>'
                    errRes.add(res) # Log error res. Should be super-seniors.
                    errRots.add(rotation) # Log the error rotations. Most are
                try: data[res][block] += cashRot
                except: pass
                tracker = firstMon
            else: #If day1 is Monday, just roll
                tracker = day1
            # tracker = tracker + DT.timedelta(7)
            while (tracker < endDay):
                tupule = blockLookup(tracker, res, allRes)
                # tupule is (blockNum, 'rotation') eg:
                # blockLookup('2016-01-20', 'Sun-V', allRes)
                # returns (8, 'ORANGE3')
                block = tupule[0]
                rotation = tupule[1]
                # These try blocks allow skipping empty cells, eg, partial year
                # super seniors. Prints those output for you to check
                try: cashRot = cashData[rotation]
                except:
                    cashRot = 0
                    # print tracker
                    # print res, tupule, '<br>'
                    errRes.add(res) # Log error res. Should be super-seniors.
                    # If not, it's a big error somewhere.
                    errRots.add(rotation) # Log the error rotations. Most are
                    # blank garbage from super-seniors, but some will be new
                    # rotation names not in the input csv
                try: data[res][block] += cashRot
                except: pass
                tracker = tracker + increment
# print data
errHandler.close()
classesStr = classesStr[:-2]
#########################################################
### Write the output data
##########################################################
with open(csvOutFile, 'wb') as csvOut:
    writer = csv.writer(csvOut, delimiter=',')
    writer.writerow(headers)
    # print headers
    # print '<br>'
    for res in sorted(data):
        row = [res]
        for block in blocks:
            row.append(data[res][block])
        writer.writerow(row)
        # print row
        # print '<br>'
# print data
# print allRes['co'
errRotStr = ''
errResStr = ''
for rot in errRots:
    if rot != '' and rot != '-' and rot != '--':
        errRotStr += '<tr><td>' + rot + '</td></tr>'
for res in errRes:
    if res != '' and res != 'co' and res != 'u':
        errResStr += '<tr><td>' + res + '</td></tr>'
if errResStr == '': errResStr += '<tr><td>None - hooray!</td></tr>'
if errRotStr == '': errRotStr += '<tr><td>None - hooray!</td></tr>'



try:
    ################################################################################
    ### Output to html (or print to stdout)
    ################################################################################
    templateVars = dict(message=message, csvOutFile=csvOutFile,
                        errFile=errFile, rotCashcsv=rotCashcsv, updated=updated,
                        rotCashUpdate=rotCashUpdate, classesStr=classesStr,
                        firstBlock=str(firstBlock), lastBlock=str(lastBlock),
                        errRotStr=errRotStr, errResStr=errResStr)
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

except:
    print '<h1>Whoa! Something went wrong with the data output!</h1>'
    print '<h1>If you are seeing this message, please double check any dates you entered, the output summary below (resident names, etc) and try again. If you still get this error, contact Mike. :(</h1>'

