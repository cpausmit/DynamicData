#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# This script will determine if there is need to release the cache and perform the release
# The conventional unit for disk space operations is Byte. 
#  
#---------------------------------------------------------------------------------------------------
import socket, sys, os, commands, shutil, time
sys.path.append(os.environ['CINDERELLA_DIR'])
import database

# - S U B R O U T I N E S -----------------------------------------------------------------------------

def deleteDataset(dataset):
    # make sure dataset name is non-empty to avoid deleteting storage base directory
    if (dataset == ''):
        print " INFO - trying to remove non-existing dataset, skipping deletion."
        return
    else:
        # delete the dataset from the FS
        hadBaseDir = os.environ['CINDERELLA_DATA']
        hadBaseDir = hadBaseDir.replace('/mnt/hadoop','')
        cmd = 'hadoop fs -rm -r ' + hadBaseDir + '/' + dataset
        os.system(cmd)
        return

def getReleaseCondition(storageCapacity,storageFreeSpace,releaseThr):
    storageOccupiedFrac = (storageCapacity-storageFreeSpace)/storageCapacity
    print " INFO - cache occupancy is at " + str(round(storageOccupiedFrac*100)) + ' %'
    # determine if cache needs to be released
    if (storageOccupiedFrac > releaseThr):
        print " INFO - cache occupancy above release threshold (" + str(releaseThr*100) + " %)."
        return True
    else:
        print " INFO - cache occupancy is below release threshold (" + str(releaseThr*100) + " %)."
        return False

def getRemovableDatasets(releaseAmount):
    removableDatasets = []
    freedSpaceSum = 0
    # loop on the ordered DB and find which datasets will be released
    # note that the DB is already ordered according to the ranking algo
    # to keep the ordering use directly the DB and avoid the handle
    sql = "SELECT * FROM DatasetStatus"
    cursor.execute(sql)
    results = cursor.fetchall()
    for row in results:
        dataset = row[0]
        dbDataset = datasetStati.retrieveElement(dataset)
        # if dataset not in cache do not consider it for deletions
        if (not dbDataset.inCache):
            continue
        freedSpaceSum += dbDataset.size
        # add this dataset to the list of removable ones
        removableDatasets.append(dataset)
        # if size of removable datasets exceeds release amount stop
        if (freedSpaceSum > releaseAmount):
            break
    return removableDatasets 

def getStorageStatus():
    # prepare the Command to get the current storage status
    cmd = 'hadoop fs -df -h'
    # example output:
    # Filesystem                        Size     Used  Available  Use%
    # hdfs://t3serv002.mit.edu:9000  257.6 T  251.0 T      6.5 T   97%
    storageStatusSummary = commands.getoutput(cmd).split()
    strStorageCapacity   = storageStatusSummary[6]
    unitStorageCapacity  = storageStatusSummary[7]
    strStorageFreeSpace  = storageStatusSummary[10]
    unitStorageFreeSpace  = storageStatusSummary[11]
    # check the sanity of the strings and convert into float
    try:
        storageCapacity = float(strStorageCapacity)
        print " INFO - total storage space is " + strStorageCapacity + ' ' + unitStorageCapacity
        if unitStorageCapacity == 'T':
            storageCapacity *= 1.e+12
        elif unitStorageCapacity == 'G':
            storageCapacity *= 1.e+9
    except ValueError:
        print ' ERROR -- cannot read storage capacity, aborting.'
        os._exit(1)
    try:
        storageFreeSpace = float(strStorageFreeSpace)
        print " INFO - total available space is " + strStorageFreeSpace + ' ' + unitStorageFreeSpace
        if unitStorageFreeSpace == 'T':
            storageFreeSpace *= 1.e+12
        elif unitStorageFreeSpace == 'G':
            storageFreeSpace *= 1.e+9
    except ValueError:
        print ' ERROR -- cannot read storage free space, aborting.'
        os._exit(1)

    return storageCapacity, storageFreeSpace

def releaseCache(executeRelease,datasetsToRemove):
    # check the execution release flag
    if (executeRelease):
        print " INFO - datasets deletions starting now. "
        # loop on the datasets, delete them and update the DB 
        for dataset in datasetsToRemove:
            print " ----> deleting dataset " + dataset
            deleteDataset(dataset)
            dbDataset = datasetStati.retrieveElement(dataset)
            updateDataset(dataset,dbDataset.nUsed,dbDataset.nDownloads,dbDataset.time,dbDataset.size)
            updateDatasetHistory(dataset,dbDataset.nDownloads,dbDataset.size)
        return
    else:
        print " INFO - user setting prevented deletions. "
        return

def updateDataset(dataset,nDatasetAccesses,nDatasetDownloads,atime,size):
    # update the dataset so that the inCache flag is correctly updated
    # prepare SQL query to UPDATE a record into the database.
    sql = "UPDATE DatasetStatus SET NUsed='%d',NDownloads='%d',InCache='%d',EntryDateUT='%d',Size='%f' WHERE Name='%s'"\
          %(nDatasetAccesses,nDatasetDownloads,False,atime,size,dataset)
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

def updateDatasetHistory(dataset,nDatasetDownloads,size):
    # update the datasets table history to record this deletion
    # deletion cycle is equal to the number of previous dataset downloads
    # deletion time is corresponding to the insertion in the DB history table 
    # prepare SQL query to INSERT a record into the history database.
    deltime = int(time.time())
    sql  = "INSERT INTO CompletedDeletions VALUES ('%s','%d','%d','%f')"\
           %(dataset,nDatasetDownloads,deltime,size)
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

# - M A I N ----------------------------------------------------------------------------------------

# Check the number of input arguments
if len(sys.argv) < 4:
    print "\n Usage: ", sys.argv[0], \
          " rel_thr rel_frac safemode"
    sys.exit(1)

# Say what we are doing 
localtime = time.asctime( time.localtime(time.time()) )
print " \n "
print " ============================================================================================= "
print " " + localtime + " : Block " + sys.argv[0] + " is starting."
print " ============================================================================================= "

# Get the parameter necessary to decide and perform a cache release
releaseThr     = float(sys.argv[1])
releaseFrac    = float(sys.argv[2])
if (sys.argv[3] == '1'):
    executeRelease = False
else:
    executeRelease = True

# Open database connection
db = database.DatabaseHandle()
# Prepare a cursor object using cursor() method
cursor = db.getCursor()
    
# Make a new objects of all datasets
datasetStati = database.Container()
rc = datasetStati.fillWithDatasetStati(db.handle)
if rc != 0:
    print " ERROR - filling courses."
    # disconnect from server
    db.disco()
    sys.exit(1)

# Take a snapshot of the FS and extract the relevant proprieties
storageCapacity = 0
storageFreeSpace = 0
(storageCapacity, storageFreeSpace) = getStorageStatus()

# Determine if caching release is needed
releaseCond = getReleaseCondition(storageCapacity,storageFreeSpace,releaseThr)

# Release the cache if necessary
if (releaseCond):
    # Compute the amount of disk to be freed
    releaseAmount = float(releaseFrac*storageCapacity)
    # Get the list of datasets to be removed
    datasetsToRemove = getRemovableDatasets(releaseAmount)
    # Show the datasets to be deleted
    print " INFO - the following datasets will be removed from the cache:"
    print " ---> : " + str(datasetsToRemove)
    # Perform the removal only if the execution deletion is set to True
    releaseCache(executeRelease,datasetsToRemove)

# disconnect from server
db.disco()
sys.exit(1)
