#!/usr/bin/python
# --------------------------------------------------------------------------------------------------
# This is the core of managing download requests. It proceeds in five steps. The order is important
# to make sure not to loose any requests.
#
# status of downloading request: the general idea is to move each download request through 3
#                                distinct states 0, 1, 2
#
#    0 - request is entered initially with status 0, meaning it is new and has not been acted upon
#    1 - once the request has been put in the queue for downloading (job submitted)
#    2 - the request has been acted upon and the download request is not anymore in the queue
#        there is no test of success here, the system assumes that the request was successful
#
#
# 1. PREP    - preparations to find all ongoing download requests in the queue (condor)
#
# 2. PART 0  - query the database to find download request in status 2 (see explanation below)
#              requests found in status 2 will be deleted from the database
#
# 3. PART 1  - query the database to find download request in status 1 (see explanation below)
#              requests found in status 1 and not anymore in our queue will be moved to status 2
#
# 4. PART 2  - query the database to find download request in status 0 (see explanation below)
#              requests found in status 0 will be processed and submitted to the queue
#
# 5. MONITOR - provide basic monitoring status
#
# TODO -- [ we need a step 6 in which old logfiles will be cleared ]
#
# --------------------------------------------------------------------------------------------------
import os, MySQLdb, time
import datetime
from   datetime import date, timedelta

# define all relevant variable in python
SMARTCACHE_DATA="/mnt/hadoop/cms/store/user/paus"
SMARTCACHE_DIR="/usr/local/DynamicData/SmartCache"
SMARTCACHE_LOGDIR="/var/log/DynamicData/SmartCache"
SMARTCACHE_STATUS= SMARTCACHE_LOGDIR + "/smartcache.status"

# push definitions into shell environment for the subsequent processes
os.environ['SMARTCACHE_DIR']    = SMARTCACHE_DIR
os.environ['SMARTCACHE_LOGDIR'] = SMARTCACHE_LOGDIR
os.environ['SMARTCACHE_STATUS'] = SMARTCACHE_STATUS

startTime = time.time()
today = str(datetime.date.today())
ttime = time.strftime("%H:%M")

print ' Review started at UT:%d == %s - %s'%(startTime,today,ttime)

# --------------------------------------------------------------------------------------------------
# PREP ---------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------
# check ongoing requests in the condor queues
files = []
dsets = []
books = []

cmd="condor_q -global $USER -format \"%s \" Cmd -format \"%s \n\" Args | grep -v queues"
iDownloads=0
for line in os.popen(cmd).readlines():   # run command
    iDownloads+=1
    line = line[:-1]                     # strip '\n'
    f = line.split(' ')
    files.append(f[1])
    dsets.append(f[2])
    books.append(f[3])
    print ' CONDOR -- File(%3d): %s  Dataset: %s  Book: %s'%(iDownloads,f[1],f[2],f[3])


# open database connection
db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="SmartCache")

# prepare a cursor object using cursor() method
cursor = db.cursor()

# --------------------------------------------------------------------------------------------------
# PART 0 -------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------
# Prepare SQL query to select a record from the database.
sql = "select * from Downloads where Status=2"

# ! this could be done in one line but it is just nice to see what is deleted !
try:
    # Execute the SQL command
    print '\n Mysql> ' + sql
    cursor.execute(sql)
    # Fetch all the rows in a list of lists.

    # Fetch all the rows in a list of lists.
    results = cursor.fetchall()
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
        # Now print fetched result
        print " --> file=%s dset=%s book=%s"% \
              (file,dset,book) + \
              " prio=%d time=%d stat=%d stim=%d ctim=%d size=%f host=%s"% \
              (prio,time,stat,stim,ctim,size,host)

        # before removing this Download request create history in CompletedDownloads table
        # --------------------------------------------------------------------------------
        # the record has already been updated by the download process
        ## - record time
        #completionTime = startTime
        ## - find file size and download status
        #sizeGb = 0
        #fullFile = SMARTCACHE_DATA + '/' + book + '/' + dset + '/' + file
        #if os.path.isfile(fullFile):
        #    sizeBytes = os.path.getsize(fullFile)
        #    sizeGb = float(sizeBytes)/1024./1024./1024.
        #    stat = 0  # overwriting the status (now it reflects the completion of download)
        #else:
        #    print ' File does not exist, download failed: ' + fullFile

        # - insert into our CompletedDownload table
        sql="insert into CompletedDownloads values ('%s','%s','%s',%d,%d,%d,%d,%d,%f,'%s');"%\
             (file,dset,book,prio,time,stat,stim,ctim,size,host)
        try:
            # Execute the SQL command
            print '        ' + sql
            cursor.execute(sql)
            # Commit your changes in the database
            db.commit()
        except:
            print " Error (%s): unable to insert record into CompletedDownload table."%(sql)

        # remove all matching download requests from the Downloads table
        # --------------------------------------------------------------
        sql="delete from Downloads where Status=2 and File='%s' and Dataset='%s'and Book='%s';"%\
             (file,dset,book)
        try:
            # Execute the SQL command
            print '        ' + sql
            cursor.execute(sql)
            # Commit your changes in the database
            db.commit()
        except:
            print " Error (%s): unable to update status."%(sql)
            # Rollback in case there is any error
            db.rollback()

except:
    print " Error (%s): unable to fetch data."%(sql)

# --------------------------------------------------------------------------------------------------
# PART I -------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------
# Prepare SQL query to select a record from the database.
sql = "select * from Downloads where Status=1"
 
try:
    # Execute the SQL command
    print '\n Mysql> ' + sql
    cursor.execute(sql)
    # Fetch all the rows in a list of lists.
    results = cursor.fetchall()
    for row in results:
        file = row[0]
        dset = row[1]
        book = row[2]
        prio = row[3]
        time = row[4]
        stat = row[5]
        # Now print fetched result
        print " --> file=%s, dset=%s, book=%s, prio=%d, time=%d, stat=%d"% \
              (file,dset,book,prio,time,stat)

        # find all matching files and make sure dataset and book are the same
        i = -1
        match = False
        try:
            while not match:
                i = files.index(file,i+1)
                #print " matched at %d"%i
                #print " file %s   files[i] %s"%(file,files[i])
                if file == files[i] and dset == dsets[i] and book == books[i]:
                    match = True
                    print "  matched confirmed: %s  file still downloading."%(file)
        except ValueError:
            pass ##print " No match found."

        # Update status information in the table
        if not match:
            sql="update Downloads set Status=2 where File='%s' and Dataset='%s'and Book='%s';"%\
                 (file,dset,book)
            try:
                # Execute the SQL command
                cursor.execute(sql)
                # Commit your changes in the database
                db.commit()
            except:
                print " Error (%s): unable to update status."%(sql)
                # Rollback in case there is any error
                db.rollback()

except:
    print " Error (%s): unable to fetch data."%(sql)

# --------------------------------------------------------------------------------------------------
# PART II ------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------
# submit new requests

# Prepare SQL query to select a record from the database.
sql = "select * from Downloads where Status=0"

try:
    # Execute the SQL command
    print '\n Mysql> ' + sql
    cursor.execute(sql)
    # Fetch all the rows in a list of lists.
    results = cursor.fetchall()
    for row in results:
        file = row[0]
        dset = row[1]
        book = row[2]
        prio = row[3]
        time = row[4]
        stat = row[5]
        # Now print fetched result
        print " --> file=%s, dset=%s, book=%s, prio=%d, time=%d, stat=%d"% \
              (file,dset,book,prio,time,stat)

        # Submit the download request
        cmd = SMARTCACHE_DIR + '/Server/submitDownload.sh ' + \
              file + ' ' + dset + ' ' + book + ' ' + str(prio) + ' ' + str(time)
        print ' Execute: ' + cmd
        os.system(cmd)

        # Update status information in the table
        sql="update Downloads set Status=1 where File='%s' and Dataset='%s'and Book='%s';"%\
             (file,dset,book)
        try:
            # Execute the SQL command
            cursor.execute(sql)
            # Commit your changes in the database
            db.commit()
        except:
            print " Error (%s): unable to update status."%(sql)
            # Rollback in case there is any error
            db.rollback()

except:
    print " Error (%s): unable to fetch data."%(sql)


# disconnect from server
db.close()

# --------------------------------------------------------------------------------------------------
# MONITOR ------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------
print " Info: Adding monitoring data: " + SMARTCACHE_STATUS + "\n"

cmd = "date > " + SMARTCACHE_STATUS + "; " + SMARTCACHE_DIR + "/Client/statusSmartCache.sh >> "\
      + SMARTCACHE_STATUS
print " CMD: " + cmd

os.system(cmd)   # run command
