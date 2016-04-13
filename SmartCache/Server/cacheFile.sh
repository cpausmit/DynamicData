#!/bin/bash
#---------------------------------------------------------------------------------------------------
#
# Download exactly one file, either interactively or submitting to condor batch system. Download
# is based on lcg-cp.
#
# TODO:
#
# - replace test whether file exists at the source with proper srm command, for now no test
#
#                                                                               v 1.0 (Jan 31, 2014)
#                                                                             Ch.Paus (Nov 18, 2010)
#---------------------------------------------------------------------------------------------------
h=`basename $0`; id=`id -u`; hostname=`hostname | tr [A-Z] [a-z]`

# setup SmartCache
source /usr/local/DynamicData/SmartCache/setup.sh

# setup Tier-2 tools
source /home/cmsprod/T2Tools/setup.sh
T2LS='list'

# setup Dropbox tools
DBXCP='/home/cmsprod/Tools/Dropbox-Uploader/dropbox_uploader.sh download'

# and the rest
LCGLS='lcg-ls -D srmv2 -b';
LCGCP='lcg-cp --verbose -D srmv2 -b';
XRDCP='xrdcp -s';


function exeCmd()
{
  # execute the given command and show what we do
  echo ""
  echo " Execute: $*"
  $*
  rc=$?
  echo " --------"
  return $rc
}

function copyFile()
{
  # copy the file to it temporary location

  # first see whther file is on Tier-2
  exeCmd $T2LS /mnt/hadoop${sourceDbx}; notOnT2="$?";
  echo " Checked if file is not on Tier-2: $notOnT2"

  # show our copy option
  echo "SmartCache copy option: $SMARTCACHE_CP"
  echo ""

  # make the copy command and do it
  if [ "$SMARTCACHE_CP" == "dropbox" ] || [ "$notOnT2" == "1" ]
  then
    echo " -X-X-X-X-  U S I N G   D R O P B O X  -X-X-X-X- "
    SMARTCACHE_CP="dropbox"
    exeCmd $DBXCP $sourceDbx /tmp/$file.$SMARTCACHE_CP.$$
    chmod a+r /tmp/$file.$SMARTCACHE_CP.$$
    mv /tmp/$file.$SMARTCACHE_CP.$$ $SMARTCACHE_DATA/$book/$dataset/
  elif [ "$SMARTCACHE_CP" == "xrootd" ]
  then
    exeCmd $XRDCP $sourceXrd $targetUrl.$SMARTCACHE_CP.$$
  elif [ "$SMARTCACHE_CP" == "lcg" ]
  then
    #exeCmd $LCGCP $sourceUrl $targetUrl.$SMARTCACHE_CP.$$
    echo " FAKING IT"
    exeCmd $XRDCP $sourceXrd $target.$SMARTCACHE_CP.$$
  else
    exeCmd $LCGCP $sourceUrl $targetUrl.$SMARTCACHE_CP.$$
  fi
}

# command line parameters
    file=$1
 dataset=$2
    book=$3
priority=$4
requestT=$5

# say where we are and what we do
if ! [ -z $SMARTCACHE_DEBUG ]
then
  echo " "
  echo " ==== JOB ENVIRONMENT ==== "
  echo " "
  echo " DATE     "`date`
  echo " WHOAMI   "`whoami`
  echo " ID       "`id`
  echo " HOSTNAME "`/bin/hostname`
  echo " PWD      "`pwd`
  echo " ls -lhrt "
  ls -lhrt
  echo " "
  echo " ==== START JOB WITH ARGUMENTS: $* ===="
  echo " "
fi

# define target
dataFile="$SMARTCACHE_DATA/$book/$dataset/$file"
target=$dataFile
procId=$$

echo " DataFile: $dataFile"
echo "       to: $target"
echo ""

# first test whether file exists
testFile=`echo "$dataFile" | sed 's@/mnt/hadoop@@g' `
exeCmd hdfs dfs -Dmv32m -fs hdfs://t3serv002.mit.edu:9000 -test -e $testFile
if [ "$?" == 0 ]
then
  echo " SUCCESS ($h) - file already in smartCache."
  exit 0
fi

# make storage Urls for target (is always local) and source
targetUrl="file:///$target"
storageEle="se01.cmsaf.mit.edu"
storagePath='/srm/v2/server?SFN='
sourceUrl="srm://${storageEle}:8443${storagePath}$dataFile"

# construct equivalent xrootd location
xrdDataFile=`echo $dataFile | sed 's#/mnt/hadoop/cms##'`
sourceXrd="root://xrootd.unl.edu/$xrdDataFile"

# construct equivalent dropbox location
sourceDbx="/cms${xrdDataFile}"

# make the directory with right permissions
dir=`dirname $target`
echo " "; echo "Make directory: $dir"; echo " "
mkdir -p    $dir
chmod ug+wx $dir

# make sure to register start time and host with the database
exeCmd $SMARTCACHE_DIR/Server/updateRequest.py --book=$book --dataset=$dataset --file=$file \
                                               --startTime --host=$hostname
# start download
voms-proxy-info -all
copyFile

# dealing with an error
if [ "$?" != "0" ]
then
  echo " ERROR ($h) - file copy failed for: $target"
  echo "              --> removing failed remainder ($file.$SMARTCACHE_CP.$$)."
  exeCmd rm -f /tmp/$file.$SMARTCACHE_CP.$$

  files=`echo "$SMARTCACHE_DATA/$book/$dataset/$file.$SMARTCACHE_CP.$$ $SMARTCACHE_DATA/$book/$dataset/$file" | sed 's@/mnt/hadoop@@g'`
  exeCmd hdfs dfs -Dmv32m -fs hdfs://t3serv002.mit.edu:9000 -rm -f $files

  # also the database needs to be updated to account for the failure
  exeCmd $SMARTCACHE_DIR/Server/updateRequest.py --book=$book --dataset=$dataset --file=$file \
                                                 --completionTime --sizeGb=-0.000001
  exit 1
fi

echo " SUCCESS ($h) - copy worked."

# move file to final location
exeCmd mv $dataFile.$SMARTCACHE_CP.$$ $dataFile
#files=`echo "$dataFile.$SMARTCACHE_CP.$$ $dataFile" | sed 's@/mnt/hadoop@@g' `
#exeCmd hdfs dfs -Dmv32m -fs hdfs://t3serv002.mit.edu:9000 -mv $files

# enter the relevant transfer parameters into the database
sizeBytes=`ls -s --block-size=1 $target | cut -d' ' -f1`
sizeGb=`echo $sizeBytes | awk '{ print $1/1024/1024/1024}'`
exeCmd $SMARTCACHE_DIR/Server/updateRequest.py --book=$book --dataset=$dataset --file=$file \
                                               --completionTime --sizeGb=$sizeGb
exit 0
