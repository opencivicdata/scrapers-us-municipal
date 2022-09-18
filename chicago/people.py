import collections

from pupa.scrape import Person, Organization, Scraper
from legistar.people import LegistarAPIPersonScraper, LegistarPersonScraper

class ChicagoPersonScraper(LegistarAPIPersonScraper, Scraper):
    BASE_URL = 'http://webapi.legistar.com/v1/chicago'
    WEB_URL = 'https://chicago.legistar.com'
    TIMEZONE = "America/Chicago"

    def scrape(self):
        body_types = self.body_types()

        city_council, = [body for body in self.bodies()
                         if body['BodyName'] == 'City Council']

        terms = collections.defaultdict(list)
        for office in self.body_offices(city_council):
            if 'vacan' not in office['OfficeRecordFullName'].lower():
                terms[office['OfficeRecordFullName'].strip()].append(office)

        web_scraper = LegistarPersonScraper(requests_per_minute = self.requests_per_minute)
        web_scraper.MEMBERLIST = 'https://chicago.legistar.com/DepartmentDetail.aspx?ID=12357&GUID=4B24D5A9-FED0-4015-9154-6BFFFB2A8CB4&R=8bcbe788-98cd-4040-9086-b34fa8e49881'
        web_scraper.ALL_MEMBERS = '3:3'

        if self.cache_storage:
            web_scraper.cache_storage = self.cache_storage

        if self.requests_per_minute == 0:
            web_scraper.cache_write_only = False


        web_info = {}
        for member, _ in web_scraper.councilMembers({'ctl00$ContentPlaceHolder$lstName' : 'City Council'}):
            web_info[member['Person Name']['label']] = member


        web_info['Balcer, James'] = collections.defaultdict(lambda : None)
        web_info['Fioretti, Bob'] = collections.defaultdict(lambda : None)
        web_info['Balcer, James']['Ward/Office'] = 11
        web_info['Fioretti, Bob']['Ward/Office'] = 2
        
        members = {}
        for member, offices in terms.items():
            web = web_info[member]
            p = Person(member)
            for term in offices:
                role = term['OfficeRecordTitle']
                p.add_term('Alderman',
                           'legislature',
                           district = "Ward {}".format(int(web['Ward/Office'])),
                           start_date = self.toDate(term['OfficeRecordStartDate']),
                           end_date = self.toDate(term['OfficeRecordEndDate']))

            if web.get('Photo'):
                p.image = web['Photo']

            contact_types = {
                "City Hall Address": ("address", "City Hall Address"),
                "City Hall Phone": ("voice", "City Hall Phone"),
                "Ward Office Phone": ("voice", "Ward Office Phone"),
                "Ward Office Address": ("address", "Ward Office Address"),
                "Fax": ("fax", "Fax")
            }

            for contact_type, (type_, _note) in contact_types.items():
                if web[contact_type] and web[contact_type] != 'N/A':
                    p.add_contact_detail(type=type_,
                                         value= web[contact_type],
                                         note=_note)

            if web["E-mail"] and web["E-mail"]["label"] and web["E-mail"]["label"] != 'N/A':
                p.add_contact_detail(type="email",
                                     value=web['E-mail']['label'],
                                     note='E-mail')


            if web['Website']:
                p.add_link(web['Website']['url'])

            source_urls = self.person_sources_from_office(term)
            person_api_url, person_web_url = source_urls
            p.add_source(person_api_url, note='api')
            p.add_source(person_web_url, note='web')


            members[member] = p

        for body in self.bodies():
            if body['BodyTypeId'] == body_types['Committee']:
                o = Organization(body['BodyName'],
                                 classification='committee',
                                 parent_id={'name' : 'Chicago City Council'})

                o.add_source(self.BASE_URL + '/bodies/{BodyId}'.format(**body), note='api')
                o.add_source(self.WEB_URL + '/DepartmentDetail.aspx?ID={BodyId}&GUID={BodyGuid}'.format(**body), note='web')

                for office in self.body_offices(body):
                    # messed up record for joanna thompson
                    if office['OfficeRecordId'] in {1055, 2513, 4383}:
                        continue
                        
                    role = office['OfficeRecordTitle']
                    if role not in ("Vice Chair", "Chairman"):
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

                    try:
                        end_date = self.toDate(office['OfficeRecordEndDate'])
                    except TypeError:
                        end_date = ''
                    p.add_membership(body['BodyName'],
                                     role=role,
                                     start_date=self.toDate(office['OfficeRecordStartDate']),
                                     end_date=end_date)

                yield o

        for body in self.bodies():
            if body['BodyTypeId'] == body_types['Joint Committee']:
                o = Organization(body['BodyName'],
                                 classification='committee',
                                 parent_id={'name' : 'Chicago City Council'})

                o.add_source(self.BASE_URL + '/bodies/{BodyId}'.format(**body), note='api')
                o.add_source(self.WEB_URL + '/DepartmentDetail.aspx?ID={BodyId}&GUID={BodyGuid}'.format(**body), note='web')

                yield o        

        for p in members.values():
            yield p

