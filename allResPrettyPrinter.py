from allResStr1 import allRes

for res in allRes:
    print res + ':'
    for rot in allRes[res]['schedule']:
        print rot
    print '\n'

