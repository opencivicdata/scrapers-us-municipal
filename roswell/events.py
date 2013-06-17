# ~*~ encoding: utf-8 ~*~
# Copyright (c) Sunlight Labs, 2013, under the terms of the BSD-3 clause
# license.
#
#  Contributors:
#
#    - Paul Tagliamonte <paultag@sunlightfoundation.com>


from pupa.scrape import Scraper
from larvae.event import Event
import datetime as dt
import lxml.html
import re

CAL_PAGE = ("http://www.roswell-nm.gov/evlist/index.php?view=month&year=2013&"
            "month=5&day=0&cal=0&cat=0")


class RoswellEventsScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def get_events(self):
        if self.session != self.get_current_session():
            raise Exception("Can't do that, dude")

        page = self.lxmlize(CAL_PAGE)
        days = page.xpath("//table[@class='evlist_month']//td")
        for day in days:
            when = day.xpath(".//span[@class='date_number']//a")
            when = when[0].text if when else None
            if when is None:
                continue
            events = day.xpath(".//a[contains(@href, 'event.php')]")
            for event in events:
                yield self.scrape_event_page(event)

    def scrape_event_page(self, event):
        url = event.attrib['href']
        page = self.lxmlize(url)
        title = page.xpath("//h2[@class='evlist_header']")
        title = title[0].text.strip() if title else None
        if title is None:
            return
        if "CANCELED" in title:
            return

        info = page.xpath("//div[@style='position:relative;margin-right:40px;']")[0]
        blocks = info.xpath(".//div")
        ret = {}
        for block in blocks:
            els = block.xpath("./*")
            if not els:
                continue
            le = els[0]

            if le.tag != 'label':
                continue

            label, div = els

            ltex = label.text_content().strip()
            dtex = div.text_content().strip()
            ret[ltex] = dtex

        when = dt.datetime.utcnow()
        date, start, end = (x.strip() for x in ret['When:'].split("\n"))
        start = re.sub("^@", "", start).strip()
        end = end.replace("-", "").strip()

        replace = [
            ('Apr', 'April'),
        ]

        skip = ["Occurs every"]

        for k, v in replace:
            date = date.replace(k, v).strip()

        if True in (x in end for x in skip):
            return

        start = "%s %s" % (date, start)
        end = "%s %s" % (date, end)
        start, end = (dt.datetime.strptime(x, "%B %d, %Y %I:%M %p") for x in (start, end))

        event = Event(
            session=self.session,
            name=title,
            location=ret['Where:'],
            when=start,
            end=end)
        event.add_source(url)
        yield event
