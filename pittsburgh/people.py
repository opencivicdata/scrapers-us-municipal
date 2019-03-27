# TODO: get legistar access and update https://pittsburgh.legistar.com/People.aspx
# and https://pittsburgh.legistar.com/Departments.aspx

import collections

from pupa.scrape import Person, Organization, Scraper
from legistar.people import LegistarAPIPersonScraper, LegistarPersonScraper


class PittsburghPersonScraper(LegistarAPIPersonScraper, Scraper):
    BASE_URL = 'http://webapi.legistar.com/v1/pittsburgh'
    WEB_URL = 'https://pittsburgh.legistar.com'
    TIMEZONE = "America/New_York"

    def scrape(self):
        body_types = self.body_types()

        city_council, = [body for body in self.bodies()
                         if body['BodyName'] == 'City Council']

        terms = collections.defaultdict(list)
        for office in self.body_offices(city_council):
            if 'VACAN' not in office['OfficeRecordFullName']:
                terms[office['OfficeRecordFullName'].strip()].append(office)

        web_scraper = LegistarPersonScraper(requests_per_minute=self.requests_per_minute)
        web_scraper.MEMBERLIST = 'https://pittsburgh.legistar.com/People.aspx'
        web_scraper.COMMITTEELIST = 'https://pittsburgh.legistar.com/Departments.aspx'

        if self.cache_storage:
            web_scraper.cache_storage = self.cache_storage

        if self.requests_per_minute == 0:
            web_scraper.cache_write_only = False

        web_info = {}
        for member in web_scraper.councilMembers():
            web_info[member['Person Name']] = member

        members = {}
        for member, offices in terms.items():
            person = Person(member)
            for term in offices:
                role = term['OfficeRecordTitle']
                person.add_term('Councilmember',
                                'legislature',
                                start_date = self.toDate(term['OfficeRecordStartDate']),
                                end_date = self.toDate(term['OfficeRecordEndDate']))

            if member in web_info:
                web = web_info[member]
                if web["E-mail"] and web["E-mail"]["label"] and web["E-mail"]["label"] != 'N/A':
                    person.add_contact_detail(type="email",
                                        value=web['E-mail']['label'],
                                        note='E-mail')

            source_urls = self.person_sources_from_office(term)
            person_api_url, person_web_url = source_urls
            person.add_source(person_api_url, note='api')
            person.add_source(person_web_url, note='web')

            members[member] = person

        for body in self.bodies():
            if body['BodyTypeId'] == body_types['Committee']:
                organization = Organization(body['BodyName'],
                             classification='committee',
                             parent_id={'name' : 'Pittsburgh City Council'})

                organization.add_source(self.BASE_URL + '/bodies/{BodyId}'.format(**body), note='api')
                organization.add_source(self.WEB_URL + '/DepartmentDetail.aspx?ID={BodyId}&GUID={BodyGuid}'.format(**body), note='web')

                for office in self.body_offices(body):






        # for person in members.values():
        #     yield person

        # for body in self.bodies():
