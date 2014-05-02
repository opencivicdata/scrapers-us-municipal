import re
from itertools import groupby

from pupa.scrape import Scraper
from pupa.scrape import Person
from pupa.scrape import Organization

from .utils import Urls


legislators_url = (
    "http://www.denvergov.org/citycouncil/DenverCityCouncil/"
    "CouncilMembers/tabid/436358/Default.aspx")


class PersonScraper(Scraper):

    def scrape(self):
        urls = Urls(dict(list=legislators_url), self)

        council = Organization('Denver City Council')
        council.add_source(legislators_url)

        # Get image urls, names, detail urls, and districts.
        image_xpath = '//a[contains(@href, "councildistrict")]/img/@src'
        image_urls = urls.list.xpath(image_xpath)

        name_xpath = '//a[contains(@href, "councildistrict")]'
        names = [a.text_content() for a in urls.list.xpath(name_xpath)][:-1]
        names = filter(None, names)

        person_urls_xpath = '//a[contains(@href, "councildistrict")]/@href'
        person_urls = urls.list.xpath(person_urls_xpath)

        post_ids = []
        xpath = '//a[contains(@href, "councildistrict")]/img/ancestor::td'
        for td in urls.list.xpath(xpath):
            text = td.text_content()
            m = re.search('Council District \d+', text)
            if m:
                post_ids.append(m.group())
                continue
            m = re.search('Council At-Large', text)
            if m:
                post_ids.append('Council At-Large')

        for post_id in post_ids:
            council.add_post(post_id, post_id)
        yield council

        data = zip(image_urls, names, person_urls, post_ids)
        for image_url, name, person_url, post_id in data:

            # Create legislator.
            person = Person(name, image=image_url)

            # Add sources.
            urls.add(detail=person_url)
            person.add_source(urls.list.url, note='list')
            person.add_source(urls.detail.url, note='detail')

            # Add membership on council.
            memb = person.add_membership(council, post_id=post_id.strip())
            memb.add_source(urls.detail.url)

            xpath = '//div[@id="dnn_column3"]'
            contact_text = urls.detail.xpath(xpath)[0].text_content()

            if not contact_text.strip():
                xpath = '//div[contains(@id, "dnn_RightPaneWide")]'
                contact_text = urls.detail.xpath(xpath)[0].text_content()

            phone_regex = r'\(\d{3}\)[ -]*\d{3}-\d{4}'
            phone = re.search(phone_regex, contact_text).group()
            memb.contact_details.append(
                dict(type='phone', value=phone, note='work'))

            # Add email address.
            email_regex = r'\S+@denvergov.org'
            email = re.search(email_regex, contact_text).group()
            memb.contact_details.append(
                dict(type='email', value=email, note='work'))

            yield person
