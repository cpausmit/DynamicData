#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# This script will perform a ranking of the records present in the dataset DB.
#
#---------------------------------------------------------------------------------------------------
import socket, sys, os, commands, shutil, time
sys.path.append(os.environ['CINDERELLA_DIR'])
import database

# - S U B R O U T I N E S -----------------------------------------------------------------------------

def rankByTime():
    # prepare SQL query to RANK the records in the database.
    sql = "ALTER TABLE DatasetStatus ORDER BY EntryDateUT ASC;"
    print ' rank: ' + sql
    try:
        # Execute the SQL command
        cursor.execute(sql)
        return
    except:
        print ' ERROR -- ranking failed, rolling back.'
        # Rollback in case there is any error
        db.rollback()
        db.disco()
        os._exit(1)
    

# - M A I N ----------------------------------------------------------------------------------------

# Check the number of input arguments
if len(sys.argv) < 2:
    print "\n Usage: ", sys.argv[0], \
          " ranking_algo"
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
rc = datasetStati.fillWithDatasetStati(db.handle)
if rc != 0:
    print " ERROR - filling courses."
    # disconnect from server
    db.disco()
    sys.exit(1)

# Rank the DB according to the user choice
rankingAlgo = sys.argv[1]
if sys.argv[1] == 'timeRank':
    print " INFO - ranking DB by time."
    rankByTime()
# If ranking algo option not recognized, use default (time based ranking) 
else:
    print " INFO - ranking algo not specified, using default option (time)."
    rankByTime()

# disconnect from server
db.disco()
sys.exit(1)
