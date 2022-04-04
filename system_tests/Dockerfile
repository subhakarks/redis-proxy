FROM python:3.8-alpine
ARG PIP3=pip3

ENV APP_DIR=/proxy_tests
RUN mkdir -p ${APP_DIR}
WORKDIR ${APP_DIR}
COPY requirements.txt ${APP_DIR}/
RUN ${PIP3} install -r requirements.txt
COPY . ${APP_DIR}
CMD pytest -s ${APP_DIR}/tests
