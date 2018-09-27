import collections

from pupa.scrape import Person, Organization
from legistar.people import LegistarAPIPersonScraper, LegistarPersonScraper


class SacramentoPersonScraper(LegistarAPIPersonScraper):
    BASE_URL = 'http://webapi.legistar.com/v1/sacramento'
    WEB_URL = 'https://sacramento.legistar.com'
    TIMEZONE = "America/Los_Angeles"

    def body_offices(self, body):
        body_id = body['BodyId']

        offices_url = self.BASE_URL + '/bodies/{}/OfficeRecords'.format(body_id)

        for office in self.pages(offices_url, item_key="OfficeRecordId"):
            office['OfficeRecordFullName'] = "{} {}".format(office['OfficeRecordFirstName'],
                                                            office['OfficeRecordLastName'])
            yield office

    def scrape(self):
        body_types = self.body_types()

        city_council, = [body for body in self.bodies()
                         if body['BodyName'] == 'City Council ']

        terms = collections.defaultdict(list)

        for office in self.body_offices(city_council):

            if office['OfficeRecordFullName'] != "Granicus BA":
                terms[office['OfficeRecordFullName']].append(office)

        members = {}

        for member, offices in terms.items():

            p = Person(member)
            for term in offices:
                role = term['OfficeRecordTitle']
                p.add_term(role,
                           'legislature',
                           # district = "District {}".format(int(web['District/Office'])),
                           start_date=self.toDate(term['OfficeRecordStartDate']),
                           end_date=self.toDate(term['OfficeRecordEndDate']))

            source_urls = self.person_sources_from_office(term)
            person_api_url, person_web_url = source_urls
            p.add_source(person_api_url, note='api')
            p.add_source(person_web_url, note='web')

            members[member] = p

        for body in self.bodies():
            if body['BodyTypeId'] == body_types['Standing Committees']:
                o = Organization(body['BodyName'],
                                 classification='committee',
                                 parent_id={'name': 'Sacramento City Council'})

                o.add_source(self.BASE_URL + '/bodies/{BodyId}'.format(**body), note='api')
                o.add_source(self.WEB_URL + '/DepartmentDetail.aspx?ID={BodyId}&GUID={BodyGuid}'.format(**body),
                             note='web')

                for office in self.body_offices(body):
                    # messed up record for joanna thompson
                    if office['OfficeRecordId'] == 1055:
                        continue

                    role = office['OfficeRecordTitle']
                    if role not in ("Vice Chair", "Chairperson"):
                        role = 'Member'

                    person = office['OfficeRecordFullName'].strip()
                    if person in members:
                        p = members[person]
                    else:
                        p = Person(person)

                        source_urls = self.person_sources_from_office(office)
                        person_api_url, person_web_url = source_urls
                        p.add_source(person_api_url, note='api')
                        p.add_source(person_web_url, note='web')

                        members[person] = p

                    p.add_membership(body['BodyName'],
                                     role=role,
                                     start_date=self.toDate(office['OfficeRecordStartDate']),
                                     end_date=self.toDate(office['OfficeRecordEndDate']))

                yield o

        for body in self.bodies():
            if body['BodyTypeId'] == body_types['Boards or Commission']:
                o = Organization(body['BodyName'],
                                 classification='commission',
                                 parent_id={'name': 'Sacramento City Council'})

                o.add_source(self.BASE_URL + '/bodies/{BodyId}'.format(**body), note='api')
                o.add_source(self.WEB_URL + '/DepartmentDetail.aspx?ID={BodyId}&GUID={BodyGuid}'.format(**body),
                             note='web')

                yield o

        for p in members.values():
            yield p
