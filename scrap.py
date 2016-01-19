Scrap

if len(blockTops) > 0:
            for top in blockTops:
                posStarts.add(top['startDate'])
                posStarts.add(blockStarts[blockNum])
                if top['stopDate'] < blockStops[blockNum]:
                    posStops.add(top['stopDate'])
                posStops.add(blockStops[blockNum])
            print posStarts
            print posStops
            remStarts = sorted(list(posStarts - topStarts))
            remStops = sorted(list(posStops - topStops))
            print remStarts
            print remStops

