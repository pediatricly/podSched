#! /usr/bin/python26

################################################################################
### CGI Setup
################################################################################
import cgi
import cgitb
# cgitb.enable()
print 'Content-Type: text/plain\r\n'
fh = open('rotationsQual.csv', 'rb')
print fh.read()
