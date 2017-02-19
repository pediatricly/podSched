#! /usr/bin/python26
print 'Content-Type: text/html\r\n\r\n'
import datetime as DT
import sys
import re
import requests
from bs4 import BeautifulSoup as bs
import lxml
import cgitb
# cgitb.enable()

urlStub = "http://amion.com/cgi-bin/ocs"
payload = {'login' : 'ucsfpeds'}
skills = {'2': '', '3': '', '4':''}

# Found in June '16 that Amion changes subtly once the new intern schedule gets
# uploaded in early June. This section gets the current academic year (fall) to
# pass into the url in AmionScraper
thisYr = DT.date.today().year
thisMonth = DT.date.today().month
if thisMonth < 7: schedYr = thisYr - 1
else: schedYr = thisYr
SyrParam = 'Syr=' + str(schedYr)
target = '^<TR.+?</tr>'
TDtar = '<td.+?</td>'
yearTar = 'Schedule, (\d\d\d\d).(\d\d\d\d)'
classTar = 'R(\d) Block'

blockStarts = {}
blockStops = {}
blockLens = {}
blockSplits = {}
#################################################################################
load = payload
skillsDict = skills
YrParam = SyrParam
# def AmionBlockScraper(urlStub, load, skillsDict, YrParam):
# First, load the main Amion landing page.
message = ''
f = 0
r = requests.post(urlStub, data=load)
html = r.text # This is outputting the html of the actual schedule landing page
fileStub = ''
# linkTar = '<a href="./ocs?File=.+&Page=Block&Fsiz=..&Sbcid=.">'
# linkTar = '<a href="./ocs?File=.+'
linkTar = '<a href="\./ocs\?File=(.+?)&Page=(.+?)&Fsiz=(.+?)&Sbcid=(.+?)".+?>Block<'
link = re.search(linkTar, html, re.I)
print link.group(1), link.group(2), link.group(3), link.group(4)
FileParam = link.group(1)
PageParam = link.group(2)
FsParam = link.group(3)
SbcParam = link.group(4)
fileStub = '?File=' + FileParam

# soup1 = bs(html)
'''
soup1 = bs(html, 'lxml')
atags = soup1.find_all('a')
for tag in atags:
    print tag
    try: print tag['title']
    except: pass
    print tag.string
    if tag.string == 'Block':
        print tag
        b = tag['href']
        b = b.encode('ascii', 'ignore')
        print b
        fileStub = b.split('?')[1]
        # Updated in June  '16, this allows construction of the url with
        # the year 'Syr' parameter
        params  = fileStub.split('&')
        for param in params:
            if param[:4] == 'File': FileParam = param
            elif param[0:4] == 'Page': PageParam = param
            elif param[0:4] == 'Fsiz': FsParam = param
            elif param[0:4] == 'Sbci': SbcParam = param
            else: pass

        fileStub = '?' + FileParam
    else: print 'not found :('
'''
# Use that filename to construct the links to the class block schedule pages.
# Those links vary only by the skill parameter, hence this loop.
# The html that returns is stored as values in the skillsDict.
for skill in skillsDict:
    htmlI = ''
    # load['Skill'] = str(skill)
    # As above, I initially used urlencode instead of string concatenation,
    # but Amion expects the query string in this specific order.
    url = urlStub + fileStub + '&' + YrParam + '&Page=' + PageParam + '&Skill=' + skill + '&Fsiz=' + FsParam + '&Sbcid=' + SbcParam
    print url
    # The line below gets a different look to the page with that extra
    # parameter Hili, not sure what it does but seems not necessary
    # url = urlStub + fileStub + '&' + YrParam + '&' + PageParam + '&Skill=' + skill + '&' + FsParam + '&Hili=-1&' + SbcParam
    rI = requests.post(url)
    htmlI = rI.text
    skillsDict[skill] = htmlI


        # skillsDict = {'2':'<block page html>...', '3':'<html...>',..}
    # return (skillsDict, message, f)

#################################################################################
#################################################################################
# skillsOut = AmionBlockScraper(urlStub, payload, skills, SyrParam)
# skills = skillsOut[0]
# Find the years from the Amion block page
for skill in skills:
    html = skills[skill]
    # print html
    years = re.search(yearTar, html, re.I)
    fallYr = int(years.group(1))
    print fallYr
    springYr = int(years.group(2))

