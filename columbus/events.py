from pupa.scrape import Scraper
from pupa.models import Event

import datetime as dt
import lxml.html
import re

PAGE = "http://council.columbus.gov/events.aspx?id=5370&menu_id=526"

EVENT_RE = re.compile("(?P<event>.*) begins at (?P<time>.*)")


class ColumbusEventScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def scrape(self):
        page = self.lxmlize(PAGE)
        events = page.xpath("//div[@class='col-middle']//ul/li")
        when = None
        for event in events:
            h3 = event.xpath("./a/h2")
            h3 = h3[0] if h3 else None
            if h3 is not None:
                when = h3.text
            else:
                if when is None:
                    self.warning("Ungrok!")
                    continue

                b, _, i = event.xpath("./p/*")
                title = b.text_content()
                event = i.text_content()

                if "NO MEETING" in event:
                    continue

                day, title = (x.strip() for x in title.split("-", 1))

                where = "Council Chambers"

                for subevent in (x.strip() for x in event.split(";")):
                    if " in " in subevent:
                        subevent, where = subevent.rsplit(" in ", 1)
                    subevent = subevent.replace(u'\xa0', ' ')

                    if "NO" in subevent and "MEETING" in subevent:
                        continue

                    if "to follow" in subevent:
                        continue

                    info = EVENT_RE.match(subevent).groupdict()
                    event, time = [info[x] for x in ['event', 'time']]

                    ampm = {
                        "a.m.": "AM",
                        "p.m.": "PM",
                    }

                    for old, new in ampm.items():
                        time = time.replace(old, new)

                    dtstring = ", ".join([day, time])

                    try:
                        etime = dt.datetime.strptime(
                            dtstring, "%m/%d/%Y, %I:%M %p")
                    except ValueError:
                        etime = dt.datetime.strptime(
                            dtstring, "%m/%d/%Y, %I%p")

                    e = Event(name=event,
                              when=etime,
                              location=where)
                    e.add_source(PAGE)
                    yield e
