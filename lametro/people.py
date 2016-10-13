import datetime

from legistar.people import LegistarAPIPersonScraper

from pupa.scrape import Scraper
from pupa.scrape import Person, Organization


VOTING_POSTS = {'Jacquelyn Dupont-Walker' : 'Appointee of Mayor of Los Angeles',
                'Eric Garcetti' : 'Mayor of the City of Los Angeles',
                'Mike Bonin' : 'Appointee of Mayor of Los Angeles',
                'Paul Krekorian' : 'Appointee of Mayor of Los Angeles',
                'Hilda L. Solis' : 'Los Angeles County Board Supervisor, District 1', 
                'Mark Ridley-Thomas' : 'Los Angeles County Board Supervisor, District 2',
                'Sheila Kuehl' : 'Los Angeles County Board Supervisor, District 3',
                'Don Knabe' : 'Los Angeles County Board Supervisor, District 4',
                'Michael Antonovich' : 'Los Angeles County Board Supervisor, District 5',
                'John Fasana' : 'Appointee of Los Angeles County City Selection Committee, San Gabriel Valley sector',
                'James Butts' : 'Appointee of Los Angeles County City Selection Committee, Southwest Corridor sector',
                'Diane DuBois' : 'Appointee of Los Angeles County City Selection Committee, Southeast Long Beach sector',
                'Ara Najarian' : 'Appointee of Los Angeles County City Selection Committee, North County/San Fernando Valley sector'}

NONVOTING_POSTS = {'Carrie Bowen' : 'Appointee of Governor of California'}




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
            for term in offices:
                role = term['OfficeRecordTitle']

                if role != 'non-voting member':
                    role = 'Board Member'
                    post = VOTING_POSTS.get(member)
                else:
                    role = 'Nonvoting Board Member'
                    post = NONVOTING_POSTS.get(member)

                p.add_term(role,
                           'legislature',
                           district = post,
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
