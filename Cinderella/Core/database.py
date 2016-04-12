# ==================================================================================================
#
# ==================================================================================================
import MySQLdb
import sys

class DatabaseHandle:
    'Class to provide a unique database handle for all work on the database.'
    
    def __init__(self):
        self.handle = MySQLdb.connect(read_default_file  = "/etc/my.cnf", \
                                      read_default_group = "mysql", \
                                      db                 = "DynamicData")
    
    def getCursor(self):
        return self.handle.cursor()

    def getHandle(self):
        return self.handle
    
    def disco(self):
        self.handle.close()

    def rollback(self):
        self.handle.rollback()

class DatasetStatus:
    'Class for a dataset status.'

    def __init__(self,name,nUsed,nDownloads,inCache,time,size):
        self.name       = name
        self.nUsed      = nUsed
        self.nDownloads = nDownloads
        self.inCache    = inCache
        self.time       = time
        self.size       = size

    def show(self):
        print " name=%s, NUsed=%d, NDownloads=%d, InCache=%d, EntryDateUT=%d, Size=%f"% \
              (self.name,self.nUsed,self.nDownloads,self.inCache,self.time,self.size)

class Container:
    'Container class for any type of object that has a unique id (hash key). We use the dataset name.'

    def __init__(self):
        self.hash = { }

    def addElement(self, key, element):
        self.hash[key] = element

    def retrieveElement(self, key):
        return self.hash[key]

    def popElement(self, key):
        return self.hash.pop(key)
    
    def getHash(self):
        return self.hash

    def show(self):
        for key, value in self.hash.iteritems():
            sys.stdout.write(" Key: %-6s -- "%key)
            value.show()

    def fillWithDatasetStati(self,database,debug=False):
        if debug:
            print " Start fill datasets."

        # grab the cursor
        cursor = database.cursor()

        # Prepare SQL query to select all courses from the Courses table
        sql = "SELECT * FROM DatasetStatus"
        if debug:
            print " SQL> " + sql
        try:
            # Execute the SQL command
            cursor.execute(sql)
            # Fetch all the results
            results = cursor.fetchall()
            for row in results:

                # (Name char(80), NUsed int, NDownloads int, InCache bool, EntryDateUT int, Size float);
                name       = row[0]
                nUsed      = int(row[1])
                nDownloads = int(row[2])
                inCache    = bool(row[3])
                time       = int(row[4])
                size       = float(row[5])

                # Now print fetched result
                if (debug):
                    print " --> name=%s, NUsed=%d, NDownloads=%d, InCache=%d, EntryDateUT=%d, Size=%f"% \
                          (name,nUsed,nDownloads,inCache,time,size)

                # create a new dataset status object and add it to our list
                datasetStatus = DatasetStatus(name,nUsed,nDownloads,inCache,time,size)
                if debug:
                    print " datasetStatus created."
                self.addElement(name,datasetStatus);
                
        except:
            print " ERROR(%s) - unable to fetch data from Courses table."%(sql)
            return 1

        # all went well
        return 0
