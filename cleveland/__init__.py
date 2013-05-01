# Copyright (c) Sunlight Labs, 2013, under the terms of the BSD-3 clause
# license.
#
#  Contributors:
#
#    - Paul Tagliamonte <paultag@sunlightfoundation.com>

from pupa.scrape import Jurisdiction, Scraper, Legislator
from larvae.organization import Organization
from larvae.person import Person

import lxml.html
import re


INFOSLUG = re.compile(r"Ward (?P<district>\d+) Council(?P<gender>.*)")


class Boston(Jurisdiction):
    jurisdiction_id = 'us-oh-cle'

    def get_metadata(self):
        return {'name': 'Cleveland',
                'legislature_name': 'Cleveland City Council',
                'legislature_url': 'http://www.clevelandcitycouncil.org/',
                'terms': [{'name': '2013-2014', 'sessions': ['2013'],
                           'start_year': 2013, 'end_year': 2014
                          }],
                'provides': ['person'],
                'parties': [],  # No parties on the city council
                'session_details': {'2013': {'_scraped_name': '2013'}},
                'feature_flags': [],}

    def get_scraper(self, term, session, scraper_type):
        if scraper_type == 'person':
            return ClevelandPersonScraper

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

            #for what in scraped_info.get('committees', []):
            #    p.add_committee_membership(what)
            # XXX: Resulting in ValueError: cannot resolve id: {UUID}


            yield p
