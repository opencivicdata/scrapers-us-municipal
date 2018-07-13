import datetime
import collections

from legistar.people import LegistarAPIPersonScraper, LegistarPersonScraper

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

NONVOTING_POSTS = {'Carrie Bowen' : 'Appointee of Governor of California',
                   'Shirley Choate' : 'Acting Caltrans District 7 Director, Appointee of Governor of California'}

class LametroPersonScraper(LegistarAPIPersonScraper, Scraper):
    BASE_URL = 'http://webapi.legistar.com/v1/metro'
    WEB_URL = 'https://metro.legistar.com'
    TIMEZONE = "America/Los_Angeles"


    def scrape(self):
        '''
        Scrape the web to create a dict with all active organizations.
        Then, we can access the correct URL for the organization detail page.
        '''
        web_scraper = LegistarPersonScraper(requests_per_minute=self.requests_per_minute)
        web_scraper.MEMBERLIST = 'https://metro.legistar.com/People.aspx'
        web_info = {}

        for _, organizations in web_scraper.councilMembers():
            for organization, _, _ in organizations:
                organization_name = organization['Department Name']['label'].strip()
                organization_info = organization['Department Name']

                web_info[organization_name] = organization_info

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
                               end_date = self.toDate(term['OfficeRecordEndDate']),
                               appointment = True)
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


            source_urls = self.person_sources_from_office(term)
            person_api_url, person_web_url = source_urls
            p.add_source(person_api_url, note='api')
            p.add_source(person_web_url, note='web')

            members[member] = p

        for body in self.bodies():
            if body['BodyTypeId'] == body_types['Committee']:
                organization_name = body['BodyName'].strip()
                o = Organization(organization_name,
                                 classification='committee',
                                 parent_id={'name' : 'Board of Directors'})

                organization_info = web_info.get(organization_name, {})
                organization_url = organization_info.get('url', self.WEB_URL + 'https://metro.legistar.com/Departments.aspx')

                o.add_source(self.BASE_URL + '/bodies/{BodyId}'.format(**body), note='api')
                o.add_source(organization_url, note='web')

                for office in self.body_offices(body):
                    role = office['OfficeRecordTitle']

                    if role not in ("Chair", "Vice Chair"):
                        if role == 'non-voting member':
                            role = 'Nonvoting Member'
                        else:
                            role = 'Member'

                    person = office['OfficeRecordFullName']

                    if person in members:
                        p = members[person]
                    else:
                        p = Person(person)

                        source_urls = self.person_sources_from_office(office)
                        person_api_url, person_web_url = source_urls
                        p.add_source(person_api_url, note='api')
                        p.add_source(person_web_url, note='web')

                        members[person] = p

                    p.add_membership(organization_name,
                                     role=role,
                                     start_date = self.toDate(office['OfficeRecordStartDate']),
                                     end_date = self.toDate(office['OfficeRecordEndDate']))

                yield o

        for p in members.values():
            yield p
