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
from allResStr import allRes
from blockDates import blockStarts23
from blockDates import blockStops23
from blockDates import blockStarts1
from blockDates import blockStops1
#########################################################
### Define Globals
##########################################################
def blockLookup(date, AmName, resDict):
    if type(date) != str:
        isoDate = date.isoformat()
    else: isoDate = date
    rot = ''
    block = ''
    blockSched = resDict[AmName]['schedule']
    for rotation in blockSched:
        if isoDate >= rotation['startDate'] and isoDate <= rotation['stopDate']:
            rot = rotation['rotation']
            block = rotation['block']
    return (block, rot)
##########################################################
# rotTest = blockLookup('2016-01-20', 'Sun-V', allRes)
# print rotTest # returns 'ORANGE3'

rotCashcsv = 'foodCashByWeek.csv'
cashData = {}
fh = open(rotCashcsv, 'rb')
reader = csv.DictReader(fh)
for row in reader:
    rot = row['Rotation']
    cashWk = row['cashWk']
    cashData[rot] = float(cashWk)
# print cashData
# {'PIC': '0', 'SFO2': '0', 'FLEX': '0', 'E-Ophtho': '24', ...}

############################################
firstBlock = 8
lastBlock = 13
blocks = [x for x in range(firstBlock, lastBlock+1)]
headers = ['AmionName']
for block in blocks:
    headers.append(block)
data = {}
classes = [1, 2, 3]
increment = DT.timedelta(7)

for res in allRes:
    resDict = {}
    for block in blocks:
        if block <14:
            resDict[block] = 0
    if allRes[res]['pgy'] in classes:
        data[res] = resDict


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
                block = tupule[0]
                rotation = tupule[1]
                try: cashRot = cashData[rotation]
                except:
                    cashRot = 0
                    print res, tupule
                try: data[res][block] += cashRot
                except: pass
                tracker = tracker + increment
# print data
csvOutFile = 'lunchMoneyOut.csv'
with open(csvOutFile, 'wb') as csvOut:
    writer = csv.writer(csvOut, delimiter=',')
    writer.writerow(headers)
    for res in data:
        row = [res]
        for block in blocks:
            row.append(data[res][block])
        writer.writerow(row)
# print data

# print allRes['co']
'''
resTemp = ['Sun-V', 'Brim-R']
    while (tracker < endDay):
        for res in allRes:
            if allRes[res]['pgy'] == pgyYr:
                data[res] = {}
                tupule = blockLookup(tracker, res, allRes)
                block = tupule[0]
                rotation = tupule[1]
                cashRot = cashData[rotation]
                previous = data[res].get(block, 0)
                print previous
                data[res][block] = previous + cashRot
                # try: data[res][block] += cashRot
                # except KeyError:
                    # data[res] = {block: cashRot}
        tracker = tracker + increment
'''
