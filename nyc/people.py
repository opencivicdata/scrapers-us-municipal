import collections
import datetime
import re

from legistar.people import LegistarAPIPersonScraper, LegistarPersonScraper
from pupa.scrape import Person, Organization

from .secrets import TOKEN


class NYCPersonScraper(LegistarAPIPersonScraper):
    BASE_URL = 'https://webapi.legistar.com/v1/nyc'
    WEB_URL = 'http://legistar.council.nyc.gov'
    TIMEZONE = 'US/Eastern'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.params = {'Token': TOKEN}

    def scrape(self):
        web_scraper = LegistarPersonScraper(None, None, fastmode=(self.requests_per_minute == 0))
        web_scraper.MEMBERLIST = 'http://legistar.council.nyc.gov/DepartmentDetail.aspx?ID=6897&GUID=CDC6E691-8A8C-4F25-97CB-86F31EDAB081&Mode=MainBody'

        web_info = {}

        for member, _ in web_scraper.councilMembers():
            web_info[member['Person Name']['label']] = member

        city_council, = [body for body in self.bodies()
                         if body['BodyName'] == 'City Council']

        terms = collections.defaultdict(list)

        public_advocates = { # Match casing to Bill De Blasio as council member
            'The Public Advocate (Mr. de Blasio)': 'Bill De Blasio',
            'The Public Advocate (Ms. James)': 'Letitia James',
        }

        for office in self.body_offices(city_council):
            name = office['OfficeRecordFullName']
            name = public_advocates.get(name, name)

            terms[name].append(office)

            # Add past members (and advocates public)
            if name not in web_info:
                web_info[name] = collections.defaultdict(lambda: None)

        members = {}

        for member, offices in terms.items():
            member = member.strip()  # Remove trailing space

            p = Person(member)

            web = web_info.get(member)

            for term in offices:
                role = term['OfficeRecordTitle']

                if role == 'Public Advocate':
                    role = 'Non-Voting Council Member'
                else:
                    role = 'Council Member'

                district = web.get('District', '').replace(' 0', ' ')

                p.add_term(role,
                           'legislature',
                           district=district,
                           start_date=self.toDate(term['OfficeRecordStartDate']),
                           end_date=self.toDate(term['OfficeRecordEndDate']))

                party = web.get('Political Party')

                if party == 'Democrat':
                    party = 'Democratic'

                if party:
                    p.add_party(party)

                if web.get('Photo'):
                    p.image = web['Photo']

                contact_types = {
                    "City Hall Office": ("address", "City Hall Office"),
                    "City Hall Phone": ("voice", "City Hall Phone"),
                    "Ward Office Phone": ("voice", "Ward Office Phone"),
                    "Ward Office Address": ("address", "Ward Office Address"),
                    "Fax": ("fax", "Fax")
                }

                for contact_type, (type_, _note) in contact_types.items():
                    if web.get(contact_type) and web(contact_type) != 'N/A':
                        p.add_contact_detail(type=type_,
                                             value= web[contact_type],
                                             note=_note)

                if web.get('E-mail'):
                    p.add_contact_detail(type="email",
                                         value=web['E-mail']['url'],
                                         note='E-mail')

                if web.get('Web site'):
                    p.add_link(web['Web site']['url'], note='web site')

                if web.get('Notes'):
                    p.extras = {'Notes': web['Notes']}

                if not p.sources:  # Only add sources once
                    source_urls = self.person_sources_from_office(term)
                    person_api_url, person_web_url = source_urls
                    p.add_source(person_api_url, note='api')
                    p.add_source(person_web_url, note='web')

            members[member] = p

        committee_types = ['Committee',
                           'Inactive Committee',
                           'Select Committee',
                           'Subcommittee',
                           'Task Force',
                           'Land Use']  # Committee on Land Use

        body_types = {k: v for k, v in self.body_types().items()
                      if k in committee_types}

        for body in self.bodies():
            if body['BodyTypeName'] in body_types \
                or body['BodyName'] in ('Legislative Documents Unit',
                                        'Legal and Government Affairs Division'):

                # Skip typo in API data
                if body['BodyName'] == 'Committee on Mental Health, Developmental Disability, Alcoholism, Substance Abuse amd Disability Services':
                    continue

                parent_org = PARENT_ORGS.get(body['BodyName'], 'New York City Council')

                body_name = body['BodyName']

                o = Organization(body_name,
                                 classification='committee',
                                 parent_id={'name': parent_org})

                o.add_source(self.BASE_URL + '/bodies/{BodyId}'.format(**body), note='api')
                o.add_source(self.WEB_URL + '/DepartmentDetail.aspx?ID={BodyId}&GUID={BodyGuid}'.format(**body), note='web')

                for office in self.body_offices(body):
                    # Possible roles: 'Council Member', 'MEMBER', 'Ex-Officio',
                    # 'Committee Member', None, 'CHAIRPERSON'

                    role = office['OfficeRecordTitle']

                    if role and role.lower() == 'chairperson':
                        role = 'Chairperson'
                    else:
                        role = 'Member'

                    person = office['OfficeRecordFullName'].strip()
                    person = public_advocates.get(person, person)

                    if person in members:
                        p = members[person]
                    else:
                        p = Person(person)

                        source_urls = self.person_sources_from_office(office)
                        person_api_url, person_web_url = source_urls
                        p.add_source(person_api_url, note='api')
                        p.add_source(person_web_url, note='web')

                        members[person] = p

                    p.add_membership(body_name,
                                     role=role,
                                     start_date=self.toDate(office['OfficeRecordStartDate']),
                                     end_date=self.toDate(office['OfficeRecordEndDate']))

                yield o

        for p in members.values():
            yield p


PARENT_ORGS = {
    'Subcommittee on Landmarks, Public Siting and Maritime Uses': 'Committee on Land Use',
    'Subcommittee on Libraries': 'Committee on Cultural Affairs, Libraries and International Intergroup Relations',
    'Subcommittee on Non-Public Schools': 'Committee on Education',
    'Subcommittee on Planning, Dispositions and Concessions': 'Committee on Land Use',
    'Subcommittee on Senior Centers': 'Committee on Aging',
    'Subcommittee on Zoning and Franchises': 'Committee on Land Use',
    'Subcommittee on Drug Abuse': 'Committee on Mental Health, Developmental Disability, Alcoholism, Substance Abuse and Disability Services',
    'Legislative Documents Unit': 'Mayor',
    'Legal and Government Affairs Division': 'Mayor',
}
