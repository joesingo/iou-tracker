#!/bin/bash
socket=/run/lighttpd/iou.socket
python site.fcgi $socket &
echo $! > /var/run/iou.pid
sleep 3
chown www-data:www-data $socket
