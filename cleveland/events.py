# Copyright (c) Sunlight Labs, 2013, under the terms of the BSD-3 clause
# license.
#
#  Contributors:
#
#    - Paul Tagliamonte <paultag@sunlightfoundation.com>

from pupa.scrape import Scraper

import datetime as dt
import lxml.html
import re

# events
CLICK_INFO = re.compile(r"CityCouncil\.popOverURL\('(?P<info_id>\d+)'\);")
ORD_INFO = re.compile(r"Ord\. No\. (?P<ord_no>\d+-\d+)")
AJAX_ENDPOINT = ("http://www.clevelandcitycouncil.org/plugins/NewsToolv7/"
                 "public/calendarPopup.ashx")


class ClevelandEventScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def get_events(self):
        page = self.lxmlize("http://www.clevelandcitycouncil.org/calendar/")
        events = page.xpath("//ul[contains(@class, 'committee-events')]//li")
        for event in events:
            print(event)
            string = event.text_content()

            po = CLICK_INFO.match(event.xpath(".//span")[0].attrib['onclick'])
            if po is None:
                continue

            poid = po.groupdict()['info_id']  # This is used to get more deetz on

            popage = self.popOverUrl(poid)
            when = dt.datetime.strptime(popage.xpath("//strong")[0].text,
                                        "%B %d, %Y @ %I:%M %p")
            who = popage.xpath("//h1")[0].text
            related = []

            for item in popage.xpath("//div"):
                t = item.text
                if t is None:
                    continue

                t = t.strip()
                for related_entity in ORD_INFO.findall(t):
                    related.append({
                        "ord_no": related_entity,
                        "what": t
                    })

            print who, when, related
            raise Exception  # XXX: Needs work


    def popOverUrl(self, poid):
        data = {
            "action": "getCalendarPopup",
            "newsid": poid
        }
        page = urllib2.urlopen(AJAX_ENDPOINT, urllib.urlencode(data))
        page = lxml.html.fromstring(page.read())
        page.make_links_absolute(AJAX_ENDPOINT)
        return page
