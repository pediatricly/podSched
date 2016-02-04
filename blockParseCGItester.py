#! /usr/bin/python26

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
try:
    from bs4 import BeautifulSoup as bs
except: cgitb.handler()
import datetime as DT
################################################################################
### CGI Setup
################################################################################
import cgi
import cgitb
cgitb.enable()
print 'Content-Type: text/html\r\n\r\n'
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


print '<h1>Hello World!</h1>'

