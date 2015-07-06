#!/bin/bash
# --------------------------------------------------------------------------------------------------
#
# Installation script for DynamicData. There will be lots of things to test and to fix, but this is
# the starting point. This installation has to be performed as user root.
#
# TODO:
#
# + make a server and a client installation
# - define where the source is (do not assume to be in the DynamicData code directory)
# - expand the configuration
#
#                                                   L.Di Matteo, Ch.Paus: Version 0.0 (Feb 17, 2014)
# --------------------------------------------------------------------------------------------------
# Command line argument (server names: smartcache- t3btch039.mit.edu, cinderella- t3btch112.mit.edu)
if [ "$1" == "" ] || [ "$2" == "" ]
then
  echo ""
  echo " ERROR - need arguments: <smartcache-server> <cinderella-server>  (ex. dd-server.mit.edu)"
  echo ""
  exit 1
fi

SMARTCACHE_SERVER="$1"
CINDERELLA_SERVER="$2"

# Configuration parameters (this needs more work but for now)
export DYNAMICDATA_USER=cmsprod
export DYNAMICDATA_GROUP=zh

# make sure mysql is setup properly for server and clients otherwise this will not work
# check out the README

# General installation (you have to be in the directory of install script and you have to be root)

# copy the software - all machines: server and clients
if [ -d "/usr/local/DynamicData" ]
then
  # make sure to remove completely the previous installed software
  rm -rf /usr/local/DynamicData
fi
cp -r ../DynamicData /usr/local

# create log file directory structure (on server only)
if [ "`hostname | tr [A-Z] [a-z]`" == "`echo $SMARTCACHE_SERVER | tr [A-Z] [a-z] `" ]
then
  mkdir -p /var/log/DynamicData/SmartCache

  # the owner has to be $DYNAMICDATA_USER:$DYNAMICDATA_GROUP, this user runs the process
  chown ${DYNAMICDATA_USER}:${DYNAMICDATA_GROUP} -R /var/log/DynamicData
fi

# install and start daemon (on server only)
if [ "`hostname | tr [A-Z] [a-z]`" == "`echo $SMARTCACHE_SERVER | tr [A-Z] [a-z] `" ]
then
  # stop potentially existing server process
  if [ -e "/etc/init.d/smartcached" ]
  then
    /etc/init.d/smartcached stop
  fi

  # copy SmartCache daemon
  cp /usr/local/DynamicData/SmartCache/sysv/smartcached /etc/init.d/

  # start new server
  /etc/init.d/smartcached status
  /etc/init.d/smartcached start
  sleep 2
  /etc/init.d/smartcached status

  # start on boot
  chkconfig --level 345 smartcached on
fi

# create log file directory structure (on server only)
if [ "`hostname | tr [A-Z] [a-z]`" == "`echo $CINDERELLA_SERVER | tr [A-Z] [a-z] `" ]
then
  mkdir -p /var/log/DynamicData/Cinderella

  # the owner has to be $DYNAMICDATA_USER:$DYNAMICDATA_GROUP, this user runs the process
  chown ${DYNAMICDATA_USER}:${DYNAMICDATA_GROUP} -R /var/log/DynamicData
fi

# install and start daemon (on server only)
if [ "`hostname | tr [A-Z] [a-z]`" == "`echo $CINDERELLA_SERVER | tr [A-Z] [a-z] `" ]
then
  # stop potentially existing server process
  if [ -e "/etc/init.d/cinderellad" ]
  then
    /etc/init.d/cinderellad stop
  fi

  # copy Cinderella daemon
  cp /usr/local/DynamicData/Cinderella/sysv/cinderellad /etc/init.d/

  # start new server
  /etc/init.d/cinderellad status
  /etc/init.d/cinderellad start
  sleep 2
  /etc/init.d/cinderellad status

  # start on boot
  chkconfig --level 345 cinderellad on
fi

exit 0
