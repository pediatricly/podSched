#! /usr/bin/python

'''
Marks:
    a - initial import statements, parameters, globals
    b - AmionBlockScraper function
    c - rowParser function
    d - cellListParser function - this is the huge block that parses individual
    cells in the block schedule with all their multilines & split bottom rows.
    e - the main loop that goes through the Amion html
    f - data output

Plan (not flow)
#- Finish the cell parsing - getting close. Next task is to read the multipart
#cells. Bottom line is assumed to be month minus date range in top lines.
#If bottom line has a |, block is split in half. Those halves may be broken by
#top lines.
#-
#- Build separate but similar top loop that reads the table date ranges from
#first row
#- At some point, use str.isalpha() to strip the =,-,* crap off AmionName
#
#Then, for reals - ponder the data structure you want. Maybe:
#{AmionN-F :
#  schedule : [
#    {block : 9,
#     startDate : 2016,3,7,
#     stopDate : 2016,3,13,
#     rotation : 'VAC'},
#    {block : 9,
#     startDate: 2016,3,14,
#     stop...
#    }],
#  CoC :
#     {weekday : 2
#     weekdayStr : 'Wed'
#     time: 'pm'
#     location: 'CARDS'},
# Amion2-F :
#  schedule :...
#}
#
#This setup preserves an index for sub-rotations because they are in a list.
#But it allows multiple to have the same block attribute.
#
'''
#################################################################################
import requests
import re
import csv
from bs4 import BeautifulSoup as bs
import datetime as DT
# import json
################################################################################
### Globals & Setup
################################################################################
# These parameters feed AmionBlockScraper function to scrape the block schedules
# out of Amion automatically. All this was reverse engineered on 2Feb16, not
# sure how stable it is.
urlStub = "http://amion.com/cgi-bin/ocs"
payload = {'login' : 'ucsfpeds'}
blockTar = 'cgi-bin/ocs\?Fi=(.+?)[&"]'
skills = {'2': '', '3': '', '4':''}
firstpart = "&Page=Block&Sbcid=6&Skill="
secondpart = '&Rsel=-1&Blks=0-0'

# Specifcy the block 1 split manually because the computer may guess
# wrong
block1split1 = DT.date(2015, 7, 6)
block1split23 = DT.date(2015, 7, 13)


# Setup output pieces
outfile = 'allResStr.py'
CoC = 'CoC.csv'
allResStr = {}
blockStarts23str = 'blockStarts23 = '
blockStops23str = 'blockStops23 = '
blockStarts1str = 'blockStarts1 = '
blockStops1str = 'blockStops1 = '
updated = 'updated = ' + DT.date.today().isoformat()

# Other globals
allRes = {}
week = dict(zip('Mon Tue Wed Thu Fri Sat Sun'.split(), range(7)))


#################################################################################
### Amion Scraper Function
# Takes the main Amion url, login info (payload), fragments of the url query
# string, and a dict. Turns out Amion expects them in a certain order & just spits out the
# default (R3) page if they're not. Rather than get fancy with ordering
# urlencode, I just used this quick string hack.
# The dict has keys = "skill" #s. This is how Amion organizes classes. skill 2 =
# R2s, 3 = R3s & 4 = R1s. (skill 1 is chiefs).
# The way it does the file name lookup is odd & explained below.
# This is the query string data (loading R2 from R3):
# File:!12e0dde3hucsf_peds  # This is what changes on almost every load.
# Page:Block
# Sbcid:6
# Skill:2
# Rsel:-1
# Blks:0-0
#################################################################################
def AmionBlockScraper(url, load, tar, first, second, skillsDict):
    # First, load the main Amion landing page.
    r = requests.post(urlStub, data=load)
    html = r.text # This is outputting the html of the actual schedule landing page

    # Regex for this link form. The ?Fi=__ returns this random file name that
    # seems to be the UCSF schedule. This link changes to a different random
    # string on almost every load, but all the links have the same string.
    search = re.findall(tar ,html, re.M)
    # To be sure, put all those filename strings into a set.
    nameSet = set(); fileStub = ''

    # Make sure the set has 1 element. Should put some better error handling in here.
    for item in search: nameSet.add(item)
    if len(nameSet) > 1: print "whoa - more than 1 link..."
    # Assuming it has 1 element, use that as the filename string.
    elif len(nameSet) == 1:
        fileStub = nameSet.pop().encode('ascii', 'ignore')
    else: print "whoa - regex found nothing"

    # Use that filename to construct the links to the class block schedule pages.
    # Those links vary only by the skill parameter, hence this loop.
    # The html that returns is stored as values in the skillsDict.
    for skill in skillsDict:
        htmlI = ''
        load['Skill'] = str(skill)
        # As above, I initially used urlencode instead of string concatenation,
        # but Amion expects the query string in this specific order.
        url = urlStub + '?File=' + fileStub + first + skill + second
        rI = requests.post(url)
        htmlI = rI.text
        skillsDict[skill] = htmlI

    # skillsDict = {'2':'<block page html>...', '3':'<html...>',..}
    return skillsDict

#################################################################################
### Parser Function
# Takes list of <td></td> cells from re.findall
# Outputs list len= # table columns with each item corresponding to 1 cell
# For cells with multiple internal tags, returns all text in a list within list
# Also: cleans out duplicates strings, white space & converts everything to
# ASCII (ignores other unicode characters
#################################################################################
def rowParser(seList):
    rowList = []
    for td in seList:
        soup = bs(td)
        if soup.string != None:
            soupStr = soup.string
            # Append single entry cells (blocks)
            rowList.append(soupStr.encode('ascii','ignore'))
        else:
            cellList = []
            inners = soup.descendants # Got to use descendants, not children or
            # findall here - those leave out some uncolored text
            for el in inners:
                if el.string == None: pass
                else:
                    elStr = el.string
                    cellList.append(elStr.encode('ascii','ignore'))
            # newList just gets stripped strings
            newList = []
            for i, item in enumerate(cellList):
                newList.append(item.strip())
            # newList2 clears out dups. Top lines must be followed by dates
            newList2 = []
            for i, item in enumerate(newList):
                if i < (len(newList)-1):
                    if item == newList[i+1]: pass
                    else: newList2.append(item)
                else: newList2.append(item)

            #Append multipart cells
            rowList.append(newList2)
    return rowList

#################################################################################
### This super complex loop parses that list of cells into a list of dicts with
# all the schedule data by resident.
# The first section is easy, parse the single rotation blocks.
# The subsequent code parses the much trickier multi-rotation blocks using the
# logic by which they are listed:
# - Bottom row is the default rotation. It fills days not listed in top rows.
# - If the bottom row is split ' | ', same rule applies but changes the bottom
# rotation at mid-block,
# - All the top rows take scehdule precedence and are assumed to be mutually
# non-overlapping.
# - Thus the bottoms have to adjust their start/stop dates to accomodate the
# tops.

def cellListParser(rowListI):
    for i, item in enumerate(rowListI):
        # Setup empty dicts for each cell/item in the row
        schedDict = {}
        schedDictB = {}
        schedDictB1 = {}
        schedDictB2 = {}

# Parse the easy, single rotation blocks - they are plain strings in rowList
        if type(item) == str:
            schedDict['block'] = i+1
            schedDict['startDate'] = blockStarts[i+1]
            try:
                schedDict['stopDate'] = blockStops[i+1]
# Corrects lookup for the last block by going to the end of the year
            except KeyError:
                schedDict['stopDate'] = blockStops[lastBlock] + DT.timedelta(days=1)
            schedDict['rotation'] = item
            schedDict['bottom'] = 1 # All these are "bottoms" ie default rotations

# cells that are list are multirotation blocks. May be just split bottoms or
# bottom and top(s)
        elif type(item) == list:
            length = len(item)
            lastTop = ''
            # Find the dates that mark the line between tops & bottoms
            for j, string in enumerate(item):
                if string[0].isdigit() == True and string[-1].isdigit() == True:
                    lastTop = int(j)
            # If there is a top line, parse it & save bottom for loop below
            if lastTop != '':
                tops = item[:lastTop+1]
                bottomRow = item[lastTop+1:]

                # Parse the tops into a dict
                for j, other in enumerate(tops):
                    schedDictO = {}
                    if other[0].isdigit() == True:
                        weekRot = item[j-1]
                        dates = other.split('-')
                        startDO = dates[0]
                        startDOs = startDO.split('/')
                        startDOmo = int(startDOs[0])
                        if startDOmo > 6: startDOYr = fallYr
                        else: startDOYr = springYr
                        startDOday = int(startDOs[1])

                        try: stopDO = dates[1]
                        except: continue
                        stopDOs = stopDO.split('/')
                        stopDOmo = int(stopDOs[0])
                        if stopDOmo > 6: stopDOYr = fallYr
                        else: stopDOYr = springYr
                        stopDOday = int(stopDOs[1])
                        schedDictO['block'] = i+1
                        schedDictO['startDate'] = DT.date(startDOYr, startDOmo,
                                                        startDOday)
                        schedDictO['stopDate'] = DT.date(stopDOYr, stopDOmo,
                                                        stopDOday)
                        schedDictO['rotation'] = weekRot
                        schedDictO['bottom'] = 0
                        if schedDictO != {}:
                            schedule.append(schedDictO)
            # If there's no top line, the whole cell, [a list], is the bottom row
            else: bottomRow = item

            # Parse the bottom row. Start by concatenating if not already
            if len(bottomRow) > 1: bottom = ' '.join(bottomRow)
            else: bottom = bottomRow[0]
# If it is a split bottom, needs 2 dicts
            if '|' in bottom:
                bottoms = bottom.split(' | ')
                schedDictB1['block'] = i+1
                schedDictB1['startDate'] = blockStarts[i+1]
                schedDictB1['stopDate'] = blockSplits[i+1] + DT.timedelta(
                    days=-1)
                schedDictB1['rotation'] = bottoms[0]
                schedDictB1['bottom'] = 1
                schedDictB2['block'] = i+1
                schedDictB2['startDate'] = blockSplits[i+1]
                schedDictB2['stopDate'] = blockStops[i+1]
                schedDictB2['rotation'] = bottoms[1]
                schedDictB2['bottom'] = 1
                schedule.append(schedDictB1)
                schedule.append(schedDictB2)
                item.pop(length - 1)
# Non-split bottoms get a simple parsing
            else:
                schedDictB['block'] = i+1
                schedDictB['startDate'] = blockStarts[i+1]
                schedDictB['stopDate'] = blockStops[i+1]
                schedDictB['rotation'] = bottom
                schedDictB['bottom'] = 1
                schedule.append(schedDictB)
        if schedDict != {}:
            schedule.append(schedDict)

# print len(resDict[AmionName]['schedule'])
# for rot in  resDict[AmionName]['schedule']:
        # print rot

#################################################################################
### Finally, adjust the bottoms' dates by the 'tops take precendence, bottoms
# fill in the rest' rule.
# Loop proceeds by blocks because nothing crosses block lines (rotations that
# span blocks are listed twice).
# I use sets for this as it fits the 'bottoms fill the rest' logic.
# The last loop allows for discontinuous bottoms, where, say, someone is on Cards for the
# month but has PLUS only in week 2. These are rare in 4wk blocks but may be
# common in longer blocks. This loops over the bottoms, but the pos-dates sets
# include all possible dates by blocks and puts start-stop dates together in
# order, so this should allow for something like a 2-wk top that spans weeks 2 &
# 3 in a split rotation block. (They don't seem to be encoding rotations this
# way currently but could esp if blocks get longer.)

# Start by grabbing all tops & bottoms (could have done this above but it's
# messy enough)
    rowTops = []
    rowBottoms = []
    for rotation in schedule:
        if rotation['bottom'] == 1:
            rowBottoms.append(rotation)
        elif rotation['bottom'] == 0:
            rowTops.append(rotation)

    for blockNum in range(1, lastBlock + 1):
        blockBottoms = []
        blockTops = []
        topStarts = set()
        topStops = set()
        posStarts = set()
        posStops = set()
        for rotation in schedule:
            if rotation['block'] == blockNum:
                if rotation['bottom'] == 1:
                    # Add bottoms to sets
                    # Looping this way should get all bottoms, split or not
                    blockBottoms.append(rotation)
                    posStarts.add(rotation['startDate'])
                    posStops.add(rotation['stopDate'])
                else:
                    # Add tops to sets
                    blockTops.append(rotation)
                    topStarts.add(rotation['startDate'])
                    topStops.add(rotation['stopDate'])
                    posStarts.add(rotation['startDate'])
                    posStops.add(rotation['stopDate'])
                    # Tops need their days before & after added to posSets but
                    # only if in the block
                    if rotation['stopDate'] + DT.timedelta(days=1) < blockStops[blockNum]:
                        posStarts.add(rotation['stopDate'] + DT.timedelta(days=1))
                    if rotation['startDate'] + DT.timedelta(days=-1) > blockStarts[blockNum]:
                        posStops.add(rotation['startDate'] + DT.timedelta(days=-1))

        # Only need to adjust the dates if there are tops. O/w dates should be
        # right from the split parsing. Hence the if len > 0:
        if len(blockTops) > 0:
            # These are blocks with only 1 bottom
            if len(blockBottoms) == 1:
                remStarts = sorted(list(posStarts - topStarts))
                remStops = sorted(list(posStops - topStops))
                if len(remStarts) > 1:
                    blockBottoms[0]['startDate'] = remStarts[0]
                    blockBottoms[0]['stopDate'] = remStops[0]
                    remStarts.pop(0)
                    remStops.pop(0)
                    for m, rem in enumerate(remStarts):
                        splitBottom = {'block' : blockNum,
                                        'startDate' : rem,
                                        'stopDate' : remStops[m],
                                        'rotation' : blockBottoms[0]['rotation']}
                        schedule.append(splitBottom)
                else:
                    blockBottoms[0]['startDate'] = remStarts[0]
                    blockBottoms[0]['stopDate'] = remStops[0]

            # These are blocks with 2 bottoms:
            # For these, need to split the date sets at the split, make 2 lists
            # and do the whole date adjustment process twice
            elif len(blockBottoms) ==2:
                posStarts1 = set()
                posStarts2 = set()
                posStops1 = set()
                posStops2 = set()
                # Find the split:
                for date in posStarts:
                    if date < blockSplits[blockNum]: posStarts1.add(date)
                    else: posStarts2.add(date)
                for date in posStops:
                    if date <= blockSplits[blockNum]: posStops1.add(date)
                    else: posStops2.add(date)

                # Get the diff of the sets. This does not create a 'negative date'
                # for dates in the other half that are not in posSet
                remStarts1 = sorted(list(posStarts1 - topStarts))
                remStarts2 = sorted(list(posStarts2 - topStarts))
                remStops1 = sorted(list(posStops1 - topStops))
                remStops2 = sorted(list(posStops2 - topStops))

                # Go through the date adjusting for first split
                if len(remStarts1) > 2:
                    blockBottoms[0]['startDate'] = remStarts1[0]
                    blockBottoms[0]['stopDate'] = remStops1[0]
                    remStarts1.pop(0)
                    remStops1.pop(0)
                    for m, rem in enumerate(remStarts1):
                        splitBottom1 = {'block' : blockNum,
                                        'startDate' : rem,
                                        'stopDate' : remStops1[m],
                                        'rotation' : blockBottoms[0]['rotation']}
                        schedule.append(splitBottom1)
                else:
                    blockBottoms[0]['startDate'] = remStarts1[0]
                    blockBottoms[0]['stopDate'] = remStops1[0]

                # Go through the date adjusting for second split
                if len(remStarts2) > 2:
                    blockBottoms[1]['startDate'] = remStarts2[1]
                    blockBottoms[1]['stopDate'] = remStops2[1]
                    remStarts2.pop(0)
                    remStops2.pop(0)
                    for m, rem in enumerate(remStarts2):
                        splitBottom2 = {'block' : blockNum,
                                        'startDate' : rem,
                                        'stopDate' : remStops2[m],
                                        'rotation' : blockBottom[1]['rotation']}
                        schedule.append(splitBottom2)
                else:
                    blockBottoms[1]['startDate'] = remStarts2[0]
                    blockBottoms[1]['stopDate'] = remStops2[0]
            else:
                print 'wtf! There should not be >2 bottoms. There are ', len(blockBottoms)

# With all those adjustments done, re-sort the schedule list by start Dates
    sortSched = sorted(schedule, key=lambda k: k['startDate'])
    return sortSched

#################################################################################
### Start loop to read the html input
#################################################################################
# This scrapes Amion & returns dict whose values are the html of the block
# schedules
skills = AmionBlockScraper(urlStub, payload, blockTar, firstpart, secondpart, skills)

# Loop here
for skill in skills:
    # Regex targets from the Amion block html
    target = '^<TR.+?</tr>'
    TDtar = '<td.+?</td>'
    yearTar = 'Schedule, (\d\d\d\d).(\d\d\d\d)'
    classTar = 'R(\d) Block'

    blockStarts = {}
    blockStops = {}
    blockLens = {}
    blockSplits = {}
#################################################################################
# Find the years from the Amion block page
    html = skills[skill]
    # print html
    years = re.search(yearTar, html, re.I)
    fallYr = int(years.group(1))
    springYr = int(years.group(2))

    classR = int(re.search(classTar, html, re.I).group(1))
# re to find the whole table (assumes there's only 1 on the html page

    table = re.findall(target, html, re.M)
    header = table[0]
    main = table[1:]
#################################################################################
### Read the headers to get block start-stop dates
#################################################################################
    seHead = re.findall(TDtar, header, re.I)

    headDates = rowParser(seHead)
    headDates.pop(0)
    headDates.pop()

    prevMonthStart = 4
    prevMonthStop = 4
    yearI = fallYr
    for cell in headDates:
        block = int(cell[0])
        datesRaw = cell[1]
        datesSplit = datesRaw.split('-')
        startD = datesSplit[0]
        startSplit = startD.split('/')
        startNums = []
        for num in startSplit:
            numInt = int(num)
            startNums.append(numInt)
        if startNums[0] >= prevMonthStart: pass
        else: yearI = springYr
        blockStarts[block] = DT.date(yearI, startNums[0], startNums[1])
        prevMonthStart = startNums[0]

        stopD = datesSplit[1]
        stopSplit = stopD.split('/')
        stopNums = []
        for num in stopSplit:
            numInt = int(num)
            stopNums.append(numInt)
        if stopNums[0] >= prevMonthStop: pass
        else: yearI = springYr
        blockStops[block] = DT.date(yearI, stopNums[0], stopNums[1])
        prevMonthStop = stopNums[0]

    lastBlock = max(blockStarts.keys())

    # These loops define the mid-date for split blocks. It takes a manual entry for
    # block1 because it's irregularly shaped (ie doesn't start on Monday).
    # CAREFUL: this works fine in the 4 week / other blocks start on Mondays world
    # It might have issues if the block structure changes.
    for block in blockStarts:
        bLen = blockStops[block] - blockStarts[block]
        bLen = round(bLen.days) + 1
        blockLens[block] = bLen

    for block in blockStarts:
        if block == 1:
            if classR == 1: blockSplits[block] = block1split1
            else: blockSplits[block] = block1split23
        else:
            blockSplits[block] = blockStarts[block] + DT.timedelta(
                days=(blockLens[block] / 2))


    # This section writes the dates for local use.

    blockStartsStr = {}
    for block in blockStarts:
        blockStartsStr[block] = blockStarts[block].isoformat()
    blockStopsStr = {}
    for block in blockStops:
        blockStopsStr[block] = blockStops[block].isoformat()
    if classR == 3:
        blockStarts23str += str(blockStartsStr)
        blockStops23str += str(blockStopsStr)
    elif classR == 1:
        blockStarts1str += str(blockStartsStr)
        blockStops1str += str(blockStopsStr)
#################################################################################
### Read the main (residents) part of the table
#################################################################################

    for line in main:
# Grabs all the TD tags (cells) in the given row
        se2 = re.findall(TDtar, line, re.I)

# Parses those TD tags into a list of block (cells) like the eg below
        rowListIn = rowParser(se2)
        '''
        List of the table row's cells where multipart cells are list items.
        Ainsworth-A=
        E-CICU
        PICU3
        SFN3
        ['VAC', '| SFX']
        SFO3
        SFO3
        PURPLE3
        PURPLE3
        ['VAC', '3/7-3/13', 'JEOP | E-Pulm']
        ['CHO-ICU', '4/4-4/10', 'JEOP | CARDS']
        ['VAC', '5/2-5/8', 'CHO-ICU']
        ICN3
        Chief
        '''

# Pop off the AmionName from the first cell of the row
        AmionName = rowListIn.pop(0)
        if AmionName[-1].isalpha() == False:
            AmionName = AmionName[:-1]
        if AmionName[0].isalpha() == False: continue
# Pop off & parse to dict the Coc date from the last cell
        CoCRaw = rowListIn.pop(lastBlock)
        CoCweekDayStr = CoCRaw[:3]
        CoCTime = CoCRaw[3:5]
        CoCLoc = CoCRaw[5:]
        try: CoCweekDay = week[CoCweekDayStr]
        except KeyError: CoCweekDay = None

# Setup data structures for ea resident/row of the table
        CoCDict = {'weekday' : CoCweekDay,
                'weekdayStr' : CoCweekDayStr,
                'time' : CoCTime,
                'location' : CoCLoc}
        # resDict = {AmionName : {
        resDict = {
                    'pgy' : classR,
                'schedule' : [],
                'CoC' : CoCDict}
        schedule = []

# Finally, put the sorted rotations list into the current resDict
        sortSchedOut = cellListParser(rowListIn)
        resDict['schedule'] = sortSchedOut
# And add the whole resident's info to the main dict
        allRes[AmionName] = resDict

'''
allRes looks like this:
{'Brim-R' :
    {'CoC': {'weekdayStr': 'Thu', 'location': 'SFGH', 'weekday': 3, 'time': 'pm'},
    'schedule': [{'startDate': datetime.date(2015, 7, 1), 'rotation': 'E-Res', 'stopDate': datetime.date(2015, 7, 5), 'block': 1, 'bottom': 0}, {'startDate': datetime.date(2015, 7, 6), 'rotation': 'PLUS', 'stopDate': datetime.date(2015, 7, 12), 'block': 1, 'bottom': 0}
    'pgy': 3}
 'Chong-A' : ...
}
'''
################################################################################
### End of main parser. allRes has the whole schedule
### Next section has prints for debugging
################################################################################
# print resDict
# print len(resDict[AmionName]['schedule'])
# for rot in  resDict[AmionName]['schedule']:
        # print rot
# for res in allRes:
    # print res
# print allRes['Sun-V']['schedule']
# testRes = 'Brim-R'
# print 'Test Resident: ', testRes
# print allRes[testRes]
# for rotation in allRes[testRes]['schedule']:
    # print rotation

################################################################################
### Save the allRes dict & other output locally
################################################################################
R1str = ''
R2str = ''
R3str = ''
totalRots = 0
for res in sorted(allRes):
    if allRes[res]['pgy'] == 1:
        R1str = R1str + res + ', '
    elif allRes[res]['pgy'] == 2:
        R2str = R2str + res + ', '
    elif allRes[res]['pgy'] == 3:
        R3str = R3str + res + ', '
    res2 = allRes[res]
    sched = res2['schedule']
    for rotation in sched:
        totalRots += 1
        rotation['startDate'] = rotation['startDate'].isoformat()
        rotation['stopDate'] = rotation['stopDate'].isoformat()
    allResStr[res] = res2
fhO = open(outfile, 'wb')
fhO.write('allRes = ' + str(allRes))
fhO.write('\n')
fhO.write(blockStarts23str)
fhO.write('\n')
fhO.write(blockStops23str)
fhO.write('\n')
fhO.write(blockStarts1str)
fhO.write('\n')
fhO.write(blockStops1str)
fhO.write('\n')
fhO.write(updated)
fhO.write('\n')
fhO.write('block1split1 = ' + str(block1split1))
fhO.write('\n')
fhO.write('block1split23 = ' + str(block1split23))
fhO.write('\n')

'''
outJson = 'allResJson.txt'
fhO = open(outJson, 'wb')
json.dump(allResStr, fhO)
'''
fhO.close()
print 'Scraped schedule data on ' + str(len(allRes)) + ' residents.'
print '(Should be about 90.)'
print 'R1s: ' + R1str[:-2]
print 'R2s: ' + R2str[:-2]
print 'R3s: ' + R3str[:-2]
print 'Total Rotations: ' + str(totalRots)
print '(Should be about 1500.)'
# print blockStarts
# print blockStops

################################################################################
### Little in situ output
################################################################################
# Get a list of all rotations in this year's schedule
# allRotations = set()
# for res in allRes:
    # sched = allRes[res]['schedule']
    # for rot in sched:
        # allRotations.add(rot['rotation'])

# Write the list of CoC days
with open(CoC, 'wb') as outfile:
    for res in sorted(allRes):
        outfile.write(res + ',' + allRes[res]['CoC']['weekdayStr'] + '\n')

'''
Note the rounding & half issue, that it may not find the right split dates for
months that don't start on Mondays

Make the parsing thing into a function???
Store allRes local.

Start output machines (prolly separate scripts):
    - Indiv date lookup - given AmionName, date, return rotation. This feeds to
    podSched
    - Date lookup + csv. Given same, return rotation & parameter for that day
    (meal allowance, location, hot/cold score, whatever)
    - Weekly lookup - esp for conf lookup, given Monday
'''
