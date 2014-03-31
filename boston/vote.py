from pupa.scrape import Scraper
from pupa.models import Vote

import datetime as dt
import lxml
import time


DURL = "http://www.cityofboston.gov/cityclerk/rollcall/default.aspx"


class BostonVoteScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def scrape(self):
        for page in self.iterpages():
            for subject in page.xpath('//div[@class="ContainerPanel"]'):
                dates = subject.xpath(".//font[@color='#276598']/b/text()")
                motions = [x.strip() for x in subject.xpath(
                    ".//div[@style='width:260px; float:left;']/text()")]
                votes = subject.xpath(".//div[@style='width:150px; float:right;']")
                docket = subject.xpath(".//div[@class='HeaderContent']/b/text()")
                docket = list(filter(lambda x: "docket" in x.lower(), docket))
                docket = docket[0] if docket else None

                for date, motion, vote in zip(dates, motions, votes):
                    when = dt.datetime.strptime(date, "%m/%d/%Y")
                    motion = motion.strip()

                    if motion == "":
                        self.warning("Skipping vote.")
                        continue

                    v = Vote(session=self.session,
                             organization="Boston City Council",
                             type='other',
                             passed=False,
                             date=when.strftime("%Y-%m-%d"),
                             motion=motion,
                             yes_count=0,
                             no_count=0,)

                    if docket:
                        v.set_bill(docket)

                    yes, no, other = 0, 0, 0

                    vit = iter(vote.xpath("./div"))
                    vote = zip(vit, vit, vit)
                    for who, entry, _ in vote:
                        how = entry.text
                        who = who.text

                        if how == 'Y':
                            v.yes(who)
                            yes += 1
                        elif how == 'N':
                            v.no(who)
                            no += 1
                        else:
                            v.other(who)
                            other += 1

                    for count in v.vote_counts:
                        count['count'] = {
                            "yes": yes,
                            "no": no,
                            "other": other
                        }[count['vote_type']]

                    v.add_source(DURL, note='root')
                    yield v


    def do_post_back(self, form, event_target, event_argument):
        block = {name: value for name, value in [(obj.name, obj.value)
                    for obj in form.xpath(".//input")]}
        block['__EVENTTARGET'] = event_target
        block['__EVENTARGUMENT'] = event_argument
        block['ctl00$MainContent$lblCurrentText'] = (int(
            block['ctl00$MainContent$lblCurrentText']) + 1)
        block.pop("ctl00$MainContent$ctl00")

        ret = lxml.html.fromstring(self.urlopen(form.action, block))

        ret.make_links_absolute(form.action)
        return ret


    def iterpages(self):
        page = self.lxmlize(DURL)
        yield page
        while page is not None:
            yield page
            page = self.next_page(page)


    def next_page(self, page):
        time.sleep(5)
        form = page.xpath("//form[@name='aspnetForm']")[0]
        n = page.xpath("//a[contains(text(), 'Next Page')]")[0]
        nextable = n.attrib['style'] != 'display: none;'
        if nextable:
            return self.do_post_back(form, 'ctl00$MainContent$lnkNext', '')
        return None
