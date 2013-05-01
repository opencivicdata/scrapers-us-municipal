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


MEMBER_PAGE = "http://council.nyc.gov/html/members/members.shtml"
COMMITTEE_BASE = "http://council.nyc.gov/includes/scripts"
COMMITTEE_PAGE = "{COMMITTEE_BASE}/nav_nodes.js".format(**locals())
JS_PATTERN = re.compile(r"\s+\['(?P<name>.*)','(?P<url>.*)',\],")



class NewYorkCity(Jurisdiction):
    jurisdiction_id = 'us-ny-nyc'

    def get_metadata(self):
        return {'name': 'New York City',
                'legislature_name': 'New York City Council',
                'legislature_url': 'http://council.nyc.gov/',
                'terms': [{'name': '2013-2014', 'sessions': ['2013'],
                           'start_year': 2013, 'end_year': 2014
                          }],
                'provides': ['person'],
                'parties': [{'name': 'Democrat' },
                            {'name': 'Republican'},
                            {'name': 'other'}],
                'session_details': {'2013': {'_scraped_name': '2013'}},
                'feature_flags': [],}

    def get_scraper(self, term, session, scraper_type):
        if scraper_type == 'person':
            return NewYorkCityPersonScraper

    def scrape_session_list(self):
        return ['2013']


class NewYorkCityPersonScraper(Scraper):
    def lxmlize(self, url, encoding='utf-8'):
        entry = self.urlopen(url).encode(encoding)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def get_people(self):
        yield self.nyc_scrape_committees()
        yield self.nyc_scrape_people()

    def scrape_homepage(self, homepage):
        ret = {}

        page = self.lxmlize(homepage)

        ret['image'] = page.xpath(
            "//td[@class='inside_top_image']//img")[0].attrib['src']

        bio = page.xpath("//td[@class='inside_sub_feature']")[0]
        ret['bio'] = bio.text_content()

        #infobox = page.xpath("//td[@class='inside_top_text']")[0]
        #infobits = infobox.xpath(".//strong")
        #for entry in infobox:
        #    k, v = entry.text, entry.tail
        #    if k == "Committees":
        #        print v

        return ret


    def get_committees(self):
        page = self.urlopen(COMMITTEE_PAGE)
        active = False
        for line in page.splitlines():
            if "['Committees','" in line:
                active = True
                continue
            if active and not line.endswith("',],"):
                active = False
                continue

            if active:
                line = JS_PATTERN.match(line)
                if line is None:
                    continue

                ret = line.groupdict()
                encoding_lame_bits = {
                    "\\'": "'"
                }
                for k, v in encoding_lame_bits.items():
                    ret['name'] = ret['name'].replace(k, v)

                ret['url'] = "%s/%s" % (COMMITTEE_BASE, ret['url'])
                yield ret


    def scrape_committee_homepage(self, url):
        ret = {"people": []}
        page = self.lxmlize(url, encoding='utf-8')
        people = page.xpath("//td[@class='inside_sub_feature']//p")
        if len(people) != 3:
            print "EMPTY COMMITTEE: ", url
            return ret

        people = people[1]
        ret['people'] = people.text_content().split("\n")
        return ret


    def nyc_scrape_committees(self):
        for committee in self.get_committees():
            name, url = [committee[x] for x in ["name", "url"]]
            info = self.scrape_committee_homepage(url)
            for person in info['people']:
                print "  %s" % (person)
            c = Organization(name=name,
                             classification='committee')
            c.add_source(url)
            # c.add_member(x) for x in info['people']
            yield c


    def nyc_scrape_people(self):
        page = self.lxmlize(MEMBER_PAGE)
        for entry in page.xpath("//table[@id='members_table']//tr"):
            entries = entry.xpath(".//td")
            if entries == []:
                continue

            name, district, borough, party = entries
            name = name.xpath(".//a")[0]
            homepage = name.attrib['href']
            name, district, borough, party = [x.text for x in
                                              [name, district, borough, party]]

            info = self.scrape_homepage(homepage)
            p = Legislator(name=name,
                           district=district,
                           # borough=borough,
                           party=party.strip() or "other")
            p.add_link(homepage, 'homepage')
            p.add_source(homepage)
            p.add_source(MEMBER_PAGE)
            yield p
