#!/usr/bin/python
# --------------------------------------------------------------------------------------------------
# Go to the database and show the full list of completed download requests (careful these are all).
# --------------------------------------------------------------------------------------------------
import os, MySQLdb, time

def getHostIndex(host):
    # very rudimentary implementation but for now it works
    if host == "":
        return -1
    else:
        return int(host[6:9])

endTime   = time.time()
# never show anything older than ~1 month (30 days) to avoid huge calulations
startTime = endTime - (30 * 24 * 3600);

print ' Consider request times between %d and %d only'%(startTime,endTime)

sparse = True
output = False
requestTimes = []
machineIdxs = []

# open database connection
db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="SmartCache")

# prepare a cursor object using cursor() method
cursor = db.cursor()

# Prepare SQL query to select a record from the database.
sql = "select * from CompletedDownloads where EntryDateUT>%d"%(startTime) + \
      " and CompletionDateUT=0"

# ! this could be done in one line but it is just nice to see what is deleted !
try:
    # Execute the SQL command
    print '\n Mysql> ' + sql
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
        stim = row[6]
        ctim = row[7]
        size = row[8]
        host = row[9]

        # Print failed record if needed
        if output:
            print " --> file=%s dset=%s book=%s"%(file,dset,book) + \
                  " prio=%d time=%d stat=%d stim=%d ctim=%d size=%f host=%s"% \
                  (prio,time,stat,stim,ctim,size,host)

        # Record the failed download
        requestTimes.append(time)
        machineIdxs.append(getHostIndex(host))

    print ' TOTAL failures: %d '%(len(requestTimes))

except:
    print " Error (%s): unable to fetch data."%(sql)

# disconnect from server
db.close()

#------------------------------------------------------------------
# Create time series of the transfer speeds with constant intervals
#------------------------------------------------------------------
import itertools

time = startTime
lastTime = startTime - 90
dots = True
fHandle = open('timeSeriesOfFailures.txt','w')
while time < endTime:
    nFailures = 0
    for machineIdx, requestTime in itertools.izip(machineIdxs, requestTimes):
        if  requestTime > lastTime and requestTime < time:
            nFailures += 1

    # always create the output for root to make the plot
    fHandle.write('%d %d\n'%(time,nFailures))

    if output:
        print ' %d: %d'%(time,nFailures)

    # keep track of the last time
    lastTime = time
    time += 90

fHandle.close()
