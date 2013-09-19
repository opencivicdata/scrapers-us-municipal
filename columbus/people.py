# Copyright (c) Sunlight Labs, 2013, under the terms of the BSD-3 clause
# license.
#
#  Contributors:
#
#    - Paul Tagliamonte <paultag@sunlightfoundation.com>


from pupa.scrape import Scraper, Legislator, Committee

from collections import defaultdict
import lxml.html

HOMEPAGE = "http://council.columbus.gov/"

class ColumbusPersonScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def get_people(self):
        yield self.cbus_scrape_people()

    def scrape_homepage(self, folk):
        url = folk.attrib['href']
        page = self.lxmlize(url)
        image = page.xpath(
            "//img[contains(@src, 'uploadedImages/City_Council/Members/')]"
        )[0].attrib['src']

        name = page.xpath("//div[@id='ctl00_ctl00_Body_body_cntCommon']/h3")
        name, = name

        leg = Legislator(name=name.text,
                         post_id='member',
                         image=image)
        leg.add_source(url)
        return leg

    def cbus_scrape_people(self):
        page = self.lxmlize(HOMEPAGE)
        folks = page.xpath("//div[@class='col-left']//"
                           "div[@class='gutter_text'][1]//"
                           "ul[@class='gutterlist']/li//a")
        for folk in folks:
            yield self.scrape_homepage(folk)
