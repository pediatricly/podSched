import re
import requests
import datetime as DT

baseUrl = "http://amion.com/cgi-bin/ocs"
AmionLogin = {"login" : "ucsfpeds"}

req0 = requests.post(baseUrl, data=AmionLogin)
html = req0.content

print html
dateTar = '&nbsp;(\w\w\w, \w\w\w \d\d, \d\d\d\d) &nbsp;'
dateI = re.findall(dateTar, html, re.M)[0]
dateI = DT.datetime.strptime(dateI, '%a, %b %d, %Y')
dateI = dateI.date()
print dateI
