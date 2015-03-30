import logging
import lxml.html
from pupa.scrape import Person, Scraper
import re


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FergusonPersonScraper(Scraper):
    COUNCIL_URL = 'http://www.fergusoncity.com/Directory.aspx?DID=3'

    def lxmlize(self, url):
        html = self.get(url).text
        doc = lxml.html.fromstring(html)
        doc.make_links_absolute(url)
        return doc

    def get_council(self, council):
        council_doc = self.lxmlize(self.COUNCIL_URL)

        member_urls = council_doc.xpath(
            '//table[@summary="City Directory"]/tr//'
            'a[contains(@href, "/directory.aspx?EID=")]/@href')
        for member_url in member_urls:
            member_doc = self.lxmlize(member_url)

            (name, ) = member_doc.xpath('//span[@class="BioName"]/span/text()')
            (name, ) = re.findall(r'^(?:Mr\.|Mrs\.|Hon\.)?\s*(.*?)\s*$', name)

            (title, ) = member_doc.xpath(
                '//a[@class="BioLink"]/following-sibling::text()')
            (title, ) = re.findall(
                r'^Title: (Council Member(?: Ward \d)|Mayor)\s*$', title)

            try:
                (image_url, ) = member_doc.xpath(
                    '//span[@class="BioText"]//img/@src')
                print(image_url)
            except ValueError:
                image_url = ''

            member = Person(name=name,
                            image=image_url)

            member.add_membership(
                organization=council,
                role=title)
            member.add_source(member_url)

            yield member

    def scrape(self):
        (council, ) = tuple(self.jurisdiction.get_organizations())
        yield from self.get_council(council)
