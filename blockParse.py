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
#{name : AmionN-F,
# schedule : [
#    {block : 9,
#     startDate : 2016,3,7,
#     stopDate : 2016,3,13,
#     rotation : 'VAC'},
#    {block : 9,
#     startDate: 2016,3,14,
#     stop...
#    }],
# CoC :
#     {weekday : 2
#     weekdayStr : 'Wed'
#     time: 'pm'
#     location: 'CARDS'}
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
### Globals & Setup
#################################################################################

week = dict(zip('Mon Tue Wed Thu Fri Sat Sun'.split(), range(7)))
blockHTML = 'blockR3.html'
fh = open(blockHTML, 'rb')
html = fh.read()
blockStarts = {}
blockStops = {}

target = '^<TR.+?</tr>'
TDtar = '<td.+?</td>'
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
            newList = []
            for i, item in enumerate(cellList):
                newList.append(item.strip())
            newList2 = []
            for i, item in enumerate(newList):
                if i < (len(newList)-1):
                    if item == newList[i+1]: pass
                    else: newList2.append(item)
                else: newList2.append(item)

            rowList.append(newList2)
    return rowList

#################################################################################
yearTar = 'Schedule, (\d\d\d\d).(\d\d\d\d)'
years = re.search(yearTar, html, re.I)
fallYr = int(years.group(1))
springYr = int(years.group(2))

# re to find the whole table (assumes there's only 1 on the html page
table = re.findall(target, html, re.M)

#################################################################################
### Read the headers to get block start-stop dates
#################################################################################
header = table[0]
seHead = re.findall(TDtar, header, re.I)

headDates = rowParser(seHead)
headDates.pop(0)
headDates.pop()

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
    #for num in startNums:
    if startNums[0] > 6: yearI = fallYr
    else: yearI = springYr
    blockStarts[block] = DT.date(yearI, startNums[0], startNums[1])

    stopD = datesSplit[1]
    stopSplit = stopD.split('/')
    stopNums = []
    for num in stopSplit:
        numInt = int(num)
        stopNums.append(numInt)
    #for num in stopNums:
    if stopNums[0] > 6: yearI = fallYr
    else: yearI = springYr
    blockStops[block] = DT.date(yearI, stopNums[0], stopNums[1])

#################################################################################
### Read the main (residents) part of the table
#################################################################################

main = table[1:]
# for line in main:
# This is where to build the loop for all resident lines eventually
line = main[2]
se2 = re.findall(TDtar, line, re.I)

rowListI = rowParser(se2)
for cell in rowListI:
    print cell

AmionName = rowListI.pop(0)
if AmionName[-1].isalpha() == False:
    AmionName = AmionName[:-1]

CoCRaw = rowListI.pop(13)
CoCweekDayStr = CoCRaw[:3]
CoCTime = CoCRaw[3:5]
CoCLoc = CoCRaw[5:]
CoCweekDay = week[CoCweekDayStr]

CoCDict = {'weekday' : CoCweekDay,
           'weekdayStr' : CoCweekDayStr,
           'time' : CoCTime,
           'location' : CoCLoc}
resDict = {AmionName : {
           'schedule' : [],
           'CoC' : CoCDict}}

for i, item in enumerate(rowListI):
    schedDict = {}
    schedDictB = {}
    schedDictB1 = {}
    schedDictB2 = {}
    if type(item) == str:
        schedDict['block'] = i+1
        schedDict['startDate'] = blockStarts[i+1]
        try:
            schedDict['stopDate'] = blockStops[i+1]
        except KeyError:
            schedDict['stopDate'] = blockStops[13] + DT.timedelta(days=1)
        schedDict['rotation'] = item
        schedDict['bottom'] = 1
    elif type(item) == list:
        length = len(item)
        bottom = item[length - 1]
        for j, other in enumerate(item):
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

                stopDO = dates[1]
                stopDOs = stopDO.split('/')
                stopDOmo = int(stopDOs[0])
                if stopDOmo > 6: stopDOYr = fallYr
                else: stopDOYr = springYr
                stopDOday = int(stopDOs[1])
                schedDictO['block'] = i+1
                schedDictO['startDate'] = DT.date(startDOYr, startDOmo, startDOday)
                schedDictO['stopDate'] = DT.date(stopDOYr, stopDOmo, stopDOday)
                schedDictO['rotation'] = weekRot
                schedDictO['bottom'] = 0
                if schedDictO != {}:
                    resDict[AmionName]['schedule'].append(schedDictO)
        if bottom[0] == '|': bottom = item[length-2] + ' ' + bottom
        if '|' in bottom:
            bottoms = bottom.split(' | ')
# Parse the bottom row
            schedDictB1['block'] = i+1
            schedDictB1['startDate'] = blockStarts[i+1]
            schedDictB1['stopDate'] = blockStarts[i+1] + DT.timedelta(days=13)
            schedDictB1['rotation'] = bottoms[0]
            schedDictB1['bottom'] = 1
            schedDictB2['block'] = i+1
            schedDictB2['startDate'] = blockStarts[i+1] + DT.timedelta(days=14)
            schedDictB2['stopDate'] = blockStarts[i+2] + DT.timedelta(days=-1)
            schedDictB2['rotation'] = bottoms[1]
            schedDictB2['bottom'] = 1
            resDict[AmionName]['schedule'].append(schedDictB1)
            resDict[AmionName]['schedule'].append(schedDictB2)
            item.pop(length - 1)
        else:
            schedDictB['block'] = i+1
            schedDictB['startDate'] = blockStarts[i+1]
            schedDictB['stopDate'] = blockStops[i+1]
            schedDictB['rotation'] = bottom
            schedDictB['bottom'] = 1
            resDict[AmionName]['schedule'].append(schedDictB)
    if schedDict != {}:
        resDict[AmionName]['schedule'].append(schedDict)


'''
This is getting close to working! It handles Ainsworth & Arora's schedules but
fails on Balkin.
I think I should re-do all the date change logic before & take advantage of the
block #. Get all the block numbers together and slide the bottom around to fill
the gaps, including to create a new bottom entry for rare, but possible cases
where they may be discontinuous.
'''

print len(resDict[AmionName]['schedule'])
for rot in  resDict[AmionName]['schedule']:
    print rot

for number in range(12,13):
    cellBlock = []
    cellTops = []
    cellBottoms = []
    blockStart = blockStarts[number]
    blockStop = blockStops[number]
    topDates = []
    for rotation in resDict[AmionName]['schedule']:
        if rotation['block'] == number:
            if rotation['bottom'] == 1:
                cellBottoms.append(rotation)
            elif rotation['bottom'] == 0:
                cellTops.append(rotation)
            for top in cellTops:
                print top
                topDates.append(top['startDate'])
                topDates.append(top['stopDate'])
    if len(topDates) > 0:
        print topDates
        print cellTops
        print cellBottoms
    # if len(cellBottoms) == 1:

    # elif len(cellBottoms) == 2:

    else: print 'wtf'


print ''
'''
This is the output from that loop:
[datetime.date(2016, 5, 2), datetime.date(2016, 5, 8)]
[]
[datetime.date(2016, 5, 9), datetime.date(2016, 5, 15)]
[]
[datetime.date(2016, 5, 30), datetime.date(2016, 6, 5)]
[]
Looks like cellBottoms is empty every time which definitely should not be
happening, but I ain't sure why yet.
'''

'''
if rotation['bottom'] == 0:
startD = rotation['startDate']
stopD = rotation['stopDate']
block = rotation['block']
for rot2 in resDict[AmionName]['schedule']:
    if rot2['bottom'] == 1 and block == rot2['block']:
        if rot2['startDate'] == startD: pass
        elif rot2['startDate'] < startD and rot2['stopDate'] >= stopD:
            # print rotation
            rot2['stopDate'] = startD - DT.timedelta(days=1)
        # elif rot['startDate']
'''
# print resDict
# print len(resDict[AmionName]['schedule'])
# for rot in  resDict[AmionName]['schedule']:
    # print rot

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

#################################################################################
### Failed bs experiments
#################################################################################
'''
This is close to working, but it hasn't solved the complex in-cell dates
        problem. Right now, it's double booking for those.
        I think I need to do a tree of if statements. Move this date parsing for
        B to the end of the loop (below this for loop) & only run that if there
        is no top line(s).
        If there is/are top lines, keep the bottom name parsing but do if
        statements through the dates using the dict lookups to get all the dates
        & rotations in the same list so they can be sorted out.

        Actually, no, you can keep those but don't append to resDict yet.
        - Start assuming the bottoms fill the month then clip away by iterating
        through. Maybe?
        - Look at Rachel's block 1. She's the most complex case with only 1
        thing in bottom and 3 upper lines.
        I dunno. It's a complex mess. Maybe you should just toss all dates &
        rotations into sets and sort them independently. But look at Alanna
        block 1. She has E-Sed in 2 pieces.
        White board it before coding or you'll go mad.

        Or maybe adjusting resDict after the fact is the way to go. You would
        however, have to encode a bottom flag so you know which is the parent
        rotation that has to adjust size.
        As I think about it, I think that's the way to go. Structuring that as
        a loop will require some thought. I think it needs an outer loop that
        iterates through the list, then inner loops that compare the startDate
        to every other start date, then the stopDate to every other stopDate:
            for rotation in resDict:
                startD = rotation['startDate']
                for others in resDict:
                    if others['startDate'] == startD: something
            This may require popping rotations on the fly temporarily to avoid
            comparing to self or just saying if rotation['rotation'] ==: pass
# This works to get all the text but it loses the cell structure
for string in soup.strings:
    print string
'''

# td1 = soup.td
# print td1 # <td style="border-color:#cccccc; border-collapse:collapse;">Ainsworth-A=</td>
# cell = td1.string
# print cell #Ainsworth-A

'''
rowList = []
# print soup
el1 = soup.td
print el1.name
print type(el1)
if el1.name == 'td': print el1.string
children = el1.descendents
if children == None:
    rowList.append(el1.string)
    nextTag = el1.next_sibling
else:
    pass
print nextTag
print rowList
'''
'''
This has been an hellish nightmare, but I think I'm on the right track. I
really need to walk through the table 1 tag at a time (in a loop).
- Grab a tag in the row
- If there's text in a td tag, keep that text
- If there's not, grab the text from the descendent tags. These have no rhyme or
reason, unfortunately. They are all over the place, font, nobr, b and often
different fragments among them. It sucks bigtime. I don't know how to parse that
text even after I get it.

This code above is finally starting to come together. tag.name gives the html
tag name (td, a, nobr, etc)
tag.string is the text content but only of that tag, not its descendents
tag.descendents == None if there's only text in the tag

bs4 examples use nested for loops to descend through tags until one reaches
descendents == None

Actually, what might work even more easily is a combo re + bs
for line (ie row), can re search for <td.+?</td>  That will get the whole tag
Can pass that tag as a soup object and grab all the strings either in bulk, doing a
find_all(True) or whatever.
'''



'''
rowall = soup.find_all(['td']) #, 'font', 'nobr', 'b'])
for tag in rowall:
    # print type(tag)
    if tag.contents != []: rowList.append(tag.contents[0])
    else:
        print tag
        inner = tag.find_all(['font', 'nobr'])
        print inner
        #children = tag.descendants
        #for child in children:
        #    print child
    #if tag.string != 'None': print tag.string
    #else: "print miss"
print rowList
'''
'''
rowall = soup.find_all(['td', 'font', 'nobr', 'b'])
# print rowall
rowList = []
for item in rowall:
    if item[:2] == '<td': rowList.append(item.string)
    if item.string == None: print 'line'
'''
'''
for l in soup.findAll('td'):
    if l.find('sup'):
        l.find('sup').extract()
    print l.getText(),'|',
'''
'''
for i in range(15):
    td2 = td1.next_element
    print td2
    td1 = td2
'''
'''
# print (soup.prettify())
tds = soup.find_all('td')
# print tds
print tds[0]

tds2 = soup.td
print type(tds2)
print tds2
print tds2.children
for td in tds2:
    print type(tds)
    print td
'''
'''
for i, cell in enumerate(tds):
    tdList = []
    print cell.contents
    print cell.descendants
'''
'''
tds = soup.findAll('font')
for i, cell in enumerate(tds):
    resList = []
    print cell.string
tds = soup.findAll('nobr')
for i, cell in enumerate(tds):
    resList = []
    print cell.string
'''
'''
This is great! Except it leaves out all those ridiculous split blocks. They
seem to be in font or nobr tags.
I think if I search for all 3 tags, store them in order by resident & then
merge them together, it should work.
'''
fh.close()
