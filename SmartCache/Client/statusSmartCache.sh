#!/bin/bash
# --------------------------------------------------------------------------------------------------
# Status tool that will only work once executed on our cluster (condor must be accessible). If
# the environment variable N_ENTRIES is set it will use its value the default is 10 entries.
# --------------------------------------------------------------------------------------------------
[ -z "$SMARTCACHE_DIR" ] && ( SMARTCACHE_DIR=/usr/local/DynamicData/SmartCache )

N_ENTRIES="$1"
if [ ".$N_ENTRIES" == "." ]
then
  N_ENTRIES=10
fi

condor_q 2> /dev/null | tail -$N_ENTRIES

if [ "$?" == "0" ]
then
  echo ""
  echo " Smart cache download requests in condor (first $N_ENTRIES max.)"
  echo " =======================================                        "
  echo ""
  condor_q cmsprod -format " --> User: %s" Owner -format "   Args: %s\n" Args | head -$N_ENTRIES
  nRequests=`condor_q cmsprod -format " --> User: %s" Owner -format "   Args: %s\n" Args | grep '.root' | wc -l`
  echo "  total requests in condor: $nRequests"
else
  echo ""
  echo " WARNING -- Condor queues are not available, cannot query condor status."
  echo ""
fi

echo ""
echo " Smart cache database snapshot (first $N_ENTRIES max.)"
echo " ============================="

$SMARTCACHE_DIR/Client/snapshotSmartCacheDb.py >& /tmp/sc.$$.tmp
head -$N_ENTRIES  /tmp/sc.$$.tmp

nRequests=`grep '.root' /tmp/sc.$$.tmp | wc -l`
rm /tmp/sc.$$.tmp

echo "  total requests in database: $nRequests"
echo ""

exit 0
