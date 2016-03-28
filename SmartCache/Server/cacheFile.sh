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
#env
h=`basename $0`; id=`id -u`; hostname=`hostname | tr [A-Z] [a-z]`
LCGLS='lcg-ls -D srmv2 -b';
LCGCP='lcg-cp --verbose -D srmv2 -b';
XRDCP='xrdcp -s';
DBXCP='/home/cmsprod/Tools/Dropbox-Uploader/dropbox_uploader.sh download'

[ -z "$SMARTCACHE_DATA" ] && ( SMARTCACHE_DATA=/mnt/hadoop/cms/store/user/paus )
[ -z "$SMARTCACHE_DIR" ] && ( SMARTCACHE_DIR=/home/cmsprod/DynamicData/SmartCache )
[ -z "$SMARTCACHE_CP" ] && ( SMARTCACHE_CP=lcg )

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

  echo "$LCGLS $sourceUrl";
  $LCGLS $sourceUrl; notOnT2="$?";
  echo " Checked if file is not on Tier-2: $notOnT2"

  echo "SmartCache copy: $SMARTCACHE_CP"

  if [ "$SMARTCACHE_CP" == "dropbox" ] || [ "$notOnT2" == "1" ]
  then
    SMARTCACHE_CP="dropbox"
    echo " -X-X-X-X-  U S I N G   D R O P B O X  -X-X-X-X- "
    echo " copy: $DBXCP $sourceDbx.$SMARTCACHE_CP.$$  /tmp/$file.$SMARTCACHE_CP.$$"
    $DBXCP $sourceDbx /tmp/$file.$SMARTCACHE_CP.$$
    mv /tmp/$file.$SMARTCACHE_CP.$$ $SMARTCACHE_DATA/$book/$dataset/
  elif [ "$SMARTCACHE_CP" == "xrootd" ]
  then
    echo " copy: $XRDCP $sourceXrd $targetUrl.$SMARTCACHE_CP.$$"
    $XRDCP $sourceXrd $targetUrl.$SMARTCACHE_CP.$$
  elif [ "$SMARTCACHE_CP" == "lcg" ]
  then
    echo " copy: $LCGCP $sourceUrl $targetUrl.$SMARTCACHE_CP.$$"
    $LCGCP $sourceUrl $targetUrl.$SMARTCACHE_CP.$$
  else
    echo " copy: $LCGCP $sourceUrl $targetUrl.$SMARTCACHE_CP.$$"
    $LCGCP $sourceUrl $targetUrl.$SMARTCACHE_CP.$$
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

# take care of the certificate
if [ -e "./x509up_u`id -u`" ]
then
  export X509_USER_PROXY="./x509up_u`id -u`"
fi
echo " INFO -- using the x509 ticket: $X509_USER_PROXY"

# define target
dataFile="$SMARTCACHE_DATA/$book/$dataset/$file"
target=$dataFile
procId=$$

echo " DataFile: $dataFile"
echo "       to: $target"
echo ""

# first test whether file exists
if [ -f "$dataFile" ]
then
  echo " SUCCESS ($h) - file already in smartCache."
  exit 0
fi

# make storage Urls for target (is always local) and source
targetUrl="file:///$target"
sourceUrl="file:///$dataFile"

if [ "`echo $dataFile | grep $SMARTCACHE_DATA`" != "" ]
then
  storageEle="se01.cmsaf.mit.edu"
  storagePath='/srm/v2/server?SFN='
  sourceUrl="srm://${storageEle}:8443${storagePath}$dataFile"
elif [ "`echo $dataFile | grep /castor/cern.ch`" != "" ]
then
  storageEle='srm-cms.cern.ch'
  storagePath='/srm/managerv2?SFN='
  sourceUrl="srm://${storageEle}:8443${storagePath}$dataFile"
fi

# construct equivalent xrootd location
xrdDataFile=`echo $dataFile | sed 's#/mnt/hadoop/cms##'`
sourceXrd="root://xrootd.unl.edu/$xrdDataFile"

# construct equivalent dropbox location
sourceDbx="/cms/$xrdDataFile"

# make the directory with right permissions
echo " "; echo "Make directory"; echo " "
mkdir -p    `dirname $target`
chmod ug+wx `dirname $target`

# make sure to register start time and host with the database
exeCmd $SMARTCACHE_DIR/Server/updateRequest.py --book=$book --dataset=$dataset --file=$file \
                                               --startTime --host=$hostname

# start download
copyFile

# dealing with an error
if [ "$?" != "0" ]
then
  echo " ERROR ($h) - file copy failed for: $target"
  echo "              --> removing failed remainder ($file.$SMARTCACHE_CP.$$)."
  echo " remove: rm -f /tmp/$file.$SMARTCACHE_CP.$$
                       $SMARTCACHE_DATA/$book/$dataset/$file.$SMARTCACHE_CP.$$
                       $SMARTCACHE_DATA/$book/$dataset/$file"
  rm -f /tmp/$file.$SMARTCACHE_CP.$$ \
        $SMARTCACHE_DATA/$book/$dataset/$file.$SMARTCACHE_CP.$$ \
        $SMARTCACHE_DATA/$book/$dataset/$file

  # also the database needs to be updated to account for the failure
  echo "
  $SMARTCACHE_DIR/Server/updateRequest.py --book=$book --dataset=$dataset --file=$file \
                                          --completionTime --sizeGb=-0.000001
  "
  $SMARTCACHE_DIR/Server/updateRequest.py --book=$book --dataset=$dataset --file=$file \
                                          --completionTime --sizeGb=-0.000001
  exit 1
fi

echo " SUCCESS ($h) - copy worked."

# move file to final location
exeCmd mv $dataFile.$SMARTCACHE_CP.$$ $dataFile

# enter the relevant transfer parameters into the database
sizeBytes=`ls -s --block-size=1 $target | cut -d' ' -f1`
sizeGb=`echo $sizeBytes | awk '{ print $1/1024/1024/1024}'`
exeCmd $SMARTCACHE_DIR/Server/updateRequest.py --book=$book --dataset=$dataset --file=$file \
                                               --completionTime --sizeGb=$sizeGb
exit 0
