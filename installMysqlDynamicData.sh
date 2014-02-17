#!/bin/bash
# --------------------------------------------------------------------------------------------------
# Install the mysql setup for the DynamicData management, on the clients. On the server it will be
# the same plus some more. This script has to be executed on every node where people run jobs and
# therefore will be making download requests. The machines that are only used for the download
# itself do not need the mysql installation, but we should do it anyways.
#
# --------------------------------------------------------------------------------------------------
# install all essential packages
echo ""
echo " ==== Installing the software packages required"
echo ""
yum install -y mysql MySQL-python

# install the mysql configuration
echo ""
echo " ==== Installing the configurations"
echo ""
cp    /home/sysadmin/config/mysqldynamicdata/my.cnf /etc/

# install the certicates
echo ""
echo " ==== Installing the certificates"
echo ""
cp -r /home/sysadmin/config/mysqldynamicdata/mysql  /etc/

echo ""
echo " ==== Installation complete!"
echo ""

exit
