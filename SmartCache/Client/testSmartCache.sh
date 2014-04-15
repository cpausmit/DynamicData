#!/bin/bash
#---------------------------------------------------------------------------------------------------
# Test the SmartCache infrastructure onm all our relevant architectures/OS combinations.
#---------------------------------------------------------------------------------------------------
if [ -z "$SMARTCACHE_DATA" ] || [ -z "$SMARTCACHE_DIR" ]
then
  echo " Please first source the setup in DynamicData/SmartCache/setup.sh"
else

  echo " Deleting the test files."

  echo "00FC73F6-74FA-E111-B096-003048D15DDA.root"; rm -f  $SMARTCACHE_DATA/filefi/029/s12-h125gg-gf-v7a/00FC73F6-74FA-E111-B096-003048D15DDA.root
  echo "045EB352-6EFA-E111-845C-003048678B34.root"; rm -f  $SMARTCACHE_DATA/filefi/029/s12-h125gg-gf-v7a/045EB352-6EFA-E111-845C-003048678B34.root
  echo "06425000-70FA-E111-B50A-00304867C034.root"; rm -f  $SMARTCACHE_DATA/filefi/029/s12-h125gg-gf-v7a/06425000-70FA-E111-B50A-00304867C034.root
  echo "14B9E620-6BFA-E111-9994-00261894386B.root"; rm -f  $SMARTCACHE_DATA/filefi/029/s12-h125gg-gf-v7a/14B9E620-6BFA-E111-9994-00261894386B.root
  echo "2046980C-B2FA-E111-88ED-002618943962.root"; rm -f  $SMARTCACHE_DATA/filefi/029/s12-h125gg-gf-v7a/2046980C-B2FA-E111-88ED-002618943962.root
  echo "20502FC6-66FA-E111-B6F3-002618943896.root"; rm -f  $SMARTCACHE_DATA/filefi/029/s12-h125gg-gf-v7a/20502FC6-66FA-E111-B6F3-002618943896.root
  echo "2A9BE306-72FA-E111-8BF4-002618943913.root"; rm -f  $SMARTCACHE_DATA/filefi/029/s12-h125gg-gf-v7a/2A9BE306-72FA-E111-8BF4-002618943913.root
  echo "7E4FC25B-6DFA-E111-A61E-003048678ED2.root"; rm -f  $SMARTCACHE_DATA/filefi/029/s12-h125gg-gf-v7a/7E4FC25B-6DFA-E111-A61E-003048678ED2.root
  echo "A2BE3068-69FA-E111-91CF-0026189438BF.root"; rm -f  $SMARTCACHE_DATA/filefi/029/s12-h125gg-gf-v7a/A2BE3068-69FA-E111-91CF-0026189438BF.root
  echo "A8E5B675-6CFA-E111-83D5-003048678A80.root"; rm -f  $SMARTCACHE_DATA/filefi/029/s12-h125gg-gf-v7a/A8E5B675-6CFA-E111-83D5-003048678A80.root
  echo "CA56A54E-62FA-E111-BCE1-00261894393C.root"; rm -f  $SMARTCACHE_DATA/filefi/029/s12-h125gg-gf-v7a/CA56A54E-62FA-E111-BCE1-00261894393C.root
  echo "D0515547-68FA-E111-B849-002618FDA262.root"; rm -f  $SMARTCACHE_DATA/filefi/029/s12-h125gg-gf-v7a/D0515547-68FA-E111-B849-002618FDA262.root
  
  echo " Requesting the test files."

  # 32 bit SL6
  ssh t3btch000 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=00FC73F6-74FA-E111-B096-003048D15DDA.root --dataset=s12-h125gg-gf-v7a --book=filefi/029
  ssh t3btch001 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=045EB352-6EFA-E111-845C-003048678B34.root --dataset=s12-h125gg-gf-v7a --book=filefi/029
  ssh t3btch002 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=06425000-70FA-E111-B50A-00304867C034.root --dataset=s12-h125gg-gf-v7a --book=filefi/029
  ssh t3btch003 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=14B9E620-6BFA-E111-9994-00261894386B.root --dataset=s12-h125gg-gf-v7a --book=filefi/029
  # 32 bit SL5
  ssh t3btch037 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=A2BE3068-69FA-E111-91CF-0026189438BF.root --dataset=s12-h125gg-gf-v7a --book=filefi/029
  ssh t3btch041 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=A8E5B675-6CFA-E111-83D5-003048678A80.root --dataset=s12-h125gg-gf-v7a --book=filefi/029
  # 64 bit SL6
  ssh t3btch084 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=2046980C-B2FA-E111-88ED-002618943962.root --dataset=s12-h125gg-gf-v7a --book=filefi/029
  ssh t3btch085 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=20502FC6-66FA-E111-B6F3-002618943896.root --dataset=s12-h125gg-gf-v7a --book=filefi/029
  ssh t3btch086 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=2A9BE306-72FA-E111-8BF4-002618943913.root --dataset=s12-h125gg-gf-v7a --book=filefi/029
  ssh t3btch087 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=7E4FC25B-6DFA-E111-A61E-003048678ED2.root --dataset=s12-h125gg-gf-v7a --book=filefi/029
  # 64 bit SL5
  ssh t3btch100 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=CA56A54E-62FA-E111-BCE1-00261894393C.root --dataset=s12-h125gg-gf-v7a --book=filefi/029
  ssh t3btch092 $SMARTCACHE_DIR/Client/addDownloadRequest.py --file=D0515547-68FA-E111-B849-002618FDA262.root --dataset=s12-h125gg-gf-v7a --book=filefi/029
fi

exit 0
