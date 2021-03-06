#! /usr/bin/python26
import csv
import datetime as DT
import os.path
from string import Template
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
firstBlock = 1 # CRITICAL - choose blocks to analyze
lastBlock = 13 # CRITICAL - choose blocks to analyze

########## Important but not so likely to change #############
csvDirName = 'badgeScanCSVs'
badgeDir = 'badgeDir.csv'
confByWeek = 'conferencesByWeek.csv'
csvOutFile = 'confAttendOut.csv'
title = 'Conference Attendance'
subtitle = 'Results'
frameTemplate = 'elNinoFrame.html'
htmlTemplate = 'confAttendTemplate.html'
filesInF = 'filesIn.txt'
today = DT.date.today()
todayStr = today.isoformat()

message = ''
errMessage = ''
errRots = []
errRotStr = '<tr><th>Resident</th><th>Block</th><th>Rotation</th></tr>'
errRotStrOrig = '<tr><th>Resident</th><th>Block</th><th>Rotation</th></tr>'
filesIn = '<tr><th>CSV Filename</th></tr>'
badgeErrs = '<tr><th>Date</th><th>Unrecognized Badges</th></tr>'
# Used just 1, now set start times individually for every weekday. Uses the
# Python date.weekday() function where Mon = 0, Fri = 4. These are assembled
# into dicts of tupules of datetime objects in the loops below.
amStartsIn = {0:(8,0), 1:(8,30), 2:(8,0), 3:(8,30), 4:(8,0)}
amTol = 60 # Tolerance for what you'll call an AM conf time stamp, in MINUTES
amStr = '<tr><th>Day of Week</th><th>Time</th></tr>'
noonStartsIn = {0:(12,15), 1:(12,15), 2:(12,15), 3:(12,15), 4:(12,15)}
noonTol = 60 # Tolerance for what you'll call an noon conf time stamp, in MINUTES
noonStr = '<tr><th>Day of Week</th><th>Time</th></tr>'

########## Will probably never change these #############
classes = [1,2,3]
classesStr =''
increment = DT.timedelta(7) # Counts up conferences expected going by weeks

# These setup the csv output
headers1 = ['Blocks:']
headers2 = ['AmionName']
headers2pattern = ['AM Attended', 'AM Expected', 'AM %', 'Avg Min Late',
                   'Noon Attended', 'Noon Expected', 'Noon %', 'Avg Noon Min Late']
superSeniors = ['Wasio-L', 'Haluck,Ning', 'Scahill-M', 'Thein-K', 'Bares-A',
                'Sznewajs,Aimee']
###############################################################################
### CGI Setup
################################################################################
import cgi
import cgitb
print 'Content-Type: text/html\r\n\r\n'
# cgitb.enable()
form = cgi.FieldStorage() # instantiate only once!

# try:
    # Get the split dates from CGI, default to previous if none entered
firstBlockIn = form.getfirst('firstBlock', '')
lastBlockIn = form.getfirst('lastBlock', '')
classesIn = form.getlist('classI')
fileStrs = ['confCSV1', 'confCSV2', 'confCSV3', 'confCSV4', 'confCSV5', 'confCSV6', 'confCSV7']
# except:
    # print '<h1>Whoa! Something went wrong with the data entry!</h1>'
    # print '<h1>If you are seeing this message, please double the data you entered, the output summary below and try again. If you still get this error, contact Mike. :(</h1>'
    # Avoid script injection escaping the user input

if firstBlockIn != '':
    firstBlock = int(cgi.escape(firstBlockIn))
    message += 'Used your first block selection %d.<br>' % firstBlock
else: message += 'Used default first block %d.<br>' % firstBlock
if lastBlockIn != '':
    lastBlock = int(cgi.escape(lastBlockIn))
    message += 'Used your last block selection %d.<br>' % lastBlock
else: message += 'Used default last block %d.<br>' % lastBlock

if len(classesIn) > 0:
    classes = []
    for classI in classesIn:
        classI = int(cgi.escape(classI))
        classes.append(classI)
        classesStr += str(classI)
    message += 'Used your classes selection %s.<br>' % classesStr[:-2]
else:
    for classI in classes:
        classesStr += str(classI) + ', '
    message += 'Used default classes %s.<br>' % classesStr[:-2]

############  File Upload ###################################
fileCount = 0
for i, fileStr in enumerate(fileStrs):
    fileitem = form[fileStr]

    # Test if the file was uploaded
    if fileitem.filename:

        # strip leading path from file name
        # to avoid directory traversal attacks
        fn = os.path.basename(fileitem.filename)
        pathName = os.path.join(csvDirName,'log_'+todayStr+'_'+str(i+1)+'.csv')
        open(pathName, 'wb').write(fileitem.file.read())
        message += ('The file "' + fn + '" was uploaded successfully and saved as '
                   + pathName + '.<br>')
        fileCount += 1
if fileCount == 0: message += 'No new badge log files uploaded.<br>'
##########################################################
masterSet = set()
prelimList = []
cleanDict = {}
inputFiles = []
badgeDict = {}
wkData = {}
data = {}
errList =[]

##########################################################
# Do this round-about datetime object thing to save the hassle of parsing time.
# Need datetime objects to utilize timedelta
amStarts = {}
for day in amStartsIn:
    hour = amStartsIn[day][0]
    minute = amStartsIn[day][1]
    amConfStart = DT.datetime(2016,1,1,hour,minute,0)
    amCutoffPre = amConfStart - DT.timedelta(minutes=amTol)
    amCutoffPost = amConfStart + DT.timedelta(minutes=amTol)
    amConfStart = DT.time(amConfStart.hour,amConfStart.minute)
    amCutoffPre = DT.time(amCutoffPre.hour, amCutoffPre.minute)
    amCutoffPost = DT.time(amCutoffPost.hour, amCutoffPost.minute)
    amStarts[day] = (amConfStart, amCutoffPre, amCutoffPost)
    amStr += '<tr><td>' + str(day) + '</td><td>' + str(amConfStart.strftime('%H:%M')) + '</td></tr>'

noonStarts = {}
for day in noonStartsIn:
    hour = noonStartsIn[day][0]
    minute = noonStartsIn[day][1]
    noonConfStart = DT.datetime(2016,1,1,hour,minute,0)
    noonCutoffPre = noonConfStart - DT.timedelta(minutes=noonTol)
    noonCutoffPost = noonConfStart + DT.timedelta(minutes=noonTol)
    noonConfStart = DT.time(noonConfStart.hour,noonConfStart.minute)
    noonCutoffPre = DT.time(noonCutoffPre.hour, noonCutoffPre.minute)
    noonCutoffPost = DT.time(noonCutoffPost.hour, noonCutoffPost.minute)
    noonStarts[day] = (noonConfStart, noonCutoffPre, noonCutoffPost)
    noonStr += '<tr><td>' + str(day) + '</td><td>' + str(noonConfStart.strftime('%H:%M')) + '</td></tr>'

#########################################################
### Read the dir of CSVs
##########################################################
directory = os.listdir(csvDirName)
for filename in directory:
    pathName = os.path.join(csvDirName, filename)
    if pathName[-4:] == '.csv':
        inputFiles.append(filename)
        fh = open(pathName, 'rb')
        reader = csv.reader(fh, delimiter=',')
        for row in reader:
            tupule = (row[0], row[1])
            masterSet.add(tupule)
        fh.close()
        filesIn += '<tr><td>' + filename + '</td></tr>'

#########################################################
### Parse the CSVs, mostly for timestamps
##########################################################
for item in masterSet:
    timeStamp = item[0]
    split1 = timeStamp.split(' ')
    date1 = split1[0]
    slash1 = date1.find('/')
    slash2 = date1.find('/', slash1+1)
    date = DT.date(int(date1[slash2+1:])+2000, int(date1[:slash1]), int(date1[slash1+1:slash2]))
    wkday = date.weekday()
    amConfStartI = amStarts[wkday][0]
    amCutoffPreI = amStarts[wkday][1]
    amCutoffPostI = amStarts[wkday][2]
    noonConfStartI = noonStarts[wkday][0]
    noonCutoffPreI = noonStarts[wkday][1]
    noonCutoffPostI = noonStarts[wkday][2]
    ap = split1[2]
    time1 = split1[1]
    colon1 = time1.find(':')
    colon2 = time1.find(':', colon1+1)
    if ap == 'PM' or ap =='pm':
        if int(time1[:colon1]) == 12: #Noon is PM but should not have 12 added
            time = DT.time(int(time1[:colon1]), int(time1[colon1+1:colon2]), int(time1[colon2+1:]))
        else: #Other PM times needs conversion to 24-hr
            time = DT.time(int(time1[:colon1])+12, int(time1[colon1+1:colon2]), int(time1[colon2+1:]))
    else:
        if int(time1[:colon1]) == 12: #Unlikely midnight event, hour = 0
            time = DT.time(0, int(time1[colon1+1:colon2]), int(time1[colon2+1:]))
        else: #All other AMs are just the hour
            time = DT.time(int(time1[:colon1]), int(time1[colon1+1:colon2]), int(time1[colon2+1:]))
    tempDict = {'date':date, 'time': time, 'badge':item[1]}

    if time <= amCutoffPostI and time >= amCutoffPreI:
        tempDict['conf'] = 'am'
        hrLate = time.hour - amConfStartI.hour
        if hrLate < 0: minLate = 0
        else:
            minLate = max(time.minute - amConfStartI.minute, 0)
            minLate = minLate + hrLate*60
        tempDict['minLate'] = minLate
    elif time <= noonCutoffPostI and time >= noonCutoffPreI:
        tempDict['conf'] = 'noon'
        hrLate = time.hour - noonConfStartI.hour
        if hrLate < 0: minLate = 0
        else:
            minLate = max(time.minute - noonConfStartI.minute, 0)
            minLate = minLate + hrLate*60
        tempDict['minLate'] = minLate
    else: tempDict['conf'] = 'unknown'

    prelimList.append(tempDict)

# print prelimList # {'date': datetime.date(2016, 1, 25), 'minLate': 4, 'badge':
# '21378801448437', 'conf': 'am', 'time': datetime.time(8, 4, 7)}

#########################################################
### Get rid of duplicates from multiple scans of the same badge at same conference
##########################################################
def dupToss(item, listOfDicts):
    for e2 in listOfDicts:
        if (e2['badge'] != item['badge'] and e2['date'] != item['date'] and
            e2['time'] != item['time']): continue
        else:
            if (e2['badge'] == item['badge'] and e2['date'] == item['date'] and
                item['time'] > e2['time']): return None
            else: continue
    return item

key = 1 # Really does nothing but makes the final dict a bit cleaner
for item in prelimList:
    result = dupToss(item, prelimList)
    if result != None:
        cleanDict[key] = result
        key += 1
# print len(masterSet)
message += 'Processed ' + str(len(cleanDict)) + ' unique badge scans.<br>'
# print cleanDict
# {1: {'date': datetime.date(2015, 12, 31), 'badge': '21378800165594', 'conf':
#      'unknown', 'time': datetime.time(14, 30, 58)},
#  2: {'date': datetime.date(2016, 1, 6), 'badge': '21378800254778', 'conf':
#      'unknown', 'time': datetime.time(15, 21, 8)}...
# }
################################################################################
### Parse badge #s to names and lookup rotations & blocks
################################################################################

# Read in the badge file
# CAREFUL - the relevant headers NEED to be AmionName and badgeCode
fh = open(badgeDir, 'rb')
reader = csv.DictReader(fh)
for row in reader:
    if row['AmionName'] != '':
        badgeDict[row['AmionName']] = row
fh.close()
message += "Used badge info (list of residents' badge numbers) from " + badgeDir + '.<br>'
# print badgeDict
# {'Simmons-R': {'Category 15-16': 'PGY-1', 'Name First': 'Roxanne', 'Name Middle':
              # 'Lynn', 'ID Number (employee)': '22157878', 'AmionName':
              # 'Simmons-R', 'Library': '21378801448544', 'badgeCode':
              # '21378801448544', 'Pager (current)': '415-443-6611',
              # 'Name Last': 'Simmons', 'email': 'Roxanne.Simmons@ucsf.edu'},
 # 'Links-B': {'Category 15-16': 'PGY-2', 'Name First': 'Elizabeth', 'Name Middle':
            # 'Rachel', 'ID Number (employee)': '28868826', 'AmionName':
            # 'Links-B', 'Library': '21378801218707', 'badgeCode':
            # '21378801218707', 'Pager (current)': '415-443-5784', 'Name Last':
            # 'Links', 'email': 'Elizabeth.Links@ucsf.edu'},...
 # }

# Lookup AmName by badge & rotation/block by AmName
# Returns 'Not Found' for AmName if the badge isn't in the directory (there is
# an unusual number of what look like fragmented badge #s in the history)
# and then '', '' for rotation & block if any aren't found. This happens both
# for those badge # frags and for tests / med student badges, etc.
for key in cleanDict:
    cleanDict[key]['AmionName'] = 'Not Found'
    badge = cleanDict[key]['badge']
    for res in badgeDict:
        if badge == badgeDict[res]['badgeCode']:
            cleanDict[key]['AmionName'] = badgeDict[res]['AmionName']
    AmName = cleanDict[key]['AmionName']
    eventDate = cleanDict[key]['date']
    try: tupule = blockLookup(eventDate, AmName, allRes)
    except KeyError: tupule = ('','')
    cleanDict[key]['rotation'] = tupule[1]
    cleanDict[key]['block'] = tupule[0]

# for key in cleanDict:
    # print cleanDict[key]
# {{'minLate': 46, 'AmionName': 'Shalen-J', 'conf': 'am', 'time':
 # datetime.time(8, 46, 4), 'date': datetime.date(2016, 1, 26), 'rotation':
 # 'PURPLE1', 'badge': '21378800976610', 'block': 8}
# {'minLate': 4, 'AmionName': 'Yang-E', 'conf': 'am', 'time':
 # datetime.time(8, 4, 7), 'date': datetime.date(2016, 1, 25), 'rotation':
 # 'PURPLE1', 'badge': '21378801448437', 'block': 8}
# }


################################################################################
### Read in the expected conference data
################################################################################
fh = open(confByWeek, 'rb')
reader = csv.DictReader(fh)
for row in reader:
    rot = row['Rotation']
    amWk = float(row['AM'])
    noonWk = float(row['Noon'])
    wkData[rot] = {'amWk':amWk, 'noonWk':noonWk}
fh.close()
# print wkData
# {'PIC': {'amWk': 0.0, 'noonWk': 0.0}, 'SFO2': {'amWk': 0.0, 'noonWk': 0.0},..}

blocks = [x for x in range(firstBlock, lastBlock+1)]

#########################################################
### Build the data dict starting with the expected data
##########################################################
# This loop just sets up the dict with attendance = 0
for res in allRes:
    resDict = {}
    for block in blocks:
        resDict[block] = {'actual' : {'am': 0, 'amLate': 0, 'noon': 0, 'noonLate':0},
                          'expected' : {'am': 0, 'noon': 0}}
                          # 'expected' : {'am': 0, 'amLate': 0, 'noon': 0, 'noonLate':0}}
    if allRes[res]['pgy'] in classes:
        data[res] = resDict
# print data
##########################################################
### Then calculate expected attendance by rotation (near identical to lunchMoney)
##########################################################
for pgyYr in classes:
    if pgyYr == 1:
        starts = blockStarts1
        stops = blockStops1
    else:
        starts = blockStarts23
        stops = blockStops23

    day1 = DT.datetime.strptime(starts[firstBlock], '%Y-%m-%d')
    firstMon = day1 + DT.timedelta(days=(7-day1.weekday()))# - increment
    endDay = DT.datetime.strptime(stops[lastBlock], '%Y-%m-%d')

    for res in allRes:
        if res != 'co' and res != 'u':
            if allRes[res]['pgy'] == pgyYr:
                if day1.weekday() != 0:
                # This if branch adjusts for ff day1 is not Monday ->
                # grab that first partial week as it if were whole and calculate >
                # Then increment tracker and proceed.
                # Without this, every R2/3 has this odd missing lookup when it
                # tries to see what rotation they were on in June
                    tupule = blockLookup(day1, res, allRes)
                    block = tupule[0]
                    rotation = tupule[1]
                    try:
                        amWk = wkData[rotation]['amWk']
                        noonWk = wkData[rotation]['noonWk']

                    except:
                        amWk = 0
                        noonWk = 0
                        thruple = (res, tupule)
                        errRots.append(thruple)
                    try:
                        data[res][block]['expected']['am'] += amWk
                        data[res][block]['expected']['noon'] += noonWk
                    except: pass
                    tracker = firstMon
                else: #If day1 is Monday, just roll through the normal loop
                    tracker = day1
                # tracker = tracker + DT.timedelta(7)
                while (tracker < endDay):
                    tupule = blockLookup(tracker, res, allRes)
# rotTest = blockLookup('2016-01-20', 'Sun-V', allRes)
# print rotTest # returns 'ORANGE3'
                    block = tupule[0]
                    rotation = tupule[1]
                    # These try blocks allow skipping empty cells, eg, partial year
                    # super seniors. Prints those output for you to check
                    try:
                        amWk = wkData[rotation]['amWk']
                        noonWk = wkData[rotation]['noonWk']
                    except:
                        amWk = 0
                        noonWk = 0
                        thruple = (res, tupule)
                        errRots.append(thruple)
                        # print res, tupule
                    try:
                        data[res][block]['expected']['am'] += amWk
                        data[res][block]['expected']['noon'] += noonWk
                        # print tracker
                        # print block
                        # print rotation
                        # print data[res][block]['expected']['am']
                        # print data[res][block]['expected']['noon']
                    except: pass
                    tracker = tracker + increment
# print data['Ainsworth-A']
# {'Simmons-R': {8: {'expected': {'amLate': 0, 'noon': 24.0, 'am': 40.0, 'noonLate': 0},
#                      'actual': {'amLate': 0, 'noon': 0, 'am': 0, 'noonLate': 0}},
#                9: {'expected': {'amLate': 0, 'noon': 12.0, 'am': 20.0, 'noonLate': 0},
#                    'actual': {'amLate': 31, 'noon': 0, 'am': 2, 'noonLate': 0}},
#                6: {'expected': {'amLate': 0, 'noon': 0.0, 'am': 0.0, 'noonLate': 0},
#                    'actual': {'amLate': 0, 'noon': 0, 'am': 0, 'noonLate': 0}},
#                7: {'expected': {'amLate': 0, 'noon': 24.0, 'am': 40.0, 'noonLate': 0},
#                    'actual': {'amLate': 0, 'noon': 0, 'am': 0, 'noonLate': 0}}
#  ...}...}

#########################################################
### Read the actual timestamp data into the resident data dict
##########################################################

for event in cleanDict:
    AmName = cleanDict[event]['AmionName']
    if AmName == 'Not Found':
        errList.append(cleanDict[event])
    else:
        blockI = cleanDict[event]['block']
        confI = cleanDict[event]['conf']
        if blockI == '' or confI == 'unknown': pass
            # errList.append(cleanDict[event])
            # This commented line above used to put these in errList, but most of
            # these seem to be chiefs and superseniors testing badges, so I don't
            # know if it's useful. Leaving it off for production as of 24Feb16.
        else:
            # This try, except block is crucial to prevent errors. If you set
            # block range small but have events outside that range, they produce
            # key errors here.
            try:
                minLateI = cleanDict[event]['minLate']
                if confI == 'am':
                    data[AmName][blockI]['actual']['am'] += 1
                    data[AmName][blockI]['actual']['amLate'] += minLateI
                elif confI == 'noon':
                    data[AmName][blockI]['actual']['noon'] += 1
                    data[AmName][blockI]['actual']['noonLate'] += minLateI
            except KeyError: pass
# print data['Ainsworth-A']

# Calculate % actual out expected. Easier here than in Excel.
for res in data:
    for block in data[res]:
        try:
            data[res][block]['actual']['amLate'] = data[res][block]['actual']['amLate'] / data[res][block]['actual']['am']
        except ZeroDivisionError:
            data[res][block]['actual']['amLate'] = '-'
        try:
            data[res][block]['actual']['noonLate'] = data[res][block]['actual']['noonLate'] / data[res][block]['actual']['noon']
        except ZeroDivisionError:
            data[res][block]['actual']['noonLate'] = '-'
# print data['Shalen-J']

#########################################################
### Write the output data CSV
##########################################################
# These 2 blocks generate the multilevel headers to keep them aligned by blocks
headers1suffix = [x for x in blocks for y in range(len(headers2pattern))]
for item in headers1suffix:
    headers1.append(item)

for y in range(firstBlock, lastBlock+1):
    for item in headers2pattern:
        headers2.append(item)

# Then write the data in a readable order to csv
with open(csvOutFile, 'wb') as csvOut:
    writer = csv.writer(csvOut, delimiter=',')
    writer.writerow(headers1)
    writer.writerow(headers2)
    for res in sorted(data):
        row = [res]
        for block in blocks:
            row.append(data[res][block]['actual']['am'])
            row.append(data[res][block]['expected']['am'])
            try: row.append(data[res][block]['actual']['am'] / data[res][block]['expected']['am'])
            except: row.append('-')
            row.append(data[res][block]['actual']['amLate'])

            row.append(data[res][block]['actual']['noon'])
            row.append(data[res][block]['expected']['noon'])
            try: row.append(data[res][block]['actual']['noon'] / data[res][block]['expected']['noon'])
            except: row.append('-')
            row.append(data[res][block]['actual']['noonLate'])
        writer.writerow(row)
    message += 'Wrote data summary to ' + csvOutFile + '.<br>'

with open(filesInF, 'wb') as filesInFH:
    filesInFH.write(filesIn)
    filesInFH.write('\n')
# print data
#########################################################
### Convert the output data to HTML
##########################################################
for err in errRots:
    errRes = err[0]; errTupule = err[1]
    if errRes not in superSeniors:
        errBlock = errTupule[0]; errRot = errTupule[1]
        errRotStr += '<tr><td>' + errRes + '</td><td>' + str(errBlock) + '</td><td>' + errRot + '</td></tr>'
if errRotStr == errRotStrOrig:
    errRotStr += '<tr><td>' + 'No errors!' + '</td><td>' + '' + '</td><td>' + 'Boom!' + '</td></tr>'
for err in errList:
    dateJ = err['date']
    dateJ = dateJ.isoformat()
    badgeErrs +=  '<tr><td>' + dateJ + '   |</td><td>' + str(err['badge']) + '</td></tr>'

try:
################################################################################
### Output to html (or print to stdout)
################################################################################
    templateVars = dict(message=message, csvOutFile=csvOutFile, filesInF=filesInF,
                        confByWeek=confByWeek, updated=updated,
                        amStr=amStr, noonStr=noonStr, badgeErrs=badgeErrs,
                        classesStr=classesStr, firstBlock=str(firstBlock),
                        lastBlock=str(lastBlock), filesIn=filesIn,
                        errRotStr=errRotStr)
    main = ''
    with open(htmlTemplate, 'r') as temp:
        htmlTemp = temp.read()
        main = Template(htmlTemp).safe_substitute(templateVars)

    templateVars = dict(version=version, title=title, subtitle=subtitle, main=main
                    )
    with open(frameTemplate, 'r') as temp:
        htmlTemp = temp.read()
        finalHTML = Template(htmlTemp).safe_substitute(templateVars)
        print finalHTML

except:
    print '<h1>Whoa! Something went wrong with the data output!</h1>'
    print '<h1>If you are seeing this message, please double check any dates you entered, the output summary below (resident names, etc) and try again. If you still get this error, contact Mike. :(</h1>'
