import datetime
import collections

from legistar.people import LegistarAPIPersonScraper

from pupa.scrape import Scraper
from pupa.scrape import Person, Organization



VOTING_POSTS = {'Jacquelyn Dupont-Walker' : 'Appointee of Mayor of the City of Los Angeles',
                'Eric Garcetti' : 'Mayor of the City of Los Angeles',
                'Mike Bonin' : 'Appointee of Mayor of the City of Los Angeles',
                'Paul Krekorian' : 'Appointee of Mayor of the City of Los Angeles',
                'Hilda L. Solis' : 'Los Angeles County Board Supervisor, District 1', 
                'Mark Ridley-Thomas' : 'Los Angeles County Board Supervisor, District 2',
                'Sheila Kuehl' : 'Los Angeles County Board Supervisor, District 3',
                'Janice Hahn' : 'Los Angeles County Board Supervisor, District 4',
                'Kathryn Barger' : 'Los Angeles County Board Supervisor, District 5',
                'John Fasana' : 'Appointee of Los Angeles County City Selection Committee, San Gabriel Valley sector',
                'James Butts' : 'Appointee of Los Angeles County City Selection Committee, Southwest Corridor sector',
                'Diane DuBois' : 'Appointee of Los Angeles County City Selection Committee, Southeast Long Beach sector',
                'Ara Najarian' : 'Appointee of Los Angeles County City Selection Committee, North County/San Fernando Valley sector',
                'Robert Garcia' : 'Appointee of Los Angeles County City Selection Committee, Southeast Long Beach sector',
                'Don Knabe' : 'Los Angeles County Board Supervisor, District 4',
                'Michael Antonovich' : 'Los Angeles County Board Supervisor, District 5'}

NONVOTING_POSTS = {'Carrie Bowen' : 'Appointee of Governor of California'}




class LametroPersonScraper(LegistarAPIPersonScraper):
    BASE_URL = 'http://webapi.legistar.com/v1/metro'
    WEB_URL = 'https://metro.legistar.com'
    TIMEZONE = "America/Los_Angeles"
    

    def scrape(self):
        body_types = self.body_types()

        board_of_directors, = [body for body in self.bodies()
                               if body['BodyName'] == 'Board of Directors - Regular Board Meeting']
        board_of_directors["BodyName"] = "Board of Directors"

        terms = collections.defaultdict(list)
        for office in self.body_offices(board_of_directors):
            terms[office['OfficeRecordFullName']].append(office)

        members = {}
        for member, offices in terms.items():
            p = Person(member)
            for term in offices:
                role = term['OfficeRecordTitle']

                if role not in {'Board Member', 'non-voting member'}:
                    p.add_term(role,
                               'legislature',
                               start_date = self.toDate(term['OfficeRecordStartDate']),
                               end_date = self.toDate(term['OfficeRecordEndDate']))
                if role != 'Chief Executive Officer':
                    if role == 'non-voting member':
                        member_type = 'Nonvoting Board Member'
                        post = NONVOTING_POSTS.get(member)
                    else:
                        member_type = 'Board Member'
                        post = VOTING_POSTS.get(member)

                    p.add_term(member_type,
                               'legislature',
                               district = post,
                               start_date = self.toDate(term['OfficeRecordStartDate']),
                               end_date = self.toDate(term['OfficeRecordEndDate']))


            source_urls = self._person_sources_from_office(term)
            person_api_url, person_web_url = source_urls
            p.add_source(person_api_url, note='api')
            p.add_source(person_web_url, note='web')

            members[member] = p

        for body in self.bodies():
            if body['BodyTypeId'] == body_types['Committee']:
                o = Organization(body['BodyName'],
                                 classification='committee',
                                 parent_id={'name' : 'Board of Directors'})

                o.add_source(self.BASE_URL + '/bodies/{BodyId}'.format(**body), note='api')
                o.add_source(self.WEB_URL + '/DepartmentDetail.aspx?ID={BodyId}&GUID={BodyGuid}'.format(**body), note='web')

                for office in self.body_offices(body):
                    role = office['OfficeRecordTitle']
                    if role not in ("Chair", "Vice Chair"):
                        role = 'Member'

                    person = office['OfficeRecordFullName']
                    if person in members:
                        p = members[person]
                    else:
                        p = Person(person)
                        
                        source_urls = self._person_sources_from_office(office)
                        person_api_url, person_web_url = source_urls
                        p.add_source(person_api_url, note='api')
                        p.add_source(person_web_url, note='web')

                        members[person] = p

                    p.add_membership(body['BodyName'],
                                     role=role,
                                     start_date = self.toDate(office['OfficeRecordStartDate']),
                        
                                     end_date = self.toDate(office['OfficeRecordEndDate']))
                        

                yield o

        for p in members.values():
            yield p

    def _person_sources_from_office(self, office):
        person_api_url = self.BASE_URL + '/persons/{OfficeRecordPersonId}'.format(**office)
        
        response = self.get(person_api_url)
        person_web_url = self.WEB_URL + '/PersonDetail.aspx?ID={PersonId}&GUID={PersonGuid}'.format(**response.json())

        return person_api_url, person_web_url
