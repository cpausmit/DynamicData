#!/usr/bin/python
#===================================================================================================
# Add a download request into the database.
#
# v1.0                                                                                  May 09, 2013
#===================================================================================================
import sys,getopt,time
import MySQLdb

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage =  " Usage: addDownloadRequest.py --file=<name>\n"
usage += "                              --dataset=<name>\n"
usage += "                              --book=<name>\n"
usage += "                              [ --priority=0\n"
usage += "                                --time=<UnixTimeNow>\n"
usage += "                                --status=0 ]\n"
usage += "                              [ --help ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['file=','dataset=','book=','priority=','time=','status=',
         'help']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError, ex:
    print usage
    print str(ex)
    sys.exit(1)

# --------------------------------------------------------------------------------------------------
# Get all parameters for the production
# --------------------------------------------------------------------------------------------------
# Set defaults for each command line parameter/option
file     = ''
dataset  = ''
book     = ''
priority = 0
time     = int(time.time())
status   = 0

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print usage
        sys.exit(0)
    if opt == "--file":
        file     = arg
    if opt == "--dataset":
        dataset  = arg
    if opt == "--book":
        book     = arg
    if opt == "--priority":
        priority = arg
    if opt == "--time":
        time     = arg
    if opt == "--status":
        status   = arg

if file == '' or dataset == '' or book == '':
    print '\n ERROR in usage. Please, fully specify your request.\n'
    print usage
    sys.exit(1)
        
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
    print ' Download request exists already. Do not insert again.'
    sys.exit(0)

# Prepare SQL query to INSERT a new record into the database.
sql = "insert into Downloads(File,Dataset,Book,Priority,EntryDateUT,Status," + \
      "StartDateUT,CompletionDateUT,SizeGb,Host)" + \
      " values('%s','%s','%s','%d','%d',0,default,default,default,default)"% \
        (file,dataset,book,priority,time)

print ' insert: ' + sql
try:
    # Execute the SQL command
    cursor.execute(sql)
    # Commit your changes in the database
    db.commit()
except:
    print ' ERROR -- insert failed, rolling back.'
    # Rollback in case there is any error
    db.rollback()
    
# disconnect from server
db.close()
