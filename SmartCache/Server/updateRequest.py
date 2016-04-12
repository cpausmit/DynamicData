#!/usr/bin/python
# --------------------------------------------------------------------------------------------------
#
# To enable proper monitoring of the downloads and track the download performance depending on the
# hardware the file cacher will update the database entry to reflect the most accurate information.
# Every request should be updated twice after creation: once when the download starts and once when
# the download is completed.
#
# In the update at the start time we update the download start time and the hostname field. At
# completion we just update the completion time field.
#
# --------------------------------------------------------------------------------------------------
import os, sys, getopt, MySQLdb, time
import datetime
from   datetime import date, timedelta

# Define string to explain usage of the script
usage =  " Usage: updateRequest.py --file=<name>\n"
usage += "                         --dataset=<name>\n"
usage += "                         --book=<name>\n"
usage += "                         [ --startTime>\n"
usage += "                           --host=<host> ]  || \n"
usage += "                         [ --completionTime ]\n"
usage += "                         [ --sizeGb ]\n"
usage += "                              [ --help ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['file=','dataset=','book=','host=','sizeGb=',
         'startTime','completionTime',
         'help']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError, ex:
    print usage
    print str(ex)
    sys.exit(1)

# --------------------------------------------------------------------------------------------------
# Get all parameters for the update
# --------------------------------------------------------------------------------------------------
# Set defaults for each command line parameter/option
file    = ''
dataset = ''
book    = ''
host    = ''
sizeGb  = -1.0
action  = ''
timeNow = int(time.time())

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print usage
        sys.exit(0)
    if opt == "--file":
        file = arg
    if opt == "--dataset":
        dataset = arg
    if opt == "--book":
        book = arg
    if opt == "--startTime":
        action = "start"
    if opt == "--host":
        host = arg
    if opt == "--completionTime":
        action = "completion"
    if opt == "--sizeGb":
        sizeGb = arg

if file == '' or dataset == '' or book == '':
    print '\n ERROR in usage. Please, fully specify your request to update.\n'
    print usage
    sys.exit(1)

if action == 'start' and host == '':
    print '\n ERROR in usage. Please, specify hostname (--host) when updating start time.\n'
    print usage
    sys.exit(1)

if action == 'completion' and sizeGb == -1.0:
    print '\n ERROR in usage. Please, specify size [GB] (--sizeGb) when updating completion time.\n'
    print usage
    sys.exit(1)
        
# --------------------------------------------------------------------------------------------------
# Get access to the database and see whether request exists
# --------------------------------------------------------------------------------------------------
# Open database connection

db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="DynamicData")

# Prepare a cursor object using cursor() method
cursor = db.cursor()

# First check whether this download request already exists in the database
sql = "select * from Downloads where File='%s' and Dataset='%s' and Book='%s';"\
      %(file,dataset,book)
print ' select: ' + sql
results = []
try:
    # Execute the SQL command
    cursor.execute(sql)
    results = cursor.fetchall()
except:
    print " Error (%s): unable to fetch data."%(sql)
    sys.exit(0)

if len(results) > 0:
    print ' Success download request exists. Going ahead to update record.'
else:
    print ' Error(): Download request does not exists. EXIT!'
    db.close()
    sys.exit(0)

# --------------------------------------------------------------------------------------------------
# Update existing request
# --------------------------------------------------------------------------------------------------
sql = ''
if action == 'start':
    print ' update start time and host for download'
    sql = "update Downloads set StartDateUT=%d, Host='%s' where File='%s' and Dataset='%s'and Book='%s';"%(timeNow,host,file,dataset,book)
elif action == 'completion':
    print ' update completion time and file size for download'
    sql = "update Downloads set CompletionDateUT=%d, SizeGb='%s' where File='%s' and Dataset='%s'and Book='%s';"%(timeNow,sizeGb,file,dataset,book)
else:
    print ' Error(action) - unknown action requested (%s)'%(action)
    db.close()
    sys.exit(0)

print " SQL> " + sql
try:
    # Execute the SQL command
    cursor.execute(sql)
    # Commit your changes in the database
    db.commit()
except:
    print " Error (%s): unable to update record."%(sql)
    # Rollback in case there is any error
    db.rollback()

# disconnect from server
db.close()
