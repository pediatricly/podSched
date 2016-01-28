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
from blockUtils import blockLookup
#########################################################
### Define Globals
##########################################################
# Parameters
firstBlock = 8
lastBlock = 13
classes = [1, 2, 3] # Gives option to break up by class year
rotCashcsv = 'foodCashByWeek.csv' # csv file for the $ by rotation
# Should look like:
# Rotation, cashByWk (header row, doesn't matter what they're called)
# 'ADOL','24' (rows by rotation, second column needs to be a number. It's read
# as a string but will be converted to float below)
csvOutFile = 'lunchMoneyOut.csv'

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
