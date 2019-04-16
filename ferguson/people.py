import lxml.html
from pupa.scrape import Person, Scraper
import re


class FergusonPersonScraper(Scraper):
    COUNCIL_URL = 'http://www.fergusoncity.com/Directory.aspx?DID=3'

    def lxmlize(self, url):
        html = self.get(url).text
        doc = lxml.html.fromstring(html)
        doc.make_links_absolute(url)
        return doc

    def get_council(self):
        council_doc = self.lxmlize(self.COUNCIL_URL)

        member_urls = council_doc.xpath(
            '//table[@summary="City Directory"]/tr//'
            'a[contains(@href, "/directory.aspx?EID=")]/@href')
        for member_url in member_urls:
            member_doc = self.lxmlize(member_url)

            (name, ) = member_doc.xpath('//h1[@class="BioName"]/text()')
            (name, ) = re.findall(r'^(?:Mr\.|Mrs\.|Hon\.)?\s*(.*?)\s*$', name)

            # Returning everything into a list because the number of values returned varies 
            # depending on if the person has an email or not
            text_list = member_doc.xpath(
                '//a[@class="BioLink"]/parent::div/text()')
            title = text_list[1].strip()
            (title, ) = re.findall(
                r'^Title: (Council Member,?(?: Ward \d)|Mayor)\s*$', title)

            try:
                (image_url, ) = member_doc.xpath(
                    '//span[@class="BioText"]//img/@src')
            except ValueError:
                image_url = ''

            member = Person(name=name,
                            image=image_url,
                            primary_org='legislature',
                            role=title)

            member.add_source(member_url)

            yield member

    def scrape(self):
        yield from self.get_council()
