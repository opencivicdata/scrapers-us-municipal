from pupa.scrape import Scraper
from pupa.scrape import Event

import datetime as dt
import lxml.html


class BostonEventsScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def scrape(self):
        url = "http://meetingrecords.cityofboston.gov/sirepub/meetresults.aspx"

        page = self.lxmlize(url)
        for entry in page.xpath(
                "//tr[@style='font-family: Verdana; font-size: 12px;']"):
            name, when, links = entry.xpath(".//td")
            name = name.text.strip().replace(u"\xc2\xa0", "")
            when = when.text.strip().replace(u"\xc2\xa0", "")
            when = dt.datetime.strptime(when, "%m/%d/%Y")
            links = links.xpath(".//a")
            links = {x.text: x.attrib['href'] for x in links}
            e = Event(name=name,
                      when=when,
                      location='unknown')

            e.add_source(url)
            for note, url in links.items():
                e.add_link(note=note, url=url)

            yield e
