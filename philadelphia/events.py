# ~*~ encoding: utf-8 ~*~
from pupa.scrape import Scraper
from pupa.models import Event
import datetime as dt
import lxml.html


class PhillyEventsScraper(Scraper):
    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def scrape(self):
        url = "http://phila.legistar.com/Calendar.aspx/"
        page = self.lxmlize(url)
        main = page.xpath("//table[@class='rgMasterTable']")[0]
        rows = main.xpath(".//tr")[1:]
        for row in rows:
            if "No records were found." in row.text_content():
                self.warning("Hum. They don't seem to have events?")
                continue

            (name, date, _, time, where, agenda, minutes) = row.xpath(".//td")
            # _ nom's the image next to the date on the page.

            name = name.text_content().strip()  # leaving an href on the table
            time = time.text_content().strip()
            location = where.text_content().strip()

            if "Deferred" in time:
                continue

            all_day = False
            if time == "":
                all_day = True
                when = dt.datetime.strptime(date.text.strip(),
                                            "%m/%d/%Y")
            else:
                when = dt.datetime.strptime("%s %s" % (date.text.strip(), time),
                                            "%m/%d/%Y %I:%M %p")

            event = Event(name=name, when=when, location=location)
            event.add_source(url)

            agendas = agenda.xpath(".//a[@href]")
            for a in agendas:
                event.add_link(a.text, a.attrib['href'])

            minutes = minutes.xpath(".//a[@href]")
            for minute in minutes:
                event.add_link(minute.text, minute.attrib['href'])

            yield event
