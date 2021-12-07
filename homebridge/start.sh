#!/usr/bin/env bash
mkdir -p /data
if [[ ! -f /data/config.json ]]
then
  cp /root/.homebridge/config.json /data/config.json
fi

if [[ ! -d /data/lib ]]
then
  mv /usr/local/lib /data
fi
rm -rf /usr/local/lib
ln -s /data/lib /usr/local/lib

/data/lib/node_modules/homebridge/bin/homebridge -U /data | tee /var/log/homebridge.log &
nginx -c /etc/nginx/nginx.conf