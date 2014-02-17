#!/bin/bash
# --------------------------------------------------------------------------------------------------
# Temporary interactive process to keep smartcache alive. Was replaced with a daemon.
#
# v1.0                                                                         C.Paus (May 12, 2013)
# --------------------------------------------------------------------------------------------------
SMARTCACHE_DIR=/usr/local/DynamicData/SmartCache
SMARTCACHE_LOGDIR=/var/log/DynamicData/SmartCache

while [ 1 ]
do

  # generate log file
  tag=`date "+%s"`
  logFile=$SMARTCACHE_LOGDIR/loop-$tag.log
  touch $logFile

  # ten loops over the process with one logfile (keep it small)
  for index in `echo 0 1 2 3 4 5 6 7 8 9`
  do
    sleep 30
    echo " loop.sh  $index  -- $tag"       >> $logFile
    $SMARTCACHE_DIR/Core/reviewRequests.py >> $logFile
  done

done
