import datetime

from legistar.people import LegistarAPIPersonScraper

from pupa.scrape import Scraper
from pupa.scrape import Person, Organization


class LametroPersonScraper(LegistarAPIPersonScraper):
    BASE_URL = 'http://webapi.legistar.com/v1/metro'
    TIMEZONE = "America/Los_Angeles"

    

    def scrape(self):
        body_types = self.body_types()
        
        board_of_directors, = [body for body in self.bodies()
                               if body['BodyName'] == 'Board of Directors']

        members = {}
        for office in self.body_offices(board_of_directors):
            members.setdefault(office['OfficeRecordFullName'], []).append(office)

        for member, offices in members.items():
            p = Person(member)
            for term in office:
                p.add_term(office['OfficeRecordTitle'],
                           'legislature',
                           start_date = self.toDate(office['OfficeRecordStartDate']),
                           end_date = self.toDate(office['OfficeRecordEndDate']))

            legistar_api = self.BASE_URL + '/OfficeRecords/'

            p.add_source(legistar_api, note='api')
            print(p)
                
            yield p

        adjunct_members = {}

        for body in self.bodies():
            if body['BodyTypeId'] == body_types['Committee']:
                o = Organization(body['BodyName'],
                                 classification='committee',
                                 parent_id={'name' : 'Board of Directors'})

                o.add_source(self.BASE_URL + '/Bodies/')

                for office in self.body_offices(body):
                    role = office['OfficeRecordTitle']
                    if role not in ("Chair", "Vice Chair"):
                        role = 'Member'

                    person = office['OfficeRecordFullName']
                    if person not in members:
                        if person not in adjunct_members:
                            p = Person(person)
                            p.add_source('foo')

                        else:
                            p = adjunct_members[person]

                        p.add_membership(body['BodyName'],
                                         role=role,
                                         start_date = self.toDate(office['OfficeRecordStartDate']),
                                         end_date = self.toDate(office['OfficeRecordEndDate']))
                        adjunct_members[person] = p
                    else:
                        o.add_member(office['OfficeRecordFullName'],
                                     role,
                                     start_date = self.toDate(office['OfficeRecordStartDate']),
                                     end_date = self.toDate(office['OfficeRecordEndDate']))
                        

                yield o

        for p in adjunct_members.values():
            yield p
