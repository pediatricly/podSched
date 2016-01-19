#! /usr/bin/python

'''
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
#This would be a good time to put classes to use. Should define a resYear class
#for the top level (a table row), a rotation class with those specific data types
#and a CoC class with those.

**NEXT**
- Figure out the top level data structure: list of dicts, move AmionName out to
be the key of the top level dict? (Probably doesn't matter much)
Either way, group by class so R3s = {} or []
- Build the outer loop to loop through all the lines of the table (easy)
- And eventually figure out how to crawl through Amion.
Can use re to get the block link from landing page.
Jumping through classes needs a post method:
    This got from R3 (default from landing page) to R2
File:!12e0dde3hucsf_peds
Page:Block
Sbcid:6
Skill:2
Rsel:-1
Blks:0-0

I think I can put that in a dict & pass it in a post, but I am not sure where
that file name is store. I don't see it in the html. Seems to come from a js
onChange="document.GetPage.submit();" which must be from a separate .js file

'''
#################################################################################
import re
import csv
import string
from bs4 import BeautifulSoup as bs
import datetime as DT
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
                schedDictB1['stopDate'] = blockStarts[i+1] + DT.timedelta(
                    days=(blockLens[i+1]/2 -1))
                schedDictB1['rotation'] = bottoms[0]
                schedDictB1['bottom'] = 1
                schedDictB2['block'] = i+1
                schedDictB2['startDate'] = blockStarts[i+1] + DT.timedelta(
                    days=blockLens[i+1]/2)
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

    for bottom in rowBottoms:
        blockI = bottom['block']
        botStart = bottom['startDate']
        botStop = bottom['stopDate']
        cellTops = []
        topStarts = set()
        topStops = set()
        for top in rowTops:
            if top['block'] == blockI:
                cellTops.append(top)
                topStarts.add(top['startDate'])
                topStops.add(top['stopDate'])

        posStarts = set()
        posStops = set()
        if len(cellTops) > 0:
            for top in cellTops:
                posStarts.add(top['startDate'])
                if top['stopDate'] + DT.timedelta(days=1) < botStop:
                    posStarts.add(top['stopDate'] + DT.timedelta(days=1))
                posStarts.add(botStart)
                if top['startDate'] + DT.timedelta(days=-1) > botStart:
                    posStops.add(top['startDate'] + DT.timedelta(days=-1))
                if top['stopDate'] < botStop:
                    posStops.add(top['stopDate'])
                posStops.add(botStop)
            remStarts = sorted(list(posStarts - topStarts))
            remStops = sorted(list(posStops - topStops))
            bottom['startDate'] = remStarts[0]
            bottom['stopDate'] = remStops[0]
            if len(remStarts) > 1:
                remStarts.pop(0)
                remStops.pop(0)
                '''
                I'm getting errors here in the rare cases of tops on split Julys
                My & Chong's schedule produce them. The logic above isn't
                grabbing a default stopDate for all scenarios. I need to add the
                end of the split block in, I think.
                As is, the loop fails because there are fewer items in remStops
                so the remStops[l] falls out of range.
                '''
                for l, split in enumerate(remStarts):
                    print split
                    try: splitBottom = {'block' : blockI,
                                'startDate' : remStarts[l],
                                'stopDate' : remStops[l],
                                'rotation' : bottom['rotation']}
                    except: print AmionName
                schedule.append(splitBottom)

# With all those adjustments done, re-sort the schedule list by start Dates
    sortSched = sorted(schedule, key=lambda k: k['startDate'])
    return sortSched
#################################################################################
### Globals & Setup
#################################################################################

week = dict(zip('Mon Tue Wed Thu Fri Sat Sun'.split(), range(7)))
allRes = {}

target = '^<TR.+?</tr>'
TDtar = '<td.+?</td>'
# htmlList = ['blockR3.html', 'blockR2.html', 'blockR1.html']
# htmlList = ['tester.html']
htmlList = ['blockR3.html']

# Loop here
for blockHTML in htmlList:
    fh = open(blockHTML, 'rb')
    html = fh.read()
    fh.close()
    blockStarts = {}
    blockStops = {}
    blockLens = {}
#################################################################################
# Find the years from the Amion block page
    yearTar = 'Schedule, (\d\d\d\d).(\d\d\d\d)'
    years = re.search(yearTar, html, re.I)
    fallYr = int(years.group(1))
    springYr = int(years.group(2))

    classTar = 'R(\d) Block'
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

    for block in blockStarts:
        bLen = blockStops[block] - blockStarts[block]
        bLen = round(bLen.days) + 1
        blockLens[block] = bLen

#################################################################################
### Read the main (residents) part of the table
#################################################################################

    for line in main:
# Grabs all the TD tags (cells) in the given row
        se2 = re.findall(TDtar, line, re.I)

# Parses those TD tags into a list of block (cells) like the eg below
        rowListIn = rowParser(se2)
        '''
# for cell in rowListI:
            # print cell
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

################################################################################
### End of main parser. allRes has the whole schedule
################################################################################
    # print resDict
# print len(resDict[AmionName]['schedule'])
# for rot in  resDict[AmionName]['schedule']:
        # print rot
# for res in allRes:
    # print res
# print allRes['Sun-V']['schedule']
for rotation in allRes['Sun-V']['schedule']:
    print rotation
################################################################################
### Little in situ output
################################################################################
# Get a list of all rotations in this year's schedule
allRotations = set()
for res in allRes:
    sched = allRes[res]['schedule']
    for rot in sched:
        allRotations.add(rot['rotation'])

'''
Proofread audit some rotation dates to make sure the new parsing works.
Put some more notes in around the trys & lens and new ifs for block quirks.
Note the rounding & half issue, that it may not find the right split dates for
months that don't start on Mondays

Make the parsing thing into a function???
Super loop to get all the residents.
Output the list of blocks for Heidi to start on
Store allRes local.

Start output machines (prolly separate scripts):
    - Indiv date lookup - given AmionName, date, return rotation. This feeds to
    podSched
    - Date lookup + csv. Given same, return rotation & parameter for that day
    (meal allowance, location, hot/cold score, whatever)
    - Weekly lookup - esp for conf lookup, given Monday
'''
