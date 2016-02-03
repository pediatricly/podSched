import requests
import re

urlStub = "http://amion.com/cgi-bin/ocs"
payload = {'login' : 'ucsfpeds'}
payload2 = {'File': '', 'Page':'Block', 'Fsiz':'-2', 'Sbcid':'6',
            'Blks':'0-0'}
skills = {2: '', 3: '', 4:''}

def AmionBlockScraper(url, load, load2, skillsDict):
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
        load2['File'] = fileStub
    else: print "whoa - regex found nothing"

    load.update(load2)

    for skill in skillsDict:
        load['Skill'] = skill
        rI = requests.post(urlStub, data=load)
        htmlI = rI.text
        skillsDict[skill] = htmlI

        return skillsDict

result = AmionBlockScraper(urlStub, payload, payload2, skills)
print result[2]






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
