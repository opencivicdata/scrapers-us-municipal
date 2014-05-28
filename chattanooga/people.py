from pupa.scrape import Scraper
from pupa.scrape.helpers import Legislator, Organization

import re
from lxml import html

chair_finder = re.compile(r'Council(wo)?man ([^,]+), Chair', re.IGNORECASE)
chair_finder_lame = re.compile(r'Chair(wo)?man of this committee is Council(wo)?man ([^.]+)\.', re.IGNORECASE)
phone_finder = re.compile(r'Phone: (\([\d]{3}\) ?[\d]{3}-[\d]{4})', re.IGNORECASE)

COUNCIL_PERSONS =   {}
EMAILS  =   {
    "Freeman": "freeman_m@chattanooga.gov",
    "Smith": "smith_ken@chattanooga.gov",
    "Berz": "berz_c@chattanooga.gov",
    "Anderson": "anderson_c@chattanooga.gov",
    "Hakeem": "hakeem_y@chattanooga.gov",
    "Grohn": "grohn_larry@chattanooga.gov",
    "Gilbert": "gilbert_r@chattanooga.gov",
    "Mitchell": "mitchell_jerry@chattanooga.gov",
    "Henderson": "henderson_chip@chattanooga.gov"
}

class ChattanoogaCouncilPersonScraper(Scraper):

    def _url_to_html(self, url):
        page = html.fromstring(self.urlopen(url))
        page.make_links_absolute(url)
        return page

    def get_people(self):
        council     =   Organization(
                            'Chattanooga City Council',
                            classification='commission'
                        )
        council.add_source('http://www.chattanooga.gov/city-council')
        self.council = council

        yield council
        yield self._yield_people()
        yield self._yield_committees()

    def _yield_committees(self):
        page = self._url_to_html('http://www.chattanooga.gov/city-council/committees')
        for committee in page.xpath('//div[@id="above-content"]//ul[@class="nav"]//a'):
            committee_name = committee.text_content().strip()
            committee_url = committee.get('href')
            committee_page = self._url_to_html(committee_url)

            comm    =   Organization(
                            committee_name,
                            classification='committee'
                        )

            comm.add_source(committee_url)

            chairperson = chair_finder.search(committee_page.text_content())
            if chairperson == None:
                chairperson = chair_finder_lame.search(committee_page.text_content())
            if chairperson:
                chairperson = chairperson.groups()[-1].split(' ')[-1]
                comm.add_post('Chairman', 'chairman')
                if chairperson in COUNCIL_PERSONS:
                    COUNCIL_PERSONS[chairperson].add_membership(comm, role='chairman')
            yield comm

    def _yield_people(self):
        page = self._url_to_html('http://www.chattanooga.gov/city-council/council-members')
        for person in page.xpath('//div[@id="above-content"]//ul[@class="nav"]//a'):
            person_name = person.text_content().strip().split(', ')[0]
            person_last_name = person_name.split(' ')[-1]
            person_district = person.text_content().strip().split(', ')[1].replace('District ', '')
            person_url = person.get('href')
            person_page = self._url_to_html(person_url)
            person_image = None
            for image in person_page.xpath('//div[@id="content"]//img'):
                if image.get('src', '').lower().find(person_last_name.lower()) > -1:
                    person_image = image.get('src')
            person_gender = 'f' if person_page.text_content().lower().find('councilwoman') > -1 else 'm'
            person_phone = phone_finder.search(person_page.text_content())
            if person_phone:
                person_phone    =   person_phone.group(1)

            council_person =    Legislator(
                                    person_name,
                                    person_district,
                                    gender = person_gender,
                                    image = person_image,
                                )

            council_person.add_source(person_url)
            council_person.add_membership(self.council, role = 'member')

            if person_phone:
                council_person.add_contact_detail('phone', person_phone, None)

            if person_last_name in EMAILS:
                council_person.add_contact_detail('email', EMAILS[person_last_name], None)

            COUNCIL_PERSONS[person_last_name]   =   council_person

            yield council_person
