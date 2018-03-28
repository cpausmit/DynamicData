#!/bin/bash
#===================================================================================================
# Submit one download request. It will use cacheFile.sh script internally.
#
# Version 2.0                                                                  C.Paus (Feb 01, 2014)
# Version 1.0                                                                  C.Paus (May 09, 2013)
#===================================================================================================
# Read the arguments
if [ -z "$SMARTCACHE_DIR" ] || [ -z "$SMARTCACHE_LOGDIR" ]
then
  echo " Environment for SmartCache not properly set. EXIT!"
  exit 1
fi

if ! [ -z $SMARTCACHE_DEBUG ]
then
  echo " "
  echo "Starting data processing with arguments:"
  echo "  --> $*"
fi

    file=$1
 dataset=$2
    book=$3
priority=$4
requestT=$5

jobId=`date +%j%m%d%k%M%S`

# Prepare environment
if ! [ -z $SMARTCACHE_DEBUG ]
then
  echo " "
  echo " Request: file=$file dataset=$dataset, book=$book, priority=$priority, requestT=$requestT"
  echo " "
fi

script="$SMARTCACHE_DIR/Server/cacheFile.sh"
workDir="$SMARTCACHE_LOGDIR/condor"
mkdir -p $SMARTCACHE_LOGDIR/condor/$book/$dataset

# Preparing and submitting the condor job
# ---------------------------------------

if ! [ -z "$SMARTCACHE_DEBUG" ]
then
  echo "   $script $file $dataset $book $priority $requestT"
  echo " "
  echo "    --> working directory: $PWD"
  echo " "
fi
 
cat > submit.cmd <<EOF
Universe                = vanilla
Requirements            = (Arch == "INTEL" || (Arch == "X86_64" && Memory < 1000)) && HasFileTransfer
#Requirements            = Arch == "X86_64" && HasFileTransfer
Notification            = Error
Executable              = $script
Arguments               = $file $dataset $book $priority $requestT
Rank                    = Mips
GetEnv                  = False
Initialdir              = $workDir
Input                   = /dev/null
Output                  = $book/$dataset/${file}.out
Error                   = $book/$dataset/${file}.err
Log                     = $book/$dataset/${file}.log
use_x509userproxy       = True
should_transfer_files   = YES
when_to_transfer_output = ON_EXIT
+AccountingGroup        = "group_cmsuser.$USER"
Queue
EOF

if ! [ -z "$SMARTCACHE_DEBUG" ]
then
  condor_submit submit.cmd
  rm submit.cmd
else
  condor_submit submit.cmd >& /dev/null;
  rm submit.cmd
fi

exit 0
