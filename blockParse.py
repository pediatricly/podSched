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
                if item == cellList[i-1]: pass
                else: newList.append(item.strip())
            rowList.append(newList)
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

#    1: DT.date(2015, 7, 1),
#    2: DT.date(2015, 8, 3),
#    3: DT.date(2015, 8, 31),
#    4: DT.date(2015, 9, 28),
#    5: DT.date(2015, 10, 26),
#    6: DT.date(2015, 11, 23),
#    7: DT.date(2015, 12, 21),
#    8: DT.date(2016, 1, 18),
#    9: DT.date(2016, 2, 15),
#    10: DT.date(2016, 3, 14),
#    11: DT.date(2016, 4, 11),
#    12: DT.date(2016, 5, 9),
#    13: DT.date(2016, 6, 6)}

#     1: DT.date(2015, 7, 1),
#     2: DT.date(2015, 8, 3),
#     3: DT.date(2015, 8, 31),
#     4: DT.date(2015, 9, 28),
#     5: DT.date(2015, 10, 26),
#     6: DT.date(2015, 11, 23),
#     7: DT.date(2015, 12, 21),
#     8: DT.date(2016, 1, 18),
#     9: DT.date(2016, 2, 15),
#     10: DT.date(2016, 3, 14),
#     11: DT.date(2016, 4, 11),
#     12: DT.date(2016, 5, 9),
#     13: DT.date(2016, 6, 6)}
#################################################################################
### Read the main (residents) part of the table
#################################################################################

main = table[1:]
# for line in main:
# This is where to build the loop for all resident lines eventually
line = main[0]
se2 = re.findall(TDtar, line, re.I)

rowListI = rowParser(se2)
# for cell in rowListI:
#     print cell

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
resDict = {'AmionName' : AmionName,
           'schedule' : [],
           'CoC' : CoCDict}

for i, item in enumerate(rowListI):
    schedDict = {}
    if type(item) == str:
        schedDict['block'] = i+1
        schedDict['startDate'] = blockStarts[i+1]
        try:
            schedDict['stopDate'] = blockStops[i+1]
        except KeyError:
            schedDict['stopDate'] = blockStops[13] + DT.timedelta(days=1)
# CAREFUL- this doesn't account for intern week off etc. Best to make a
# blockStops dict
        schedDict['rotation'] = item
    elif type(item) == list: pass
# Here's where you parse those lists into dicts

    resDict['schedule'].append(schedDict)

print resDict

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
