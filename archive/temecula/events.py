from pupa.scrape import Scraper
from pupa.scrape import Event

import datetime as dt
import lxml.html
import re


CAL_PAGE = ("http://www.cityoftemecula.org/Temecula/Visitors/Calendar.htm")


class TemeculaEventScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def cleanup(self, foo):
        foo = re.sub("\s+", " ", foo).strip()
        return foo

    def scrape(self):
        page = self.lxmlize(CAL_PAGE)
        form = page.xpath("//form[@name='Form1']")
        form = form[0] if form else None
        if form is None:
            raise Exception("Erm, crud.")
        page = self.do_post_back(form, 'Listview1$ddlCategory', '', **{
            "Listview1:ddlCategory": "1"
        })
        for event in self.scrape_event_page(page):
            event.add_source(CAL_PAGE)
            yield event


    def get_start_end(self, obj):
        date = obj['Date:']
        times = obj['time']
        start, end = ("%s %s" % (date, times[time]) for time in times)
        return (dt.datetime.strptime(x, "%A, %B %d, %Y %I:%M %p")
                for x in (start, end))


    def scrape_event_page(self, page):
        for entry in page.xpath(
                "//table[@id='Listview1_DataGrid1']//tr[@class='mainText']"):
            title = None
            ret = {}
            for block in entry.xpath(".//td[@class='mainText']"):
                entries = block.xpath("./*")
                if "table" in (x.tag for x in entries):
                    continue
                info = [self.cleanup(x.text_content()) for x in entries]
                if title is None:
                    title = info[1]
                    continue
                key = info.pop(0)
                val = None
                if "Time: " in key:
                    _, val = key.split("Time: ", 1)
                    start, end = val.split(" - ", 1)
                    val = {"start": start,
                           "end": end}
                    key = "time"
                else:
                    val = info.pop(0) if info else None

                ret[key] = val
                if info != []:
                    raise Exception("Erm. odd scrape.")

            if title is None:
                continue

            ret['title'] = title
            start, end = self.get_start_end(ret)
            ret['time']['start'], ret['time']['end'] = start, end

            event = Event(name=ret['Description:'] or "TBA",
                          location=ret['Location:'],
                          when=ret['time']['start'],
                          end=ret['time']['end'])
            yield event


    def post_back(self, form, **kwargs):
        block = {name: value for name, value in [(obj.name, obj.value)
                    for obj in form.xpath(".//input")]}
        block.update(kwargs)

        ret = lxml.html.fromstring(self.urlopen(form.action, block))

        ret.make_links_absolute(form.action)
        return ret


    def do_post_back(self, form, event_target, event_argument, **kwargs):
        block = kwargs
        event_argument = ":".join(event_argument.split("$"))
        block['__EVENTTARGET'] = event_target
        block['__EVENTARGUMENT'] = event_argument
        return self.post_back(form, **block)
