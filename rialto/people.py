import lxml.html

from pupa.scrape import Scraper, Legislator
from pupa.scrape import Person, Organization


class PersonScraper(Scraper):

    url = 'http://www.ci.rialto.ca.us/citycouncil_council-members.php'
    def get_people(self):

        html = self.urlopen(self.url)
        doc = lxml.html.fromstring(html)

        title_xpath = '//div[contains(@class, "biotitle")]'
        name_xpath = '//div[contains(@class, "bioname")]'
        for title, name in zip(doc.xpath(title_xpath), doc.xpath(name_xpath)):
            name = name.text_content().strip()
            title = title.text_content().strip()
            p = Legislator(name=name, post_id=title)
            p.add_source(self.url)
            yield p
