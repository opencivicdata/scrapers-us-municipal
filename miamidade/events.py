from pupa.scrape import Scraper
from pupa.scrape import Event

import lxml.html
from datetime import datetime
import pytz


class MiamidadeEventScraper(Scraper):

    def lxmlize(self, url):
        html = self.get(url).text
        doc = lxml.html.fromstring(html)
        doc.make_links_absolute(url)
        return doc

    def scrape(self):
        local_timezone =  pytz.timezone("US/Eastern")
        base_calendar_url = "http://www.miamidade.gov/cob/county-commission-calendar.asp"
        #things get messy more than a few months out
        #so we're just pulling 3 months. If we want three
        #more, they are called "nxx", "nxy" and "nxz"
        months = ["cur","nex","nxw"]
        for m in months:
            doc = self.lxmlize(base_calendar_url + "?next={}".format(m))
            events = doc.xpath("//table[contains(@style,'dotted #ccc')]")
            for event in events:
                rows = event.xpath(".//tr")
                for row in rows:
                    heading, data = row.xpath(".//td")
                    h = heading.text_content().lower().replace(":","").strip()
                    if h == "event":
                        title = data.text_content()
                        link = data.xpath(".//a")[0].attrib["href"]
                    elif h == "event date":
                        when = datetime.strptime(data.text, '%m/%d/%y %H:%M%p')
                        when = local_timezone.localize(when)
                    elif h == "location":
                        where = data.text
                    elif h == "description":
                        description = data.text

                if not description:
                    description = ""

                e = Event(name=title,
                            start_time=when,
                            timezone="US/Eastern",
                            location_name=where,
                            description=description)
                
                e.add_source(link)
                yield e

