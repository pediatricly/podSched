from allResStr import allRes

for res in allRes:
    print res + ':\n'
    for rot in allRes[res]['schedule']:
        print rot

