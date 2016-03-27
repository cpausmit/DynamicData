#!/bin/bash
#---------------------------------------------------------------------------------------------------
# Test the SmartCache infrastructure onm all our relevant architectures/OS combinations.
#---------------------------------------------------------------------------------------------------
DSET=GluGluToHToGG_M-125_7TeV-powheg-pythia6+Fall11-PU_S6_START42_V14B-v1+AODSIM
BOOK=filefi/025

if [ -z "$SMARTCACHE_DATA" ] || [ -z "$SMARTCACHE_DIR" ]
then
  echo " Please first source the setup in DynamicData/SmartCache/setup.sh"
else

  echo " Deleting the test files."

  echo "5A56FCE4-1DF0-E011-82D6-E41F13181834.root"; rm -f  $SMARTCACHE_DATA/$BOOK/$DSET/5A56FCE4-1DF0-E011-82D6-E41F13181834.root
  echo "8EA9D118-E8EF-E011-9909-00215E21DD50.root"; rm -f  $SMARTCACHE_DATA/$BOOK/$DSET/8EA9D118-E8EF-E011-9909-00215E21DD50.root
  echo "94C2366B-E4EF-E011-97C0-00215E220F78.root"; rm -f  $SMARTCACHE_DATA/$BOOK/$DSET/94C2366B-E4EF-E011-97C0-00215E220F78.root
  echo "569DFDB3-14F0-E011-9F1D-00215E2223D0.root"; rm -f  $SMARTCACHE_DATA/$BOOK/$DSET/569DFDB3-14F0-E011-9F1D-00215E2223D0.root
  echo "64338902-DDEF-E011-813C-00215E21D64E.root"; rm -f  $SMARTCACHE_DATA/$BOOK/$DSET/64338902-DDEF-E011-813C-00215E21D64E.root
  echo "D4BB3512-F1EF-E011-9639-00215E21D5BE.root"; rm -f  $SMARTCACHE_DATA/$BOOK/$DSET/D4BB3512-F1EF-E011-9639-00215E21D5BE.root
  echo "E276EBD8-DDEF-E011-9E87-001B2163C7CC.root"; rm -f  $SMARTCACHE_DATA/$BOOK/$DSET/E276EBD8-DDEF-E011-9E87-001B2163C7CC.root
  
  echo " Requesting the test files."

  ssh t3btch000 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=5A56FCE4-1DF0-E011-82D6-E41F13181834.root --dataset=$DSET --book=$BOOK
  ssh t3btch001 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=8EA9D118-E8EF-E011-9909-00215E21DD50.root --dataset=$DSET --book=$BOOK
  ssh t3btch027 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=94C2366B-E4EF-E011-97C0-00215E220F78.root --dataset=$DSET --book=$BOOK
  ssh t3btch028 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=569DFDB3-14F0-E011-9F1D-00215E2223D0.root --dataset=$DSET --book=$BOOK
  ssh t3btch084 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=64338902-DDEF-E011-813C-00215E21D64E.root --dataset=$DSET --book=$BOOK
  ssh t3btch087 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=D4BB3512-F1EF-E011-9639-00215E21D5BE.root --dataset=$DSET --book=$BOOK
  ssh t3btch100 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=E276EBD8-DDEF-E011-9E87-001B2163C7CC.root --dataset=$DSET --book=$BOOK
fi

exit 0
