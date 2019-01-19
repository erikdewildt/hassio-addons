ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

RUN apk update && \
    apk upgrade && \
    apk add --no-cache python3

COPY requirements.txt /
COPY dropbox-backup.py /

RUN python3 -m ensurepip && \
    pip3 install --no-cache-dir -U pip setuptools && \
    pip3 install --no-cache-dir -r requirements.txt

RUN rm -rf /var/cache/apk/* && \
    rm -rf /root/.cache

RUN chmod a+x /dropbox-backup.py

CMD [ "python3", "/dropbox-backup.py" ]
