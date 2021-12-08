ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

RUN apk update && \
    apk upgrade && \
    apk add --no-cache curl bash nodejs gcc g++ make python3 net-tools npm ffmpeg nginx nano

RUN npm install -g --unsafe-perm ffmpeg-for-homebridge homebridge homebridge-config-ui-x

# Fix base href for HomeAssistant Ingress
RUN sed -i 's#<base href="/">#<base href="/api/hassio_ingress/jr0GbVqkevO6VJMzsod3nD-aLofjDdKJizIS-D5a8DI/" />#' /usr/local/lib/node_modules/homebridge-config-ui-x/public/index.html && \
    sed -i 's#${window.location.host}#${window.location.host}${window.location.path}#' /usr/local/lib/node_modules/homebridge-config-ui-x/public/main-es2015.6a0995681999f14fd2d1.js


COPY rootfs /

RUN chmod a+x /usr/local/bin/start.sh

EXPOSE 8581 53997

CMD /usr/local/bin/start.sh