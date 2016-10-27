#!/bin/bash

#Force bash if it isn't the shell already
if [ "$(ps -p "$$" -o comm=)" != "bash" ]; then
  bash "$0" "$@"
  exit "$?"
fi

#DIR should be the location of app-config.  This can be overriden for cases like
#vagrant, which execute this script from /tmp instead of from /vagrant
echo $1
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
if [ -n "$1" ]; then
  DIR="$1";
fi

# add repos
sudo yum -y install epel-release

# install python and dev tools
sudo yum groupinstall -y "Development tools"
sudo yum install -y python-devel.x86_64

# install and config
sudo yum -y install mailman

# create default list
sudo /usr/lib/mailman/bin/newlist mailman admin@project.org some_password

# requirements for mailman-api
sudo yum -y install python-pip
sudo pip install -r requirements.txt

# start mailman-api
cd /vagrant
export PATH=$PATH:/vagrant
sudo /usr/bin/python setup.py install
sudo cp init/systemd/mailman-api.service /usr/lib/systemd/system
sudo ln -s /usr/lib/systemd/system/mailman-api.service /etc/systemd/system/multi-user.target.wants/mailman-api.service

sudo systemctl start mailman-api
