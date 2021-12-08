#!/usr/bin/env bash

# Create data dir, place default config if not exist.
mkdir -p /data
if [[ ! -f /data/config.json ]]
then
  cp /tmp/hb_config.json /data/config.json
fi

# Remove old versions if exist.
rm -rf /data/lib/node_modules/homebridge
rm -rf /data/lib/node_modules/homebridge-config-ui-x
rm -rf /data/lib/node_modules/ffmpeg-for-homebridge

# Copy node_module packages to /data
cp -pr /usr/local/lib /data

# Remove node modules from /usr/local/lib to create symlink to /data/lib
rm -rf /usr/local/lib

# Create symlink from /data to /usr/local for persistence.
ln -s /data/lib /usr/local/lib

/data/lib/node_modules/homebridge/bin/homebridge -U /data | tee /var/log/homebridge.log
