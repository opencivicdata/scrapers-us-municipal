#Copyright (c) Sunlight Labs, 2013, under the terms of the BSD-3 clause
# license.
#
#  Contributors:
#
#    - Paul Tagliamonte <paultag@sunlightfoundation.com>

from pupa.scrape import Jurisdiction, Scraper, Legislator
from larvae.organization import Organization
from larvae.person import Person

import datetime as dt
import lxml.html
import re


# events
CLICK_INFO = re.compile(r"CityCouncil\.popOverURL\('(?P<info_id>\d+)'\);")
ORD_INFO = re.compile(r"Ord\. No\. (?P<ord_no>\d+-\d+)")
AJAX_ENDPOINT = ("http://www.clevelandcitycouncil.org/plugins/NewsToolv7/"
                 "public/calendarPopup.ashx")

# people
INFOSLUG = re.compile(r"Ward (?P<district>\d+) Council(?P<gender>.*)")


class Cleveland(Jurisdiction):
    jurisdiction_id = 'us-oh-cle'

    def get_metadata(self):
        return {'name': 'Cleveland',
                'legislature_name': 'Cleveland City Council',
                'legislature_url': 'http://www.clevelandcitycouncil.org/',
                'terms': [{'name': '2013-2014', 'sessions': ['2013'],
                           'start_year': 2013, 'end_year': 2014
                          }],
                'provides': ['person', 'events'],
                'parties': [],  # No parties on the city council
                'session_details': {'2013': {'_scraped_name': '2013'}},
                'feature_flags': [],}

    def get_scraper(self, term, session, scraper_type):
        scrapers = {
            "person": ClevelandPersonScraper,
            "events": ClevelandEventScraper
        }

        if scraper_type in scrapers:
            return scrapers[scraper_type]

    def scrape_session_list(self):
        return ['2013']


class ClevelandPersonScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def get_people(self):
        yield self.cleveland_scrape_people()

    def scrape_page(self, url):
        ret = {}
        page = self.lxmlize(url)
        bio = page.xpath("//div[@class='biotab bio']")[0].text_content()
        ret['bio'] = bio
        email = page.xpath(
            "//a[contains(@href, 'mailto:')]"
        )[0].attrib['href'].strip()[len("mailto:"):]
        ret['email'] = email
        committees = page.xpath("//ul[@class='list-flat']//li")
        ret['committees'] = [x.text for x in committees]
        contact = page.xpath("//div[@class='sidebar-content']//p")[0]

        contact_details = dict([y.strip().split(":", 1) for y in [contact.text]
                                + [x.tail for x in contact.xpath(".//br")] if y
                                and ":" in y])
        ret['contact_details'] = contact_details
        return ret

    def cleveland_scrape_people(self):
        page = self.lxmlize(
            "http://www.clevelandcitycouncil.org/council-members/")

        table = page.xpath("//div[@class='standard-content column']//table")[0]
        for person in table.xpath(".//td[@align='center']"):
            strong = person.xpath(".//strong")[0]
            who = strong.text.strip()
            role = strong.xpath("./br")[0].tail.strip()
            img = person.xpath(".//img")[0].attrib['src']
            info = INFOSLUG.match(role).groupdict()

            scraped_info = {}
            page = person.xpath(".//a")
            if page != []:
                page = page[0].attrib['href']
                scraped_info = self.scrape_page(page)

            kwargs = {}
            biography = scraped_info.get('bio', None)
            if biography:
                kwargs['biography'] = biography

            p = Legislator(name=who,
                           district=info['district'],
                           gender=info['gender'],
                           image=img, **kwargs)
            p.add_source(page)

            for what in scraped_info.get('committees', []):
                p.add_committee_membership(what)

            yield p


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
