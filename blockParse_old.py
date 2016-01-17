'''
Working! I need to head to the strip club but this is basically solved. Those
diff of sets statements at the bottom are the start & end dates the bottoms
should be adjusted to.
The only extra setp is to put in some logic that allows creation & append of a
new "rotation" with same block & name but with the seond set of start/stop dates
should they exist. (This is probably super rare but could become common in 6 wk
blocks. Although, I think my cards rotation was discontinuous around PLUS?)

**Actually, I bet it's easily solved using max / min functions.
No, even better, just put all possible start dates in a list:
    [bottom start date, top end dates + 1]
    and whatever is not already a top start date is a bottom start date.
    Then just sort out the rare situation where they may be discontinuous bottom
'''

'''
for number in range(12,13):
    cellBlock = []
    topDates = []
    if len(topDates) > 0:
        print topDates
        print cellTops
        print cellBottoms
    # if len(cellBottoms) == 1:

    # elif len(cellBottoms) == 2:

    else: print 'wtf'
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

