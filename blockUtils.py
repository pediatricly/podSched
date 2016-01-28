def blockLookup(date, AmName, resDict):
    if type(date) != str:
        isoDate = date.isoformat()
    else: isoDate = date
    rot = ''
    block = ''
    blockSched = resDict[AmName]['schedule']
    for rotation in blockSched:
        if isoDate >= rotation['startDate'] and isoDate <= rotation['stopDate']:
            rot = rotation['rotation']
            block = rotation['block']
    return (block, rot)
##########################################################

