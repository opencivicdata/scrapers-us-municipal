# Copyright (c) Sunlight Labs, 2013, under the terms of the BSD-3 clause
# license.
#
#  Contributors:
#
#    - Paul Tagliamonte <paultag@sunlightfoundation.com>


from pupa.scrape import Scraper, Legislator, Committee

from collections import defaultdict
import lxml.html

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
            for person in people:
                print person
