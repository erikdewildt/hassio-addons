#ARG BUILD_FROM
#FROM $BUILD_FROM
FROM alpine:latest

ENV LANG C.UTF-8

RUN apk update && \
    apk upgrade && \
    apk add --no-cache curl bash nodejs gcc g++ make python3 net-tools npm

RUN npm install -g --unsafe-perm homebridge homebridge-config-ui-x

COPY ./hb_config.json /root/.homebridge/config.json
COPY start.sh /usr/local/bin

RUN chmod a+x /usr/local/bin/start.sh

EXPOSE 8581

CMD /usr/local/bin/start.sh