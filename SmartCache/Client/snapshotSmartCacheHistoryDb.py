#!/usr/bin/python
# --------------------------------------------------------------------------------------------------
# Go to the database and show the full list of completed download requests (careful these are all).
# --------------------------------------------------------------------------------------------------
import os, MySQLdb, time

startTime = 1800000000
endTime = time.time()

sparse = True
output = False
tInits = []
tEnds = []
rates = []

# open database connection
db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="SmartCache")

# prepare a cursor object using cursor() method
cursor = db.cursor()

# Prepare SQL query to select a record from the database.
sql = "select * from CompletedDownloads"

# ! this could be done in one line but it is just nice to see what is deleted !
try:
    # Execute the SQL command
    #print '\n Mysql> ' + sql
    if output:
        print ''
        print '  File Size  Download time       Transfer  File'
        print '--------------------------------------------------------------------------------' + \
              '---------'
    cursor.execute(sql)
    # Fetch all the rows in a list of lists.
    results = cursor.fetchall()
    totalTime = 0.
    totalSize = 0.
    for row in results:
        file = row[0]
        dset = row[1]
        book = row[2]
        prio = row[3]
        time = row[4]
        stat = row[5]
        ctim = row[6]
        size = row[7]
        # Now print fetched result
        #print " --> file=%s, dset=%s, book=%s, prio=%d, time=%d, stat=%d, ctim=%d, size=%f"% \
        #      (file,dset,book,prio,time,stat,ctim,size)

        totalTime += (ctim-time)
        totalSize += size

        if output:
            print "   %5.2f GB     %6.2f min  %6.3f MB/sec  %-80s"% \
                  (size,(ctim-time)/60.,size*1024./(ctim-time),book+'/'+dset+'/'+file)

        # determine boundaries of performance plot
        if time<startTime:
            startTime = time

        tInits.append(time)
        tEnds.append(ctim)
        rates.append(size*1024./(ctim-time))
        
    if output:
        print '--------------------------------------------------------------------------------' + \
              '---------'
        print ' %6.2f GB    %8.2f min  TOTALS'% \
              (totalSize,totalTime/60.)
        print ''

except:
    print " Error (%s): unable to fetch data."%(sql)

# disconnect from server
db.close()

# Create time series of the transfer speeds with constant intervals

import itertools

time = startTime
lastRate = 0
dots = True
fHandle = open('timeSeriesOfRates.txt','w')
while time < endTime:
    presentRate = 0
    nConnections = 0
    for tInit, tEnd, rate in itertools.izip(tInits, tEnds, rates):
        if tInit < time and tEnd > time:
            nConnections += 1
            presentRate += rate

    # always create the output for root to make the plot
    fHandle.write('%d %f %d\n'%(time,presentRate,nConnections))

    if sparse:
        if lastRate != 0 or presentRate != 0:
            if output:
                print ' Rate(%d) [MB/sec]: %f (nConn: %d)'%(time,presentRate,nConnections)
            dots = True
        elif lastRate == 0 and dots:
            if output:
                print ' .. '
            dots = False
    else:
        if output:
            print ' Rate(%d) [MB/sec]: %f (nConn: %d)'%(time,presentRate,nConnections)

    # keep track of the last rate
    lastRate = presentRate
    time += 90

fHandle.close()
