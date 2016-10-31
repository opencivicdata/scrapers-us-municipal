from pupa.scrape import Scraper
from pupa.scrape import Event

import lxml.html
from datetime import datetime
import pytz

DUPLICATE_EVENT_URLS = ('http://miamidade.gov/wps/Events/EventDetail.jsp?eventID=445731',)

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

                if link in DUPLICATE_EVENT_URLS:
                    continue

                if title == "Mayor's FY 2016-17 Proposed Budget Public Meeting":
                    continue

                if not description:
                    description = ""

                status = "confirmed"
                if "cancelled" in title.lower():
                    status = "cancelled"

                e = Event(name=title,
                            start_time=when,
                            timezone="US/Eastern",
                            location_name=where,
                            description=description,
                            status=status)
                
                e.add_source(link)
                yield e

            e = Event(name="Mayor's FY 2016-17 Proposed Budget Public Meeting",
                      start_time=local_timezone.localize(datetime.strptime('08/08/16 06:00PM', '%m/%d/%y %H:%M%p')),
                      timezone="US/Eastern",
                      location_name='111 NW 1st Street',
                      description='Pursuant to Section 2-1800A of the County Code, a Public Meeting has been scheduled by the Honorable Carlos A. Gimenez, Mayor, Miami-Dade County, to discuss the FY 2016-17 budget, tax rates, and fee changes.',
                      status='confirmed')
            e.add_source('http://miamidade.gov/wps/Events/EventDetail.jsp?eventID=447192')
            yield e
