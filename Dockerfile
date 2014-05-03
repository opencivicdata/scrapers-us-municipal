FROM        paultag/pupa:latest
MAINTAINER  Paul R. Tagliamonte <paultag@sunlightfoundation.com>

RUN mkdir -p /opt/sunlightfoundation.com/
ADD . /opt/sunlightfoundation.com/scrapers-us-municipal/
RUN apt-get update && apt-get build-dep python3-lxml
RUN pip3 install lxml

RUN echo "/opt/sunlightfoundation.com/scrapers-us-municipal/" > /usr/lib/python3/dist-packages/scrapers-us-municipal.pth

ENTRYPOINT ["pupa", "update"]
