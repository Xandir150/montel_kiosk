#!/bin/bash

xset s noblank
xset s off
xset -dpms

unclutter -idle 0.5 -root &

#sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' /home/user/.config/chromium/Default/Preferences
#sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/'   /home/user/.config/chromium/Default/Preferences

midori -e Fullscreen -a file:///home/user/montel_kiosk/web/index.html
#/usr/bin/chromium --disable-application-cache --media-cache-size=1 --disk-cache-size=1 --noerrdialogs --disable-infobars --kiosk --disable-web-security --user-data-dir=/home/user/.config/chromium/ /home/user/montel_kiosk/web/index.html &

while true; do
   #xdotool keydown ctrl+Tab; xdotool keyup ctrl+Tab;
   sleep 10
done
