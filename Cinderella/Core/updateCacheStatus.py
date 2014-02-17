#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# This script will check all dataset presently on disk and update their database record, or create
# it if the record does not yet exist.
#
#---------------------------------------------------------------------------------------------------
import socket, sys, os, time, commands, shutil, mmap
from datetime import datetime
sys.path.append(os.environ['CINDERELLA_DIR'])
import database

# - S U B R O U T I N E S -----------------------------------------------------------------------------

def findLastAccessedFile(dir):
    cmd = 'ls -Aru ' + dir + ' | tail -n 1'
    theLatestFile = commands.getoutput(cmd)
    return theLatestFile

def getDataSetSize(dataset,hadBaseDir):
    cmd = 'hadoop fs -du -s ' + hadBaseDir + '/' + dataset
    datasetSize = commands.getoutput(cmd).split()[0]
    # Check if dataset size is a float, otherwise exit from the subroutine and main routine
    try:
        float(datasetSize)
        return float(datasetSize)
    except ValueError:
        print ' ERROR -- dataset ' + dataset + ' size is nan, aborting.'
        db.rollback()
        db.disco()
        os._exit(1)

    
def insertDataset(dataset,nDatasetAccesses,nDatasetDownloads,atime,size):
    # prepare SQL query to INSERT a record into the database.
    sql = "insert into DatasetStatus(Name,NUsed,NDownloads,InCache,EntryDateUT,Size) values ('%s','%d','%d',true,'%d','%f')"\
          %(dataset,nDatasetAccesses,nDatasetDownloads,atime,size)
    print ' insert: ' + sql
    try:
        # Execute the SQL command
        cursor.execute(sql)
        return
    except:
        print ' ERROR -- insert failed, rolling back.'
        # Rollback in case there is any error
        db.rollback()
        db.disco()
        os._exit(1)

def updateDataset(dataset,nDatasetAccesses,nDatasetDownloads,datasetInCache,atime,size):
    # prepare SQL query to UPDATE a record into the database.
    sql = "UPDATE DatasetStatus SET NUsed='%d',NDownloads='%d',InCache='%d',EntryDateUT='%d',Size='%f' WHERE Name='%s'"\
          %(nDatasetAccesses,nDatasetDownloads,datasetInCache,atime,size,dataset)
    print ' update: ' + sql
    try:
        # Execute the SQL command
        cursor.execute(sql)
        return
    except:
        print ' ERROR -- update failed, rolling back.'
        # Rollback in case there is any error
        db.rollback()
        db.disco()
        os._exit(1)
    

# - M A I N ----------------------------------------------------------------------------------------

# Check the number of input arguments
if len(sys.argv) < 2:
    print "\n Usage: ", sys.argv[0], \
          " dataset_base_path"
    sys.exit(1)

# Say what we are doing 
localtime = time.asctime( time.localtime(time.time()) )
print " \n "
print " ============================================================================================= "
print " " + localtime + " : Block " + sys.argv[0] + " is starting."
print " ============================================================================================= "

# Open database connection
db = database.DatabaseHandle()
# Prepare a cursor object using cursor() method
cursor = db.getCursor()

# Make a new objects of all datasets
datasetStati = database.Container()
rc = datasetStati.fillWithDatasetStati(db.handle,True)
if rc != 0:
    print " ERROR - filling courses."
    # disconnect from server
    db.disco()
    sys.exit(1)

# Show what is presently in our database (careful, this container will not be updated)
datasetStati.show()

# files in hadoop accessed through fuse need "/mnt/hadoop" at the beginning while files accessed
# directly through hadoop need that to not be there so we're setting that up here:

hadoopString = '/mnt/hadoop'

baseDir      = sys.argv[1]
hadBaseDir   = baseDir.replace(hadoopString,'')

# warning: this is hardcoded and needs to be tuned according to the FS depth
cmd = 'find ' + baseDir + ' -maxdepth 3 -mindepth 3'
os.chdir(baseDir);

for line in os.popen(cmd).readlines():
    line    = line[:-1]
    dataset = line.replace(baseDir+'/','')

    print "processing dataset " + dataset.replace(baseDir,'')

    # find the dataset timestamp by looking at the latest accessed file
    theLatestFile = findLastAccessedFile(dataset)
    (mode,ino,dev,nlink,uid,gid,size,atime,mtime,ctime) = os.stat(dataset + '/' + theLatestFile)
    print " last accessed file %s  at %s --> %s"%(theLatestFile,time.ctime(atime),atime)

    # initialize dataset attributes to default values
    # do not compute size by default to save on processing time
    nDatasetAccesses  = 1
    nDatasetDownloads = 1
    datasetTimeStamp  = atime
    datasetSize       = -1

    # see whether we know this dataset already
    try:
        dbDataset = datasetStati.retrieveElement(dataset)
        print ' Dataset in our database.'
        # adjust dataset attributes according to the DB
        nDatasetAccesses    = dbDataset.nUsed
        datasetOldTimeStamp = dbDataset.time
        datasetSize         = dbDataset.size
        datasetInCache      = dbDataset.inCache
        # increment the dataset download request if already in DB but appears as not in cache
        # and reset InCache flag to True
        if not dbDataset.inCache:
            nDatasetDownloads = dbDataset.nDownloads + 1
            datasetInCache    = True
        else:
            nDatasetDownloads = dbDataset.nDownloads
        # check wether dataset timestamp has changed wrt latest cycle, otherwise do not touch DB
        if (int(datasetTimeStamp) != int(datasetOldTimeStamp)):
            # update access count and size only if dataset has been touched
            nDatasetAccesses += 1
            datasetSize = getDataSetSize(dataset,hadBaseDir)
            updateDataset(dataset,nDatasetAccesses,nDatasetDownloads,datasetInCache,datasetTimeStamp,datasetSize)
    except LookupError:
        print ' Dataset not yet in our database.'
        # compute dataset size and leave other attributes to default
        datasetSize = getDataSetSize(dataset,hadBaseDir)
        insertDataset(dataset,nDatasetAccesses,nDatasetDownloads,atime,datasetSize)

# disconnect from server
db.disco()
sys.exit(1)
