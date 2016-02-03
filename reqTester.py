import requests
import re
import urllib

urlStub = "http://amion.com/cgi-bin/ocs"
payload = {'login' : 'ucsfpeds'}
# payload2 = {'File': '', 'Page':'Block', 'Fsiz':'-2', 'Sbcid':'6',
# payload2 = {'File': '', 'Page':'Block', 'Sbcid':'6',
            # 'Blks':'0-0', 'Rsel':'-1'}
skills = {'2': '', '3': '', '4':''}
firstpart = "&Page=Block&Sbcid=6&Skill="
secondpart = '&Rsel=-1&Blks=0-0'

def AmionBlockScraper(url, load, first, second, skillsDict):
    r = requests.post(urlStub, data=load)
    html = r.text # This is outputting the html of the actual schedule landing page
    # print html
    tar = 'cgi-bin/ocs\?Fi=(.+?)[&"]'
    search = re.findall(tar ,html, re.M)
    nameSet = set(); fileStub = ''

    for item in search: nameSet.add(item)
    if len(nameSet) > 1: print "whoa - more than 1 link..."
    elif len(nameSet) == 1:
        fileStub = nameSet.pop().encode('ascii', 'ignore')
    else: print "whoa - regex found nothing"

    for skill in skillsDict:
        htmlI = ''
        load['Skill'] = str(skill)
        url = urlStub + '?File=' + fileStub + first + skill + second
        rI = requests.post(url)
        htmlI = rI.text
        skillsDict[skill] = htmlI

    return skillsDict

result = AmionBlockScraper(urlStub, payload, firstpart, secondpart, skills)
print result['2'][:200]
print result['3'][:200]
print result['4'][:200]
'''
fileStub = result[1]
load3 = {'File': '%2152fc1ad9lwaudangbu', 'Page':'Block', 'Fsiz':'-2', 'Sbcid':'6',
         'Blks':'0-0', 'Rsel':'-1', 'Skill':4, 'login': 'ucsfpeds'}
rI = requests.get(urlStub, data=load3)
htmlI = rI.text
print htmlI[:200]

r2 = requests.get('http://www.amion.com/cgi-bin/ocs?File=!b2fc1bc1rz^xadkj_x&Page=Block&Sbcid=6&Skill=4&Rsel=-1&Blks=0-0')
html2 = r2.text
print html2[:150]
'''


'''
from westValue:
payload = {"login" : "ucsfpeds"}
r = requests.post("http://amion.com/cgi-bin/ocs", data=payload)
html = r.text # This is outputting the html of the actual schedule landing page


from loading the R3 block from homepage:
General:
Request URL:http://amion.com/cgi-bin/ocs?File=!a2fbe090qz^xadkj_x&Page=Block&Fsiz=-2&Sbcid=6
Request Method:GET

Query String Parameters:
File:!a2fbe090qz^xadkj_x
Page:Block
Fsiz:-2
Sbcid:6

Looks like this encoded: File=!a2fbe090qz^xadkj_x&Page=Block&Fsiz=-2&Sbcid=6
'''
