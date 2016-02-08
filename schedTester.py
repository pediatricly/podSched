#! /usr/bin/python26
import datetime as DT
from allResStr import allRes as allRes # Local stored dict of whole block sched
message = ''
errMessage = ''
########### CGI Inputs ############################
# Defaults
# AmionNames = ['Sun-V', 'Brim-R', 'Ainsworth-A', 'Pantell-M']
# endDate = DT.date(2016,2,29)
AmionNames = []

try:
    import cgi; import cgitb
    print 'Content-Type: text/html\r\n\r\n'
    cgitb.enable()
    form = cgi.FieldStorage()
except:
    errMessage += 'Whoa! Something went wrong with the CGI initialization.'

try:
    namesIn = form.getlist('namesIn')
    for AmName in namesIn:
        AmionNames.append(cgi.escape(AmName))
    print AmionNames
except: errMessage += 'Whoa! Something went wrong with the Amion Names input.'

try:
    startDateIn = form.getfirst('startDate', '')
    startDateIn = cgi.escape(startDateIn)
    # HTML form brings the whole ISO date format. This strips to just the date.
    startDateIn = startDateIn[:10]
    startDateIn = DT.datetime.strptime(startDateIn, '%Y-%m-%d')
    startDate = startDateIn.date()
    message += 'Used the entered startDate, %s<br>' % startDate
except:
    startDate = DT.date.today() # Default to search from today
    message += 'Used the default startDate<br>'

try:
    endDateIn = form.getfirst('endDate', '')
    endDateIn = cgi.escape(endDateIn)
    # HTML form brings the whole ISO date format. This strips to just the date.
    endDateIn = endDateIn[:10]
    endDateIn = DT.datetime.strptime(endDateIn, '%Y-%m-%d')
    endDate = endDateIn.date()
    message += 'Used the entered endDate, %s<br>' % endDate
except:
    endDateIn = DT.datetime.now() + DT.timedelta(days=60) # Default to search for 2 mo
    endDate = endDateIn.date()
    message += 'Used the default endDate<br>'

try:
    weekendsIn = form.getfirst('weekends')
    weekendsIn = cgi.escape(weekendsIn)
    if weekendsIn == '1':
        weekendsOK = 1
        message += 'Used the entered weekends parameter, %s<br>' % weekendsOK
    else: weekendsOK = 0
except:
    weekendsOK = 0
    message += 'Used the default weekends parameter, 0<br>'

try:
    candIn = form.getfirst('candidates', '')
    candidates = int(cgi.escape(candIn))
    message += 'Used the entered candidates %s<br>' % candidates
except:
    candidates = 15
    message += 'Used the default candidates %s<br>' % candidates

vacTupules = []
try:
    vacStartsIn = form.getlist('vacStart')
    vacStopsIn = form.getlist('vacStop')
    assert (len(vacStartsIn) == len(vacStopsIn))
    for i, start in enumerate(vacStartsIn):
        assert (start < vacStopsIn[i])
        startI = cgi.escape(start)
        startI = startI[:10]
        startI = DT.datetime.strptime(startI, '%Y-%m-%d')
        startD = startI.date()

        stopI = cgi.escape(vacStopsIn[i])
        stopI = stopI[:10]
        stopI = DT.datetime.strptime(stopI, '%Y-%m-%d')
        stopD = stopI.date()
        vacTupule = (startD, stopD)
        vacTupules.append(vacTupule)
except:
    errMessage += 'Whoa! Something went wrong with vacation date entry, e.g., not all were entered as start/stop pairs or start date after stop date.<br>'

print vacTupules
print '<br>'
vacationInput = '(5/9,5/12) (1/30,2/14) (1/30,2/14)' # Will want to make this raw_input
csvIn = 'rotationsQual.csv'

print message
print errMessage

testInput = 'http://pediatricly.com/cgi-bin/elNino/schedTester.py?vacStart=2016-02-16&vacStop=2016-02-26&vacStart=2016-01-31&vacStop=2016-02-15'

