ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

RUN apk update && \
    apk upgrade && \
    apk add --no-cache curl bash nodejs gcc g++ make python3 net-tools npm ffmpeg

RUN npm install -g --unsafe-perm ffmpeg-for-homebridge homebridge homebridge-config-ui-x

# Fix paths for HomeAssistant Ingress
RUN sed -i 's#<base href="/">##' /usr/local/lib/node_modules/homebridge-config-ui-x/public/index.html && \
    sed -i 's#src="runtime-es2015#src="./runtime-es2015#' /usr/local/lib/node_modules/homebridge-config-ui-x/public/index.html && \
    sed -i 's#src="polyfills-es2015#src="./polyfills-es2015#' /usr/local/lib/node_modules/homebridge-config-ui-x/public/index.html && \
    sed -i 's#src="main-es2015#src="./main-es2015#' /usr/local/lib/node_modules/homebridge-config-ui-x/public/index.html && \
    sed -i 's#src="scripts#src="./scripts#' /usr/local/lib/node_modules/homebridge-config-ui-x/public/index.html && \
    sed -i 's#href="styles#href="./styles#' /usr/local/lib/node_modules/homebridge-config-ui-x/public/index.html

COPY ./hb_config.json /root/.homebridge/config.json
COPY start.sh /usr/local/bin

RUN chmod a+x /usr/local/bin/start.sh

EXPOSE 8581 53997

CMD /usr/local/bin/start.sh