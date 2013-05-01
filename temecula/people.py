from pupa.scrape import Scraper
from larvae.person import Person
from larvae.organization import Organization

from .utils import PageContext

legislators_url = (
    'http://www.cityoftemecula.org/Temecula/Government/'
    'CouncilCommissions/CityCouncil/')


class PersonScraper(Scraper):

    def get_people(self):
        page = PageContext(self, dict(list=legislators_url))

        council = Organization(
            'Temecula City Council',
            classification='legislature')
        yield council

        for tr in page.urls.list.xpath('//table[2]//tr')[1:]:

            # Parse some attributes.
            name, role = tr.xpath('td/p[1]//font/text()')
            image = tr.xpath('td/img/@src').pop()

            # Create legislator.
            person = Person(name, image=image)

            # Add membership on council.
            memb = person.add_membership(council, role=role)

            # Add email address.
            email, detail_url = tr.xpath('td//a/@href')
            email = email[7:]
            memb.contact_details.append(
                dict(type='email', value=email, note='work'))

            # Add sources.
            person.add_source(page.urls.list.url)
            person.add_source(detail_url)

            yield person
