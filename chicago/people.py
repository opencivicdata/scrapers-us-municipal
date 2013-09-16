# Copyright (c) Sunlight Labs, 2013, under the terms of the BSD-3 clause
# license.
#
#  Contributors:
#
#    - Paul Tagliamonte <paultag@sunlightfoundation.com>


from pupa.scrape import Scraper, Legislator, Committee

from collections import defaultdict
import lxml.html


MEMBER_LIST = "http://www.cityofchicago.org/city/en/about/wards.html"


class ChicagoPersonScraper(Scraper):

    def lxmlize(self, url):
        entry = self.urlopen(url)
        page = lxml.html.fromstring(entry)
        page.make_links_absolute(url)
        return page

    def get_people(self):
        yield self.bos_scrape_people()

    def scrape_ward(self, el):
        url = el.attrib['href']
        page = self.lxmlize(url)
        name = page.xpath("//div[@id='content-content']/h3")[0].text_content()
        badthings = [
            "Alderman"
        ]
        for thing in badthings:
            if name.startswith(thing):
                name = name[len(thing):].strip()

        district = page.xpath("//h1[@class='page-heading']/text()")[0]
        leg = Legislator(name=name, post_id=district)
        leg.add_source(url)

        type_types = {
            "City Hall Office:": ("address", "City Hall Office"),
            "City Hall Phone:": ("phone", "City Hall Phone"),
            "Phone:": ("phone", "Personal Phone"),
            "Office:": ("address", "Personal Office"),
            "Fax:": ("fax", "Fax"),
            "Fax": ("fax", "Fax"),
        }

        for row in page.xpath("//table//tr"):
            type_, val = (x.text_content().strip() for x in row.xpath("./td"))
            if val == "":
                continue

            types = [type_]
            vals = [val]

            if "\n" in type_:
                if "\n" in val:
                    types = type_.split("\n")
                    vals = val.split("\n")
                else:
                    continue

            for type_ in types:
                for val in vals:
                    ctype, note = type_types[type_]
                    leg.add_contact(ctype, val, note)

        return leg

    def bos_scrape_people(self):
        page = self.lxmlize(MEMBER_LIST)
        wards = page.xpath("//div[@id='content-content']/h4/"
                           "a[contains(@href, 'city/en/about/wards')]")
        for ward in wards:
            yield self.scrape_ward(ward)
