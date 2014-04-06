#!/usr/bin/python
# --------------------------------------------------------------------------------------------------
# Go to the database and show the full list of download requests.
# --------------------------------------------------------------------------------------------------
import os,MySQLdb

# open database connection
db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="SmartCache")

# prepare a cursor object using cursor() method
cursor = db.cursor()

# Prepare SQL query to select a record from the database.
sql = "select * from Downloads"

# ! this could be done in one line but it is just nice to see what is deleted !
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
        stim = row[6]
        ctim = row[7]
        size = row[8]
        host = row[9]
        # Now print fetched result
        print " --> file=%s dset=%s book=%s"% \
              (file,dset,book) + \
              " prio=%d time=%d stat=%d stim=%d ctim=%d size=%f host=%s"% \
              (prio,time,stat,stim,ctim,size,host)

except:
    print " Error ($s): unable to fetch data."%(sql)

# disconnect from server
db.close()
