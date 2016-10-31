from pupa.scrape import Scraper
from pupa.scrape import Event

import datetime as dt
import lxml.html
import re

# events
CLICK_INFO = re.compile(r"CityCouncil\.popOverURL\('(?P<info_id>\d+)'\);")
ORD_INFO = re.compile(r"Ord\. No\. (?P<ord_no>\d+-\d+)")
AJAX_ENDPOINT = ("http://www.clevelandcitycouncil.org/plugins/NewsToolv7/"
                 "public/calendarPopup.ashx")

URL = ("http://www.clevelandcitycouncil.org/calendar/"
       "?from_date={from}&to_date={til}")


class ClevelandEventScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def scrape(self):
        start = dt.datetime.utcnow()
        start = start - dt.timedelta(days=10)
        end = start + dt.timedelta(days=30)

        url = URL.format(**{"from": start.strftime("%Y/%m/%d"),
                            "til": end.strftime("%Y/%m/%d")})


        page = self.lxmlize(url)
        events = page.xpath("//ul[contains(@class, 'committee-events')]//li")

        for event in events:
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

            e = Event(name=who, when=when, location='unknown')
            e.add_source(url)

            for o in related:
                i = e.add_agenda_item(o['what'])
                i.add_bill(o['ord_no'], note='consideration')

            yield e


    def popOverUrl(self, poid):
        data = {
            "action": "getCalendarPopup",
            "newsid": poid
        }
        page = self.urlopen(AJAX_ENDPOINT, body=data)
        page = lxml.html.fromstring(page)
        page.make_links_absolute(AJAX_ENDPOINT)
        return page
