#!/usr/bin/python
# --------------------------------------------------------------------------------------------------
# Go to the database and show the full list of completed download requests (careful these are all).
# --------------------------------------------------------------------------------------------------
import os,MySQLdb

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
    print ''
    print '  File Size  Download time       Transfer  File'
    print '-----------------------------------------------------------------------------------------'
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

        print "   %5.2f GB     %6.2f min  %6.3f MB/sec  %-80s"% \
              (size,(ctim-time)/60.,size*1024./(ctim-time),book+'/'+dset+'/'+file)

    print '-----------------------------------------------------------------------------------------'
    print ' %6.2f GB    %8.2f min  %6.3f MB/sec   TOTALS'% \
          (totalSize,totalTime/60.,totalSize*1024/totalTime)
    print ''

except:
    print " Error (%s): unable to fetch data."%(sql)

# disconnect from server
db.close()
