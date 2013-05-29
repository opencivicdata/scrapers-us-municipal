# Copyright (c) Sunlight Labs, 2013, under the terms of the BSD-3 clause
# license.
#
#  Contributors:
#
#    - Paul Tagliamonte <paultag@sunlightfoundation.com>


from pupa.scrape import Scraper
from larvae.event import Event

import datetime as dt
from functools import partial
import lxml.html

CAL_URL = ("http://www.townofcary.org/Town_Council/Meetings____"
           "Public_Notices_Calendar.htm")


class CaryEventsScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def get_events(self):
        page = self.lxmlize(CAL_URL)
        events = page.xpath("//div[@id='ctl14_pnlCalendarAll']//td")
        for event in events:
            when = event.xpath(".//a[contains(@href, 'javascript')]")
            if when == []:
                continue
            when = when[0]

            dom = when.text  # day of month
            hrefs = event.xpath(".//a[contains(@href, 'htm')]")
            for href in hrefs:
                for e in self.scrape_event(href):
                    yield e


    def scrape_event(self, href):
        page = self.lxmlize(href.attrib['href'])
        what = page.xpath("//td[@id='ctl14_ctl16_tdTitleCell']")[0].text
        info = page.xpath("//div[@id='ctl14_pnlEvent']//table//table//tr")[1:]
        ret = {
            "Location:": "Unknown"
        }
        for tr in info:
            tds = tr.xpath(".//td")
            if len(tds) < 2:
                continue
            what, data = [tds.pop(0).text_content().strip() for x in range(2)]
            ret[what] = data

        agendas = page.xpath("//a[contains(@title, 'Meeting Agenda')]")
        if agendas:
            for agenda in agendas:
                print "Agenda:", agenda.attrib['href']

        t = ret['Time:']
        start_time, end_time = t, None
        if "-" in t:
            start_time, end_time = (x.strip() for x in t.split("-", 1))

        start_time = "%s %s" % (ret['Date:'], start_time)
        dts = "%B %d, %Y %I:%M %p"
        start = dt.datetime.strptime(start_time, dts)

        end = None
        if end_time:
            end = "%s %s" % (ret['Date:'], end_time)
            end = dt.datetime.strptime(end, dts)

        kwargs = {}
        if end:
            kwargs['end'] = end

        e = Event(description=what,
                  location=ret['Location:'],
                  start=start,
                  **kwargs)
        e.add_source(href.attrib['href'])
        yield e
