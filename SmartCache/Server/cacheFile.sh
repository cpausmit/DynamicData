#!/bin/bash
#---------------------------------------------------------------------------------------------------
# Download exactly one file, either interactively or submitting to condor batch system. Download
# is based on lcg-cp which we setup via /afs/cern.ch.
#
# TODO:
#
# - replace test whether file exists at the source with proper srm command, for now no test
# - setp lcg-cp more generally
# - target location is very specific, need to fix that
# - source location is also not cleanly specified
#
#                                                                               v 1.0 (Jan 31, 2014)
#                                                                             Ch.Paus (Nov 18, 2010)
#---------------------------------------------------------------------------------------------------
h=`basename $0`; id=`id -u`
LCGCP='lcg-cp';

if [ -z "$SMARTCACHE_DATA" ]
then
  SMARTCACHE_DATA=/mnt/hadoop/cms/store/user/paus
fi

# command line parameters
    file=$1
 dataset=$2
    book=$3
priority=$4
requestT=$5

# say where we are and what we do
if ! [ -z $SMARTCACHE_DEBUG ]
then
  echo " ";echo " ==== JOB ENVIRONMENT ==== ";echo " "; whoami;id;/bin/hostname;pwd;ls -lhrt
  echo " ";echo " ==== START JOB WITH ARGUMENTS: $* ====";echo " "
fi

# take care of the certificate
if [ -e "./x509up_u`id -u`" ]
then
  #rm /tmp/x509up_u`id -u`
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

# file not yet in the cache, let's get it!
echo " "; echo "Initialize UI"; echo " "
pwd
pwd=`pwd`

# legacy but works on 32 bit machines
if [ "`uname -p`" != "x86_64" ]
then
  source /afs/cern.ch/cms/LCG/LCG-2/UI/cms_ui_env_3_1.sh
else
  source /afs/cern.ch/cms/LCG/LCG-2/UI/cms_ui_env.sh
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

## test whether source is available
#ssh paus@se01.cmsaf.mit.edu ls -1 $dataFile
#if [ "$?" != "0" ]
#then
#  echo ' ERROR: requested source file does not exist or has error in access.'
#  exit 1
#fi

# make the directory with right permissions
echo " "; echo "Make directory"; echo " "
mkdir -p    `dirname $target`
chmod ug+wx `dirname $target`

echo " "; echo "Starting download now"; echo " "
echo "$LCGCP -D srmv2 -b $sourceUrl $targetUrl.smartcache.$$"
$LCGCP -D srmv2 -b  $sourceUrl $targetUrl.smartcache.$$
if [ "$?" != "0" ]
then
  echo " ERROR ($h) - file copy failed for: $source/$file"
  echo "              --> removing failed remainder ($dataFile.smartcache.$$)."
  rm $dataFile.smartcache.$$
  exit 1
else
  echo " SUCCESS ($h) - copy worked."
fi 
mv $dataFile.smartcache.$$ $dataFile

exit 0
