#!/usr/bin/python
# --------------------------------------------------------------------------------------------------
# This script is the main worker that is executed in the daemon and will perform a full review of
# the cache status.
#
# The review of the cache situation entails a monitor of dataset usage and a corresponding database
# which keeps track of each dataset, and if required the script will trigger a cache release.
#
# 
# --------------------------------------------------------------------------------------------------
import sys, os, time

# define current python script variables starting from the environmental variables
# if variables are not assigned use default
CINDERELLA_TESTING    = os.environ.get('CINDERELLA_TESTING', "1") 
CINDERELLA_DEBUG      = os.environ.get('CINDERELLA_DEBUG', "1")     
CINDERELLA_SAFEMODE   = os.environ.get('CINDERELLA_SAFEMODE', "1")     
CINDERELLA_DATA       = os.environ.get('CINDERELLA_DATA', "/mnt/hadoop/cms/store/user/paus/")    
CINDERELLA_DIR        = os.environ.get('CINDERELLA_DIR', "/usr/local/DynamicData/Cinderella")     
CINDERELLA_LOGDIR     = os.environ.get('CINDERELLA_LOGDIR', "/var/log/DynamicData/Cinderella")  
CINDERELLA_HTMLDIR    = os.environ.get('CINDERELLA_HTMLDIR', "/home/cmsprod/public_html/Cinderella")  
CINDERELLA_RANKALGO   = os.environ.get('CINDERELLA_RANKALGO', "timeRank")
CINDERELLA_RELTHR     = os.environ.get('CINDERELLA_RELTHR', "0.92")  
CINDERELLA_RELFRAC    = os.environ.get('CINDERELLA_RELFRAC', "0.05") 
CINDERELLA_STATUS     = CINDERELLA_LOGDIR + "/cinderella.status"
CINDERELLA_HTMLSTATUS = CINDERELLA_HTMLDIR + "/cinderella.html"

# define the time t0 when we start in seconds (epoch time)
tZero = int(time.time())
tLast = tZero

# perform a full monitoring cycle of the existing datasets in our cache
tNow = int(time.time())
print '\n -=- MONITOR -=- Timing [sec]: last %d total %d'%(tNow-tLast,tNow-tZero)
cmd = CINDERELLA_DIR + '/Core/updateCacheStatus.py ' + CINDERELLA_DATA + ' >> ' + CINDERELLA_STATUS
print ' Execute: ' + cmd
if (CINDERELLA_TESTING == "0"):
    os.system(cmd)
tLast = tNow

# create a ranked list of datasets
tNow = int(time.time())
print '\n -=- RANKING -=- Timing [sec]: last %d total %d'%(tNow-tLast,tNow-tZero)
cmd = CINDERELLA_DIR + '/Core/rankCache.py ' + CINDERELLA_RANKALGO + ' >> ' + CINDERELLA_STATUS
print ' Execute: ' + cmd
if (CINDERELLA_TESTING == "0"):
    os.system(cmd)
tLast = tNow

# determine if cache needs to be release and, eventually, take action
tNow = int(time.time())
print '\n -=- CACHE RELEASE -=- Timing [sec]: last %d total %d'%(tNow-tLast,tNow-tZero)
cmd = CINDERELLA_DIR + '/Core/releaseCache.py ' + CINDERELLA_RELTHR + ' ' + CINDERELLA_RELFRAC + ' ' + CINDERELLA_SAFEMODE \
      +' >> ' + CINDERELLA_STATUS
print ' Execute: ' + cmd
if (CINDERELLA_TESTING == "0"):
    os.system(cmd)
tLast = tNow

# create an html page to show the cache status on web
tNow = int(time.time())
print '\n -=- HTML PAGE MAKING -=- Timing [sec]: last %d total %d'%(tNow-tLast,tNow-tZero)
cmd = CINDERELLA_DIR + '/Core/makeCacheWebPage.py ' + CINDERELLA_RELFRAC + ' ' + CINDERELLA_HTMLSTATUS\
      +' >> ' + CINDERELLA_STATUS
print ' Execute: ' + cmd
if (CINDERELLA_TESTING == "0"):
    os.system(cmd)
tLast = tNow

if (CINDERELLA_TESTING == "0"):
    os.system('sleep 20')
print '\n -=- REVIEW COMPLETE -=- Timing [sec]: last %d total %d'%(tNow-tLast,tNow-tZero)

sys.exit(0)
