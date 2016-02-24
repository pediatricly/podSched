#! /usr/bin/python26
import csv
import datetime as DT
import os.path
from allResStr import allRes as allRes
# from shalStr import aString as allRes
from allResStr import blockStarts23
from allResStr import blockStops23
from allResStr import blockStarts1
from allResStr import blockStops1
from blockUtils import blockLookup
from allResStr import updated
#########################################################
### Define Globals
##########################################################
try: version = os.path.basename(__file__)
except: version = 'confAttendCGItest.py'
# Parameters
########## CRITICAL #############
firstBlock = 8 # CRITICAL - choose blocks to analyze
lastBlock = 11 # CRITICAL - choose blocks to analyze

########## Important but not so likely to change #############
csvDirName = 'badgeScanCSVs'
badgeDir = 'badgeDir.csv'
confByWeek = 'conferencesByWeek.csv'
csvOutFile = 'confAttendOut.csv'
today = DT.date.today()
todayStr = today.isoformat()

message = ''
errMessage = ''
# Used just 1, now set start times individually for every weekday. Uses the
# Python date.weekday() function where Mon = 0, Fri = 4. These are assembled
# into dicts of tupules of datetime objects in the loops below.
amStartsIn = {0:(8,0), 1:(8,15), 2:(8,0), 3:(8,15), 4:(8,0)}
amTol = 60 # Tolerance for what you'll call an AM conf time stamp, in MINUTES
noonStartsIn = {0:(12,0), 1:(12,0), 2:(12,0), 3:(12,0), 4:(12,0)}
noonTol = 60 # Tolerance for what you'll call an noon conf time stamp, in MINUTES

########## Will probably never change these #############
classes = [1,2,3]
classesStr =''
increment = DT.timedelta(7) # Counts up conferences expected going by weeks

# These setup the csv output
headers1 = ['Blocks:']
headers2 = ['AmionName']
headers2pattern = ['AM Attended', 'AM Expected', 'AM %', 'Avg Min Late',
                   'Noon Attended', 'Noon Expected', 'Noon %', 'Avg Noon Min Late']
###############################################################################
### CGI Setup
################################################################################
import cgi
import cgitb
print 'Content-Type: text/html\r\n\r\n'
cgitb.enable()
form = cgi.FieldStorage() # instantiate only once!

# try:
    # Get the split dates from CGI, default to previous if none entered
firstBlockIn = form.getfirst('firstBlock', '')
lastBlockIn = form.getfirst('lastBlock', '')
classesIn = form.getlist('classI')
# except:
    # print '<h1>Whoa! Something went wrong with the data entry!</h1>'
    # print '<h1>If you are seeing this message, please double the data you entered, the output summary below and try again. If you still get this error, contact Mike. :(</h1>'
    # Avoid script injection escaping the user input

if firstBlockIn != '':
    firstBlock = int(cgi.escape(firstBlockIn))
    message += 'Used your first block selection %d' % firstBlock
else: message += 'Used default first block %d' % firstBlock
if lastBlockIn != '':
    lastBlock = int(cgi.escape(lastBlockIn))
    message += 'Used your last block selection %d' % lastBlock
else: message += 'Used default last block %d' % lastBlock


print str(firstBlock) + '<br>'
print str(lastBlock) + '<br>'

if len(classesIn) > 0:
    classes = []
    for classI in classesIn:
        classI = int(cgi.escape(classI))
        classes.append(classI)
        classesStr += str(classI)
    message += 'Used your classes selection %s' % classesStr
else:
    for classI in classes:
        classesStr += str(classI)
        message += 'Used default classes %s' % classesStr
print classesStr + '<br>'

############  File Upload ###################################
fileStrs = ['confCSV1', 'confCSV2', 'confCSV3', 'confCSV4', 'confCSV5', 'confCSV6', 'confCSV7']
for i, fileStr in enumerate(fileStrs):
    fileitem = form[fileStr]

    # Test if the file was uploaded
    if fileitem.filename:

        # strip leading path from file name
        # to avoid directory traversal attacks
        fn = os.path.basename(fileitem.filename)
        pathName = os.path.join(csvDirName,'log_'+todayStr+'_'+str(i+1)+'.csv')
        open(pathName, 'wb').write(fileitem.file.read())
        message = ('The file "' + fn + '" was uploaded successfully and saved as '
                   + pathName)
    else:
        message = 'No new badge log file was uploaded'
