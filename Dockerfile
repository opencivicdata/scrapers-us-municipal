FROM python:3.6-slim-stretch
LABEL maintainer "DataMade <info@datamade.us>"

ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y libxml2-dev gdal-bin && \
    apt-get clean && \
    rm -rf /var/cache/apt/* /var/lib/apt/lists/*

RUN mkdir /src
WORKDIR /src

COPY ./requirements.txt /src/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /src

ENTRYPOINT ["/src/docker-entrypoint.sh"]
