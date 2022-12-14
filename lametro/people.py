from datetime import date
import collections

from legistar.people import LegistarAPIPersonScraper, LegistarPersonScraper

from pupa.scrape import Scraper
from pupa.scrape import Person, Organization


VOTING_POSTS = {'Jacquelyn Dupont-Walker' : 'Appointee of Mayor of the City of Los Angeles',
                'Eric Garcetti' : 'Mayor of the City of Los Angeles',
                'Mike Bonin' : 'Appointee of Mayor of the City of Los Angeles',
                'Paul Krekorian' : 'Appointee of Mayor of the City of Los Angeles',
                'Hilda L. Solis' : 'Los Angeles County Board Supervisor, District 1',
                'Holly J. Mitchell' : 'Los Angeles County Board Supervisor, District 2',
                'Mark Ridley-Thomas' : 'Los Angeles County Board Supervisor, District 2',
                'Sheila Kuehl' : 'Los Angeles County Board Supervisor, District 3',
                'Janice Hahn' : 'Los Angeles County Board Supervisor, District 4',
                'Kathryn Barger' : 'Los Angeles County Board Supervisor, District 5',
                'John Fasana' : 'Appointee of Los Angeles County City Selection Committee, San Gabriel Valley sector',
                'James Butts' : 'Appointee of Los Angeles County City Selection Committee, Southwest Corridor sector',
                'Diane DuBois' : 'Appointee of Los Angeles County City Selection Committee, Southeast Long Beach sector',
                'Ara J. Najarian' : 'Appointee of Los Angeles County City Selection Committee, North County/San Fernando Valley sector',
                'Robert Garcia' : 'Appointee of Los Angeles County City Selection Committee, Southeast Long Beach sector',
                'Don Knabe' : 'Los Angeles County Board Supervisor, District 4',
                'Michael Antonovich' : 'Los Angeles County Board Supervisor, District 5',
                'Tim Sandoval': 'Appointee of Los Angeles County City Selection Committee, San Gabriel Valley sector',
                'Fernando Dutra' : 'Appointee of Los Angeles County City Selection Committee, Southeast Long Beach sector',
                'Lindsey Horvath' : 'Los Angeles County Board Supervisor, District 3',
                'Karen Bass' : 'Mayor of the City of Los Angeles'}

NONVOTING_POSTS = {'Carrie Bowen' : 'Appointee of Governor of California',
                   'Shirley Choate' : 'District 7 Director, California Department of Transportation (Caltrans), Appointee of the Governor of California',
                   'John Bulinski' : 'District 7 Director, California Department of Transportation (Caltrans), Appointee of the Governor of California',
                   'Tony Tavares' : 'District 7 Director, California Department of Transportation (Caltrans), Appointee of the Governor of California',
                   'Gloria Roberts' : 'District 7 Director (Interim), California Department of Transportation (Caltrans), Appointee of the Governor of California'}

ACTING_MEMBERS_WITH_END_DATE = {'Shirley Choate': date(2018, 10, 24)}

BOARD_OFFICE_ROLES = ("Chair",
                      "Vice Chair",
                      "1st Vice Chair",
                      "2nd Vice Chair",
                      "Chief Executive Officer")

PENDING_COMMITTEE_MEMBERS = ()


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

                    start_date = self.toDate(term['OfficeRecordStartDate'])
                    end_date = self.toDate(term['OfficeRecordEndDate'])
                    board_membership = p.add_term(member_type,
                               'legislature',
                               district = post,
                               start_date = start_date,
                               end_date = end_date)

                    acting_member_end_date = ACTING_MEMBERS_WITH_END_DATE.get(p.name)

                    if acting_member_end_date and acting_member_end_date <= end_date:
                        board_membership.extras = {'acting': 'true'}

            # Each term contains first and last names. This should be the same
            # across all of a person's terms, so go ahead and grab them from the
            # last term in the array.
            p.family_name = term['OfficeRecordLastName']
            p.given_name = term['OfficeRecordFirstName']

            # Defensively assert that the given and family names match the
            # expected value.
            if member == 'Hilda L. Solis':
                # Given/family name does not contain middle initial.
                assert p.given_name == 'Hilda' and p.family_name == 'Solis'
            elif member == 'Gloria Roberts (Interim)':
                assert p.given_name == 'Gloria' and p.family_name == 'Roberts'
            else:
                assert member == ' '.join([p.given_name, p.family_name])

            source_urls = self.person_sources_from_office(term)
            person_api_url, person_web_url = source_urls

            p.add_source(person_api_url, note='api')
            p.add_source(person_web_url, note='web')

            members[member] = p

        for body in self.bodies():
            if body['BodyTypeId'] in (body_types['Committee'], body_types['Independent Taxpayer Oversight Committee']):
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

                    if role not in BOARD_OFFICE_ROLES:
                        if role == 'non-voting member':
                            role = 'Nonvoting Member'
                        else:
                            role = 'Member'

                    person = office['OfficeRecordFullName']

                    # Temporarily skip committee memberships, e.g., for
                    # new board members. The content of this array is provided
                    # by Metro.
                    if person in PENDING_COMMITTEE_MEMBERS:
                        self.warning('Skipping {0} membership for {1}'.format(organization_name, person))
                        continue

                    if person in members:
                        p = members[person]
                    else:
                        p = Person(person)

                        source_urls = self.person_sources_from_office(office)
                        person_api_url, person_web_url = source_urls
                        p.add_source(person_api_url, note='api')
                        p.add_source(person_web_url, note='web')

                        members[person] = p

                    start_date = self.toDate(office['OfficeRecordStartDate'])
                    end_date = self.toDate(office['OfficeRecordEndDate'])
                    membership = p.add_membership(organization_name,
                                     role=role,
                                     start_date=start_date,
                                     end_date=end_date)

                    acting_member_end_date = ACTING_MEMBERS_WITH_END_DATE.get(p.name)
                    if acting_member_end_date and acting_member_end_date <= end_date:
                        membership.extras = {'acting': 'true'}

                yield o

        for p in members.values():
            yield p
