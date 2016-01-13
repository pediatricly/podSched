#! /usr/bin/python

import re
import csv
import string
from bs4 import BeautifulSoup as bs

blockHTML = 'blockR3.html'
fh = open(blockHTML, 'rb')
html = fh.read()

target = '^<TR.+?</tr>'
search = re.findall(target, html, re.M)
# print search[0]

header = search[0]
main = search[1:]
# for line in main:
line = main[0]
# soup = bs(line)

# print line
tar2 = '<td.+?</td>'
se2 = re.findall(tar2, line, re.I)
print len(se2)

rowList = []
for td in se2:
    soup = bs(td)
    if soup.string != None: rowList.append(soup.string)
    else:
        cellList = []
        inners = soup.descendants
        for el in inners:
            if el.string == None: pass
            else:
                cellList.append(el.string)
                rowList.append(cellList)

for cell in rowList:
    print cell

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
