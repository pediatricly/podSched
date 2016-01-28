#! /usr/bin/python

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

import csv
import datetime as DT
import os.path
from allResStr import allRes
from blockDates import blockStarts23
from blockDates import blockStops23
from blockDates import blockStarts1
from blockDates import blockStops1
from blockUtils import blockLookup
#########################################################
### Define Globals
##########################################################
# Parameters
csvDirName = 'badgeScanCSVs'
csvOutFile = 'confAttendOut.csv'
amConfStartHr = 8 # Start time hours
amConfStartMin = 0 # Start time minutes
amTol = 60 # Tolerance for what you'll call an AM conf time stamp, in MINUTES

noonConfStartHr = 12
noonConfStartMin = 15
noonTol = 75 # Tolerance for what you'll call an noon conf time stamp, in MINUTES

startRange = DT.date(2015,7,1)
stopRange = DT.date(2016,6,30)
##########################################################
# Setup the basic intake data
masterSet = set()
prelimList = []
cleanDict = {}
inputFiles = []

# Do this round-about datetime object thing to save the hassle of parsing time.
# Need datetime objects to utilize timedelta
amConfStart = DT.datetime(2016,1,1,amConfStartHr,amConfStartMin,0)
amCutoffPre = amConfStart - DT.timedelta(minutes=amTol)
amCutoffPost = amConfStart + DT.timedelta(minutes=amTol)
amConfStart = DT.time(amConfStart.hour,amConfStart.minute)
amCutoffPre = DT.time(amCutoffPre.hour, amCutoffPre.minute)
amCutoffPost = DT.time(amCutoffPost.hour, amCutoffPost.minute)

noonConfStart = DT.datetime(2016,1,1,noonConfStartHr,noonConfStartMin,0)
noonCutoffPre = noonConfStart - DT.timedelta(minutes=noonTol)
noonCutoffPost = noonConfStart + DT.timedelta(minutes=noonTol)
noonConfStart = DT.time(noonConfStart.hour,noonConfStart.minute)
noonCutoffPre = DT.time(noonCutoffPre.hour, noonCutoffPre.minute)
noonCutoffPost = DT.time(noonCutoffPost.hour, noonCutoffPost.minute)
#########################################################
### Read the dir of CSVs
##########################################################
directory = os.listdir(csvDirName)
for filename in directory:
    pathName = os.path.join(csvDirName, filename)
    if pathName[-4:] == '.csv':
        inputFiles.append(filename)
        fh = open(pathName, 'rb')
        reader = csv.reader(fh, delimiter=',')
        for row in reader:
            tupule = (row[0], row[1])
            masterSet.add(tupule)

for item in masterSet:
    timeStamp = item[0]
    split1 = timeStamp.split(' ')
    date1 = split1[0]
    slash1 = date1.find('/')
    slash2 = date1.find('/', slash1+1)
    date = DT.date(int(date1[slash2+1:])+2000, int(date1[:slash1]), int(date1[slash1+1:slash2]))
    ap = split1[2]
    time1 = split1[1]
    colon1 = time1.find(':')
    colon2 = time1.find(':', colon1+1)
    if ap == 'PM' or ap =='pm':
        time = DT.time(int(time1[:colon1])+12, int(time1[colon1+1:colon2]), int(time1[colon2+1:]))
    else:
        time = DT.time(int(time1[:colon1]), int(time1[colon1+1:colon2]), int(time1[colon2+1:]))
    tempDict = {'date':date, 'time': time, 'badge':item[1]}

    if time <= amCutoffPost and time >= amCutoffPre:
        tempDict['conf'] = 'am'
        hrLate = time.hour - amConfStart.hour
        if hrLate < 0: minLate = 0
        else:
            minLate = max(time.minute - amConfStart.minute, 0)
            minLate = minLate + hrLate*60
        tempDict['minLate'] = minLate
        print tempDict
    elif time <= noonCutoffPost and time >= noonCutoffPre:
        tempDict['conf'] = 'noon'
        hrLate = time.hour - noonConfStart.hour
        if hrLate < 0: minLate = 0
        else:
            minLate = max(time.minute - noonConfStart.minute, 0)
            minLate = minLate + hrLate*60
        tempDict['minLate'] = minLate
        print tempDict
    else: tempDict['conf'] = 'unknown'

    prelimList.append(tempDict)

# print prelimList # {'date': datetime.date(2016, 1, 26), 'badge': '21378801298865', 'time': datetime.time(8, 41, 12)}

#########################################################
### Get rid of duplicates from multiple scans of the same badge at same conference
##########################################################















'''

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

# This does the actual rotation lookup & adds up cash going week by week
# (Mondays) through the given date range.
for pgyYr in classes:
    if pgyYr == 1:
        starts = blockStarts1
        stops = blockStops1
    else:
        starts = blockStarts23
        stops = blockStops23

    day1 = DT.datetime.strptime(starts[firstBlock], '%Y-%m-%d')
    firstMon = day1 + DT.timedelta(days=(7-day1.weekday())) - increment
    endDay = DT.datetime.strptime(stops[lastBlock], '%Y-%m-%d')

    for res in allRes:
        if allRes[res]['pgy'] == pgyYr:
            tracker = firstMon
            # tracker = tracker + DT.timedelta(7)
            while (tracker < endDay):
                tupule = blockLookup(tracker, res, allRes)
# rotTest = blockLookup('2016-01-20', 'Sun-V', allRes)
# print rotTest # returns 'ORANGE3'
                block = tupule[0]
                rotation = tupule[1]
                # These try blocks allow skipping empty cells, eg, partial year
                # super seniors. Prints those output for you to check
                try: cashRot = cashData[rotation]
                except:
                    cashRot = 0
                    print res, tupule
                try: data[res][block] += cashRot
                except: pass
                tracker = tracker + increment
# print data

#########################################################
### Write the output data
##########################################################
with open(csvOutFile, 'wb') as csvOut:
    writer = csv.writer(csvOut, delimiter=',')
    writer.writerow(headers)
    for res in sorted(data):
        row = [res]
        for block in blocks:
            row.append(data[res][block])
        writer.writerow(row)
# print data

# print allRes['co']
'''
