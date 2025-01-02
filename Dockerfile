FROM python:3.12-alpine

ENV NAMESPACE="jupyterhub"

RUN apk add gcc
RUN pip install --upgrade pip
RUN pip install kubernetes
RUN MULTIDICT_NO_EXTENSIONS=1 pip install kopf
ADD ./service.py /src/service.py

CMD kopf run /src/service.py -A --standalone
