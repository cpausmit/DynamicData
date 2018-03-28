#!/bin/bash
# --------------------------------------------------------------------------------------------------
# Script to generate the requests for all missing files and add them to the download request table.
# --------------------------------------------------------------------------------------------------
[ -z "$SMARTCACHE_DIR" ] && SMARTCACHE_DIR=/usr/local/DynamicData/SmartCache
[ -z "$CATALOG" ] && CATALOG=/home/cmsprod/catalog/t2mit
[ -z "$DATA" ] && DATA=/mnt/hadoop/cms/store/user/paus

# get the command line arguments
if [ $# -ne 2 ]
then
  echo ""
  echo " usage:  requestSample.sh  <book>  <dataset>"
  echo ""
  echo "         book    - book of the sample, ex. filefi/032"
  echo "         dataset - dataset name, ex. s12-ww-v7a"
  echo ""
  exit 1
else
  BOOK="$1"
  DATASET="$2"
fi

# say what we will do
echo ""
echo " Adding download requests to complete download of dataset: $DATASET in book: $BOOK"
echo ""

# get all files from the catalog
files=`cat $CATALOG/$BOOK/$DATASET/Files | grep -v ^# | tr -s ' ' | cut -d' ' -f2`
nFiles=`wc -l $CATALOG/$BOOK/$DATASET/Files | cut -d' ' -f1`
echo " --> found $nFiles in catalog. Checking availability and add to requests."

# create a list of existing file to avoid load on $DATA directory
exisitingFileLists=/tmp/$DATASET.$$
rm -f $exisitingFileLists
ls -1 $DATA/$BOOK/$DATASET 2> /dev/null | grep -v smartcache | grep -v xrdcp > $exisitingFileLists

# find the missing files
missingFiles=''
for file in $files
do
  exists=`grep $file $exisitingFileLists`
  if [ ".$exists" == "." ]
  then
    missingFiles="$missingFiles $file"
    echo " File $file missing."
  else
    echo " File $file already exists."
  fi
done
nFiles=`echo $missingFiles | wc -w`
if [ "$nFiles" == "0" ]
then
  echo " --> found all files in local cache ($nFiles missing). EXIT."
  exit 0
fi

echo " --> found $nFiles missing in local cache, add them to the request table."
echo ""
read -p " Do you wish to continue? [N/y] " yn
if [ "$yn" != "y" ] && [ "$yn" != "Y" ] 
then
  echo " Nothing done. EXIT."
  exit
fi

# request the missing files for download
for file in $missingFiles
do
  cmd="$SMARTCACHE_DIR/Client/addDownloadRequest.py --file=$file --dataset=$DATASET --book=$BOOK"
  echo $cmd
  $cmd
done

# cleanup
rm -f $exisitingFileLists

exit 0
