# ~*~ encoding: utf-8 ~*~
# Copyright (c) Sunlight Labs, 2013, under the terms of the BSD-3 clause
# license.
#
#  Contributors:
#
#    - Paul Tagliamonte <paultag@sunlightfoundation.com>


from pupa.scrape import Scraper
from larvae.event import Event

from sh import pdftotext
import datetime as dt
import urllib2
import os
import re


CAL_PDF = ("http://www.cityofboise.org/city_clerk/HearingSchedule/"
           "HearingSchedule.pdf")

MONTHS = [
    "JANUARY",
    "FEBRUARY",
    "MARCH",
    "APRIL",
    "MAY",
    "JUNE",
    "JULY",
    "AUGUST",
    "SEPTEMBER",
    "OCTOBER",
    "NOVEMBER",
    "DECEMBER"
]

DATE_FINDER = re.compile(
    r"(?P<month>%s) (?P<day>\d{1,2}), (?P<year>\d{4})" % ("|".join(MONTHS))
)

TIME_FINDER = re.compile(r"\d{1,2}:\d{1,2} \w+")



class BoiseEventScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def download_file(self, url):
        fpath = os.path.basename(url)
        if not os.path.exists(fpath):
            open(fpath, 'wb').write(urllib2.urlopen(url).read())
        return fpath

    def get_events(self):
        path = self.download_file(CAL_PDF)
        target = re.sub("\.pdf$", ".txt", path)
        if not os.path.exists(target):
            pdftotext(path)

        entries = self.parse_file(open(target, 'r'))
        next(entries)  # two ignorable lines
        next(entries)

        for entry in entries:
            for e in self.handle_buffer(entry):
                e.add_source(CAL_PDF)
                yield e


    def handle_buffer(self, buf):
        dates = DATE_FINDER.findall(buf)
        if dates == []:
            return
        month, day, year = dates[0]
        _, buf = buf.split(year, 1)
        time = TIME_FINDER.findall(buf)
        time = time[0] if time else None

        all_day = time is None

        tbuf = "%s %s %s" % (month, day, year)
        fmt = "%B %d %Y"

        dt_replace = {"Noon": "PM"}
        et_replace = [["–", "-"],
                      [r"^\s+\-\s+", ""]]

        if not all_day:
            tbuf += " %s" % (time)
            fmt += " %I:%M %p"

        for k, v in dt_replace.items():
            tbuf = tbuf.replace(k, v)

        for k, v in et_replace:
            buf = re.sub(k, v, buf)

        buf = buf.strip()

        obj = dt.datetime.strptime(tbuf, fmt)
        e = Event(description=buf,
                  start=obj,
                  location="City Hall")
        yield e


    def parse_file(self, fd):
        collect = ""
        for line in fd.readlines():
            line = line.strip()
            if True in (x in line for x in MONTHS):
                yield collect
                collect = line
                continue
            collect += " " + line
