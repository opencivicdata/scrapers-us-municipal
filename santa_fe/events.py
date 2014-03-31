# ~*~ encoding: utf-8 ~*~
from pupa.scrape import Scraper
from pupa.models import Event

import datetime as dt
import lxml.html
import re


CAL_PAGE = "http://www.santafenm.gov/index.aspx?NID=1066"
DT = re.compile(r"(?P<time>\d{1,2}:\d{1,2}) (?P<ampm>AM|PM)")
WHEN = re.compile(r"DAY,\s+(?P<month>\w+)\s+(?P<dom>\d{1,2}),\s+(?P<year>\d{4})")


class SantaFeEventsScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def cleanup(self, what):
        return re.sub("\s+", " ", what).strip()

    def scrape(self):
        curdate = None
        page = self.lxmlize(CAL_PAGE)
        for el in page.xpath("//div[@id='Section1']/*"):
            if el.tag[0] == 'h':
                when = WHEN.findall(el.text_content())
                when = when[0] if when else None
                if when is None:
                    continue
                curdate = " ".join(when)

            if (el.tag == 'p'): # and el.attrib.get('class') == 'MsoNormal'):

                els = el.xpath("./*")
                agenda = el.xpath(".//a[contains(@href, 'Archive.aspx')]")
                agenda = agenda[0] if agenda else None
                if agenda is None:
                    continue

                info = self.cleanup(el.text_content())
                when = DT.findall(info)
                when = when[0] if when else None
                if when is None:
                    continue

                people = el.xpath(".//personname")
                places = el.xpath(".//place")
                time, ampm = when

                if curdate is None:
                    self.warning("Can't scrape, since I don't know what date it is")
                    continue

                tbuf = " ".join([curdate, time, ampm])
                obj = dt.datetime.strptime(tbuf, "%B %d %Y %I:%M %p")

                try:
                    _, where = info.rsplit(u"–", 1)
                except ValueError:
                    continue

                where = where.replace(u" ", " ")
                where  = re.sub("\s+", " ", where).strip()
                where = re.sub("agenda$", "", where).strip()

                event = Event(name=info, when=obj, location=where)
                event.add_source(CAL_PAGE)
                yield event
