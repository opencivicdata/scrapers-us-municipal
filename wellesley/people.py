# Copyright (c) Sunlight Labs, 2013, under the terms of the BSD-3 clause
# license.
#
#  Contributors:
#
#    - Paul Tagliamonte <paultag@sunlightfoundation.com>


from pupa.scrape import Scraper, Legislator, Committee

from collections import defaultdict
import lxml.html
import re

MEMBER_LIST = "http://www.wellesleyma.gov/Pages/WellesleyMA_Clerk/elected"


class WellesleyPersonScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def get_people(self):
        yield self.wellesley_scrape_people()

    def wellesley_scrape_people(self):
        page = self.lxmlize(MEMBER_LIST)
        for row in page.xpath("//table[@frame='void']/tbody/tr")[1:]:
            role, whos, expire = row.xpath("./*")
            people = zip([x.text_content() for x in whos.xpath(".//font")],
                         [x.text_content() for x in expire.xpath(".//font")])
            thing = role.text_content()

            comm = Committee(name=thing)
            url = role.xpath(".//a")[0].attrib['href']
            comm.add_link(url=url, note='homepage')

            for person, expire in people:
                if "TBA" in person:
                    continue
                info = {}

                try:
                   info = re.match("(?P<name>.*), (?P<addr>\d+\w* .*)",
                                   person).groupdict()
                except AttributeError:
                    info = re.match("(?P<name>.*) (?P<addr>\d+\w* .*)",
                                    person).groupdict()

                leg = Legislator(name=info['name'], post_id='member')
                leg.add_contact_detail(type="address",
                                       value=info['addr'],
                                       note="Address")
                leg.add_source(MEMBER_LIST)
                yield leg

                leg.add_membership(comm)
            comm.add_source(MEMBER_LIST)
            yield comm
