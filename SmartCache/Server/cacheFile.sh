#!/bin/bash
#---------------------------------------------------------------------------------------------------
#
# Download exactly one file, either interactively or submitting to condor batch system. Download
# is based on lcg-cp which we setup via /afs/cern.ch.
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
LCGCP='lcg-cp -D srmv2 -b';
XRDCP='xrdcp -s';

[ -z "$SMARTCACHE_DATA" ] && ( SMARTCACHE_DATA=/mnt/hadoop/cms/store/user/paus )
[ -z "$SMARTCACHE_DIR" ] && ( SMARTCACHE_DIR=/home/cmsprod/DynamicData/SmartCache )

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

# make the directory with right permissions
echo " "; echo "Make directory"; echo " "
mkdir -p    `dirname $target`
chmod ug+wx `dirname $target`

# make sure to register start time and host with the database
echo "
$SMARTCACHE_DIR/Server/updateRequest.py --book=$book --dataset=$dataset --file=$file \
                                        --startTime --host=$hostname
"
$SMARTCACHE_DIR/Server/updateRequest.py --book=$book --dataset=$dataset --file=$file \
                                        --startTime --host=$hostname

# start download
echo " copy:  $LCGCP $sourceUrl $targetUrl.smartcache.$$"
$LCGCP $sourceUrl $targetUrl.smartcache.$$

#echo " copy: $XRDCP $sourceXrd $targetUrl.xrdcp.$$"
#$XRDCP $sourceXrd $targetUrl.xrdcp.$$

if [ "$?" != "0" ]
then
  echo " ERROR ($h) - file copy failed for: $target"

  echo "              --> removing failed remainder ($dataFile.smartcache.$$)."
  echo " remove: rm $dataFile.smartcache.$$"
  rm $dataFile.smartcache.$$

  #echo "              --> removing failed remainder ($dataFile.xrdcp.$$)."
  #echo " remove: rm $dataFile.xrdcp.$$"
  #rm $dataFile.xrdcp.$$

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

# move file in final location

echo " move: mv $dataFile.smartcache.$$ $dataFile"
mv $dataFile.smartcache.$$ $dataFile

#echo " move: mv $dataFile.xrdcp.$$ $dataFile"
#mv $dataFile.xrdcp.$$ $dataFile

# enter the relevant transfer parameters into the database
sizeBytes=`ls -s --block-size=1 $target | cut -d' ' -f1`
sizeGb=`echo $sizeBytes | awk '{ print $1/1024/1024/1024}'`
echo "
$SMARTCACHE_DIR/Server/updateRequest.py --book=$book --dataset=$dataset --file=$file \
                                        --completionTime --sizeGb=$sizeGb
"
$SMARTCACHE_DIR/Server/updateRequest.py --book=$book --dataset=$dataset --file=$file \
                                        --completionTime --sizeGb=$sizeGb
exit 0
