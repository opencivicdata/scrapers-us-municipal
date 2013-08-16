from pupa.scrape import Scraper
from pupa.models import Person, Organization

from .utils import Urls

legislators_url = (
    'http://www.cityoftemecula.org/Temecula/Government/'
    'CouncilCommissions/CityCouncil/')


class PersonScraper(Scraper):

    def get_people(self):
        urls = Urls(dict(list=legislators_url), self)

        council = Organization(
            'Temecula City Council',
            classification='legislature')
        yield council

        for tr in urls.list.xpath('//table[2]//tr')[1:]:

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
            person.add_source(urls.list.url)
            person.add_source(detail_url)

            yield person
