FROM python:3.8-alpine
ARG PIP3=pip3

ENV APP_DIR=/redis_proxy \
    LOG_DIR=/redis_proxy/logs

ENV LOG_FILE=${LOG_DIR}/redis_proxy.log

RUN mkdir -p ${APP_DIR} \
 && mkdir -p ${LOG_DIR}
WORKDIR ${APP_DIR}

COPY requirements.txt ${APP_DIR}/
RUN ${PIP3} install -r requirements.txt
COPY . ${APP_DIR}
CMD python3 ${APP_DIR}/main.py
