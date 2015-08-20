FROM        sunlightlabs/pupa:latest
MAINTAINER  Paul R. Tagliamonte <paultag@sunlightfoundation.com>

RUN mkdir -p /opt/sunlightfoundation.com/
ADD . /opt/sunlightfoundation.com/scrapers-us-municipal/
RUN echo "deb-src http://debian.lcs.mit.edu/debian/ unstable main" >> /etc/apt/sources.list
RUN apt-get update && apt-get build-dep python3-lxml -y
RUN pip3 install lxml
RUN pip3 install -r /opt/sunlightfoundation.com/scrapers-us-municipal/requirements.txt

RUN echo "/opt/sunlightfoundation.com/scrapers-us-municipal/" > /usr/lib/python3/dist-packages/scrapers-us-municipal.pth
