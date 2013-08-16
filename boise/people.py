from pupa.scrape import Scraper
from pupa.models import Person, Organization

from .utils import Urls

legislators_url = 'http://mayor.cityofboise.org/city-council/'


class PersonScraper(Scraper):

    def get_people(self):
        urls = Urls(dict(list=legislators_url), self)

        council = Organization('Boise City Council')
        council.add_source(legislators_url)
        yield council

        xpath = '//div[@id="content"]/div/a/@href'
        people_urls = urls.list.xpath(xpath)

        # SKip the mayor because his page has no name or email.
        people_urls = people_urls[1:]
        for url in people_urls:

            urls.add(detail=url)
            # Parse some attributes.

            image = urls.detail.xpath('//div[@id="content"]/p/img/@src').pop()
            name = urls.detail.xpath('//h1/text()').pop()

            name = name.replace('Council ', '')
            role, _, name = name.partition(' ')

            # Create legislator.
            person = Person(name, image=image)

            # Add membership on council.
            memb = person.add_membership(council, role=role)

            # Add email address.
            email_xpath = '//a[contains(@href, "mailto")]/@href'
            email = urls.detail.xpath(email_xpath).pop()[7:]
            memb.contact_details.append(
                dict(type='email', value=email, note='work'))

            # Add sources.
            person.add_source(urls.list.url)
            person.add_source(urls.detail.url)

            yield person
