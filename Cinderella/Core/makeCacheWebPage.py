#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# This script will read the cache status database and translate it in a web page format
#   
#---------------------------------------------------------------------------------------------------
import socket, sys, os, commands, shutil, time
sys.path.append(os.environ['CINDERELLA_DIR'])
import database

# - S U B R O U T I N E S -----------------------------------------------------------------------------

def getStorageStatus():
    # prepare the Command to get the current storage status
    cmd = 'hadoop fs -df -h'
    # store the storage status in an array
    # the relevant fields are : [6] -> storageCapacity
    #                           [8] -> freeSpace
    storageStatusSummary = commands.getoutput(cmd).split()
    strStorageCapacity   = storageStatusSummary[6]
    strStorageFreeSpace  = storageStatusSummary[8]
    # fix the format of the relevant string, i.e. strip the ending 'g' character
    strStorageCapacity  = strStorageCapacity.replace("g", "")
    strStorageFreeSpace = strStorageFreeSpace.replace("g", "")
    # check the sanity of the strings and convert into float
    try:
        storageCapacity = float(strStorageCapacity)*1.0e9
    except ValueError:
        print ' ERROR -- cannot read storage capacity, aborting.'
        os._exit(1)
    try:
        storageFreeSpace = float(strStorageFreeSpace)*1.0e9
    except ValueError:
        print ' ERROR -- cannot read storage free space, aborting.'
        os._exit(1)
    return storageCapacity, storageFreeSpace

def makeHtmlBody(outputHtml,releaseAmount):
    # define the color string used to highlight the dataset that would
    # be deleted in case of a positive trigger of the cache release
    colorStringDanger = ", null, {\'style\': \'color: red;\'}"
    # define the color string used to highlight the dataset that are
    # currently not present in cache
    colorStringDeleted = ", null, {\'style\': \'color: blue;\'}"
    freedSpaceSum = 0
    lineCounter = 0
    # loop on the ordered DB and dump the datasets into an html file
    # note that the DB is already ordered according to the ranking algo
    # to keep the ordering use directly the DB and avoid the handle
    sql = "SELECT * FROM DatasetStatus"
    cursor.execute(sql)
    results = cursor.fetchall()
    numOfDatasets = str(len(results)) 
    # add rows to to the webtable to fit all datasets in the DB
    thisLine = '  data.addRows(' + str(numOfDatasets) + ');'
    outputHtml.write(thisLine + "\n")
    # start loop
    for row in results:
        dataset = row[0]
        dbDataset = datasetStati.retrieveElement(dataset)
        # dataset deletion will increase free space only if dataset is present in cache
        if (dbDataset.inCache):
            freedSpaceSum += dbDataset.size
        # if dataset is not anymore in cache highlight dataset with specific color (blue)
        if (not dbDataset.inCache):
            thisLine = '  data.setCell(' + str(lineCounter) + ',0,\'' + dataset + '\'' + colorStringDeleted + ');'
        # if dataset is in cache and in danger zone highlight dataset with specific color (red)
        elif (dbDataset.inCache and freedSpaceSum < releaseAmount):
            thisLine = '  data.setCell(' + str(lineCounter) + ',0,\'' + dataset + '\'' + colorStringDanger + ');'
        # if dataset is in cache and not in danger zone use default color (black)
        else:
            thisLine = '  data.setCell(' + str(lineCounter) + ',0,\'' + dataset + '\');'
        outputHtml.write(thisLine + "\n")
        thisLine = '  data.setCell(' + str(lineCounter) + ',1,' + str(dbDataset.nUsed) + ');'
        outputHtml.write(thisLine + "\n")
        thisLine = '  data.setCell(' + str(lineCounter) + ',2,' + str(dbDataset.nDownloads) + ');'
        outputHtml.write(thisLine + "\n")
        thisLine = '  data.setCell(' + str(lineCounter) + ',3,' + str(int(dbDataset.inCache)) + ');'
        outputHtml.write(thisLine + "\n")
        thisLine = '  data.setCell(' + str(lineCounter) + ',4,' + str(dbDataset.time) + ');'
        outputHtml.write(thisLine + "\n")
        thisLine = '  data.setCell(' + str(lineCounter) + ',5,' + str(dbDataset.size/1.0e9) + ');'
        outputHtml.write(thisLine + "\n")

        lineCounter += 1
    return


def makeHtmlHeader(outputHtml):
    # Prepare html file header 
    header_str = """\
<html>
<head>
<font color="orange">Hints</font>:<br> 
* You can sort the table, just click on the fields<br>
* Pass the mouse around the cells and click it<br>
<font color="green">Legend</font>:<br> 
* <font color="blue">Blue datasets are not present in cache</font><br>
* <font color="red">Red datasets are present in cache and in danger zone, i.e. will be deleted at the next deletion trigger</font><br>

<script type="text/javascript"
src="http://www.google.com/jsapi"></script>
<script type="text/javascript">
google.load("visualization", "1", {packages:["table"]});
google.setOnLoadCallback(drawTable);
function drawTable() {
  var data = new google.visualization.DataTable();

  data.addColumn('string',  'Dataset name');
  data.addColumn('number',  'Number of accesses');
  data.addColumn('number',  'Number of downloads');
  data.addColumn('number',  'Is stored in cache');
  data.addColumn('number',  'Last access time (UT)');
  data.addColumn('number',  'Size [GB]');\
    """

    # Print the file header into the outputHtml file 
    print >> outputHtml, header_str
    return

def makeHtmlTail(outputHtml):
    # close the main table
    tailerStr = """\
  var table = new google.visualization.Table(document.getElementById('table_div'));
  table.draw(data, {allowHtml: true, showRowNumber: false});
  }
</script>
</head>

<body>
<div id="table_div"></div>\
    """
    print >>outputHtml, tailerStr
  
    # put the current time in the webpage tail
    localtime = time.asctime( time.localtime(time.time()) )
    tailerStr = """<p align="center"><font size="3" color="blue"><b>Last Refresh:""" + localtime
    print >>outputHtml, tailerStr
  
    tailerStr = """\
</body>
</html>
    """
    print >>outputHtml, tailerStr
    return


# - M A I N ----------------------------------------------------------------------------------------

# Check the number of input arguments
if len(sys.argv) < 3:
    print "\n Usage: ", sys.argv[0], \
          " rel_frac html_output_file"
    sys.exit(1)

# Say what we are doing 
localtime = time.asctime( time.localtime(time.time()) )
print " \n "
print " ============================================================================================= "
print " " + localtime + " : Block " + sys.argv[0] + " is starting."
print " ============================================================================================= "

# Get the input arguments
releaseFrac    = float(sys.argv[1])
outputHtmlName = sys.argv[2]
print " INFO - output html file is " + outputHtmlName

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
releaseAmount = float(releaseFrac*storageCapacity)

# Open the HTML output file in write mode
outputHtml = open(outputHtmlName, 'w')

# Make the HTML file header
makeHtmlHeader(outputHtml)

# Make the HTML file body
makeHtmlBody(outputHtml,releaseAmount)

# Make the HTML file tail
makeHtmlTail(outputHtml)

# Close the html file 
outputHtml.close()

# Disconnect from server
db.disco()
sys.exit(1)


