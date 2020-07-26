#!/bin/bash

folder="/home/user/montel_kiosk/"
repo_url="https://github.com/Xandir150/montel_kiosk.git"
if [ -d ${folder} ]
then
  echo -e "\e[31m${folder} already exist!\e[39m"
  echo "try to update"
  cd ${folder}
  git remote update
  count=$(git rev-list HEAD...origin/master --count)
  if [ $count -gt "0" ]
  then
    git fetch --all
    git reset --hard origin/master
	chmod -R +x
	cp -u ${folder}/etc/* /etc/systemd/system
	daemon-reload
	systemctl restart  kiosk-proxy.service
	systemctl restart  kiosk-hw.service
	systemctl restart  kiosk.service
  fi
  cd -
else
  echo "${folder} not exist"
  git clone $repo_url
  if [ $? -eq "0" ] 
  then
    echo -e "\e[32m${folder} repo clone is Ok!\e[39m"
	apt install sqlite3 -y
	cp -u ${folder}/etc/* /etc/systemd/system
	systemctl enable  kiosk-proxy.service
	systemctl enable  kiosk-hw.service
	systemctl enable  kiosk.service
	daemon-reload
	systemctl start  kiosk-proxy.service
	systemctl start  kiosk-hw.service
	systemctl start  kiosk.service
  fi
fi
