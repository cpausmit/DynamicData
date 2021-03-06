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
import os, sys, MySQLdb, time
import traceback
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

cmd = "condor_q -global $USER -format \"%s \" Cmd -format \"%s \n\" Args"

iDownloads = 0
for line in os.popen(cmd).readlines():   # run command
    if 'cacheFile.sh' not in line:
        continue
    if 'queues' in line:
        continue

    iDownloads+=1
    line = line[:-1]                     # strip '\n'
    f = line.split(' ')
    files.append(f[1])
    dsets.append(f[2])
    books.append(f[3])
    print ' CONDOR -- File(%3d): %s  Dataset: %s  Book: %s'%(iDownloads,f[1],f[2],f[3])


# open database connection
db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="DynamicData")

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
        etim = row[4]
        stat = row[5]
        stim = row[6]
        ctim = row[7]
        size = row[8]
        host = row[9]
        # print fetched result
        print " --> file=%s dset=%s book=%s"% \
              (file,dset,book) + \
              " prio=%d etim=%d stat=%d stim=%d ctim=%d size=%f host=%s"% \
              (prio,etim,stat,stim,ctim,size,host)

        # check whether the transfer worked
        resubmit = 0
        if host == "":
            resubmit = 1
            print ' Error in download request. Download host did not register in database.'
            if size > 0.0001 and ctim > 0:
                print ' WARNING - file seems to have arrived though? this should never happen.'
            else:
                print ' Error - continued. File did not download. Considering re-submission.'
        else:
            if size < 0.0001 or ctim == 0:
                print ' Error - file failed download on host: ' + host + \
                      ' Considering re-submission.'
                resubmit = 1

        # testing details of failed transfer update record and decide if re-submit needed
        if resubmit == 1:
            # test the status here (this happens only in exceptional cases == failures)
            # - record time
            # - find file size and download status
            completionTime = startTime
            sizeGb = 0
            fullFile = SMARTCACHE_DATA + '/' + book + '/' + dset + '/' + file
            if os.path.isfile(fullFile):
                sizeBytes = os.path.getsize(fullFile)
                sizeGb = float(sizeBytes)/1024./1024./1024.
                # maybe should test file size here? but against what?
                ctim = completionTime # approximate completion time (+ cycle time max)
                stat = 0              # overwriting status (reflects the fix)
                resubmit = 0
            else:
                print ' File does not exist, download failed: ' + fullFile

        sql = 'select SizeGb from CompletedDownloads where File = \'%s\' and Dataset = \'%s\' and Book = \'%s\' order by EntryDateUT desc;' % \
            (file, dset, book)

        cursor.execute(sql)

        results = cursor.fetchall()
        nfail = 0
        for row in results:
            if row[0] < 0.001:
                nfail += 1

                # failed 5 times in a row - maybe resubmitting doesn't work for this file
                if nfail == 5:
                    resubmit = 0
                    break
            else:
                break

        # insert into our CompletedDownload table (failed or successfully completed)
        sql="insert into CompletedDownloads values ('%s','%s','%s',%d,%d,%d,%d,%d,%f,'%s');"%\
             (file,dset,book,prio,etim,stat,stim,ctim,size,host)
        try:
            # Execute the SQL command
            print '        ' + sql
            cursor.execute(sql)
            # Commit your changes in the database
            db.commit()
        except:
            traceback.print_exc(3, sys.stdout)
            print " Error (%s): unable to insert record into CompletedDownload table."%(sql)

        # remove all matching download requests from the Downloads table
        sql="delete from Downloads where Status=2 and File='%s' and Dataset='%s' and Book='%s';"%\
             (file,dset,book)
        try:
            # Execute the SQL command
            print '        ' + sql
            cursor.execute(sql)
            # Commit your changes in the database
            db.commit()
        except:
            traceback.print_exc(3, sys.stdout)
            print " Error (%s): unable to update status."%(sql)
            # Rollback in case there is any error
            db.rollback()

        # take care of failed requests (this is dangerous is everything fails, needs safety)
        if resubmit == 1:
            # Submit the download request
            cmd = SMARTCACHE_DIR + '/Client/addDownloadRequest.py --file=' + \
                  file + ' --dataset=' + dset + ' --book=' + book
            print ' WARNING - DANGEROUS RECOVERY LOOP IN ACTION -- Execute: ' + cmd
            os.system(cmd)

# STATUS should only be updated after the Server issues submitDownload.sh (Y.I. 2016/07/10)
#            # Update status information in the table
#            sql="update Downloads set Status=1 where File='%s' and Dataset='%s'and Book='%s';"%\
#                 (file,dset,book)
#            try:
#                # Execute the SQL command
#                cursor.execute(sql)
#                # Commit your changes in the database
#                db.commit()
#            except:
#                traceback.print_exc(3, sys.stdout)
#                print " Error (%s): unable to update status."%(sql)
#                # Rollback in case there is any error
#                db.rollback()
            

except:
    traceback.print_exc(3, sys.stdout)
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
        etim = row[4]
        stat = row[5]
        # Now print fetched result
        print " --> file=%s, dset=%s, book=%s, prio=%d, etim=%d, stat=%d"% \
              (file,dset,book,prio,etim,stat)

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
                traceback.print_exc(3, sys.stdout)
                print " Error (%s): unable to update status."%(sql)
                # Rollback in case there is any error
                db.rollback()

except:
    traceback.print_exc(3, sys.stdout)
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
        etim = row[4]
        stat = row[5]
        # Now print fetched result
        print " --> file=%s, dset=%s, book=%s, prio=%d, etim=%d, stat=%d"% \
              (file,dset,book,prio,etim,stat)

        # Submit the download request
        cmd = SMARTCACHE_DIR + '/Server/submitDownload.sh ' + \
              file + ' ' + dset + ' ' + book + ' ' + str(prio) + ' ' + str(etim)
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
            traceback.print_exc(3, sys.stdout)
            print " Error (%s): unable to update status."%(sql)
            # Rollback in case there is any error
            db.rollback()

except:
    traceback.print_exc(3, sys.stdout)
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
