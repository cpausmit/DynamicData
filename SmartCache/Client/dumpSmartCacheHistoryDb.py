#!/usr/bin/python
# --------------------------------------------------------------------------------------------------
# Go to the database and show the full list of completed download requests (careful these are all).
# --------------------------------------------------------------------------------------------------
import os, MySQLdb, time

#startTime = 1800000000

endTime   = time.time()
startTime = 0;

print ' Consider times between %d and %d only'%(startTime,endTime)

sparse = True
output = False
rates = []

# open database connection
db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="SmartCache")

# prepare a cursor object using cursor() method
cursor = db.cursor()

# Prepare SQL query to select a record from the database.
sql = "select * from CompletedDownloads where StartDateUT>%d and CompletionDateUT>%d"% \
      (startTime,startTime)

# ! this could be done in one line but it is just nice to see what is deleted !
try:
    # Execute the SQL command
    print '\n Mysql> ' + sql
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


    fHandle = open('requests.txt','w')

    for row in results:
        file = row[0]
        dset = row[1]
        book = row[2]
        prio = row[3]
        time = row[4]
        stat = row[5]
        stim = row[6]
        ctim = row[7]
        size = row[8]
        host = row[9]

        # only consider entries that are in our time range (already done in SQL but do it again)
        if ctim < startTime or stim < startTime:
            continue

        # always create the output for root to make the plot
        fHandle.write('%s %s %s %d %d %d %d %d %f %s\n'% \
                      (file,dset,book,prio,time,stat,stim,ctim,size,host))

        totalTime += (ctim-stim)
        totalSize += size

        if output:
            print "   %5.2f GB     %6.2f min  %6.3f MB/sec  %-80s"% \
                  (size,(ctim-stim)/60.,size*1024./(ctim-stim),book+'/'+dset+'/'+file)

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
