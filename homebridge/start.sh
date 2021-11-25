#!/usr/bin/env bash
mkdir -p /data
if [[ ! -f /data/config.json ]]
then
  cp /root/.homebridge/config.json /data/config.json
fi
homebridge -U /data | tee /var/log/homebridge.log