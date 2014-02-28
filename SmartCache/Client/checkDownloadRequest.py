#!/usr/bin/python
#===================================================================================================
# Check for a download request into the database.
#
# v1.0                                                                                  May 09, 2013
#===================================================================================================
import os,sys,getopt,re,time
import MySQLdb

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage =  " Usage: checkDownloadRequest.py --files=<name1,name2,...>\n"
usage += "                                --dataset=<name>\n"
usage += "                                --book=<name>\n"
usage += "                                [ --priority=0\n"
usage += "                                  --time=<UnixTimeNow>\n"
usage += "                                  --status=0 ]\n"
usage += "                                [ --help ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['files=','dataset=','book=','priority=','time=','status=',
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
# set defaults for each command line parameter/option
files    = ''
dataset  = ''
book     = ''
priority = 0
time     = int(time.time())
status   = 0

# read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print usage
        sys.exit(0)
    if opt == "--files":
        files     = arg
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

if files == '' or dataset == '' or book == '':
    print '\n ERROR in usage. Please, fully specify your request.\n'
    print usage
    sys.exit(1)
        
# open database connection
db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="SmartCache")

# prepare a cursor object using cursor() method
cursor = db.cursor()

# prepare SQL query to INSERT a record into the database.
sql = "select * from Downloads where Status<2 and Dataset='%s' and Book='%s';"%\
      (dataset,book)

file = ''
match = False
try:
    # Execute the SQL command
    cursor.execute(sql)
    # Fetch all the rows in a list of lists.
    results = cursor.fetchall()

    for row in results:
        file   = row[0]
        status = row[5]
        if re.search(file,files):
            match = True
            break

except:
    pass  #print " Not data matches record."

# disconnect from server
db.close()

# exit
if match:
    print ' Download not yet completed (%s, status=%s).'%(file,status)
    sys.exit(0)
else:
    print ' Download completed (%s).'%(file)
    if os.path.isdir('/mnt/hadoop/cms/store/user/paus'):
        for file in files.split(','):
            os.system('ls -lh /mnt/hadoop/cms/store/user/paus/' + book + '/' + dataset + '/' + file)

    sys.exit(1)
