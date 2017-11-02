import collections
import datetime
import re

from legistar.people import LegistarAPIPersonScraper, LegistarPersonScraper
from pupa.scrape import Person, Organization

from .secrets import TOKEN

# 
# VOTING_POSTS = {'Jacquelyn Dupont-Walker' : 'Appointee of Mayor of the City of Los Angeles',
#                 'Eric Garcetti' : 'Mayor of the City of Los Angeles',
#                 'Mike Bonin' : 'Appointee of Mayor of the City of Los Angeles',
#                 'Paul Krekorian' : 'Appointee of Mayor of the City of Los Angeles',
#                 'Hilda L. Solis' : 'Los Angeles County Board Supervisor, District 1',
#                 'Mark Ridley-Thomas' : 'Los Angeles County Board Supervisor, District 2',
#                 'Sheila Kuehl' : 'Los Angeles County Board Supervisor, District 3',
#                 'Janice Hahn' : 'Los Angeles County Board Supervisor, District 4',
#                 'Kathryn Barger' : 'Los Angeles County Board Supervisor, District 5',
#                 'John Fasana' : 'Appointee of Los Angeles County City Selection Committee, San Gabriel Valley sector',
#                 'James Butts' : 'Appointee of Los Angeles County City Selection Committee, Southwest Corridor sector',
#                 'Diane DuBois' : 'Appointee of Los Angeles County City Selection Committee, Southeast Long Beach sector',
#                 'Ara Najarian' : 'Appointee of Los Angeles County City Selection Committee, North County/San Fernando Valley sector',
#                 'Robert Garcia' : 'Appointee of Los Angeles County City Selection Committee, Southeast Long Beach sector',
#                 'Don Knabe' : 'Los Angeles County Board Supervisor, District 4',
#                 'Michael Antonovich' : 'Los Angeles County Board Supervisor, District 5'}
# 
# NONVOTING_POSTS = {'Carrie Bowen' : 'Appointee of Governor of California'}



class NYCPersonScraper(LegistarAPIPersonScraper):
    BASE_URL = 'https://webapi.legistar.com/v1/nyc'
    WEB_URL = 'http://legistar.council.nyc.gov'
    TIMEZONE = 'US/Eastern'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.params = {'Token': TOKEN}

    def _public_advocate_name(self, office):
        '''
        The full name for public advocates is "The Public Advocate Mr./Ms. X".
        The last name is "Mr./Ms. X." This method combines the first name and
        the last name, less the courtesy title, into a usable full name.
        '''
        first_name = office['OfficeRecordFirstName']
        last_name = ' '.join(office['OfficeRecordLastName'].split(' ')[1:])
        return ' '.join([first_name, last_name])

    def scrape(self):
        web_scraper = LegistarPersonScraper(None, None)
        web_scraper.MEMBERLIST = 'http://legistar.council.nyc.gov/DepartmentDetail.aspx?ID=6897&GUID=CDC6E691-8A8C-4F25-97CB-86F31EDAB081&Mode=MainBody'

        web_info = {}
        for member, _ in web_scraper.councilMembers():
            web_info[member['Person Name']['label']] = member
            break

        city_council, = [body for body in self.bodies()
                         if body['BodyName'] == 'City Council']

        terms = collections.defaultdict(list)
        for office in self.body_offices(city_council):
            name = office['OfficeRecordFullName']

            if name.lower().startswith('the public advocate'):
                name = self._public_advocate_name(office)

            terms[name].append(office)

        members = {}
        for member, offices in terms.items():
            web = web_info.get(member)

            if not web:
                continue

            p = Person(member)

            for term in offices:
                p.add_term(office['OfficeRecordTitle'],
                           'legislature',
                           district=web.get('District', 'None'),
                           start_date=self.toDate(term['OfficeRecordStartDate']),
                           end_date=self.toDate(term['OfficeRecordEndDate']))

                party = web['Political Party']

                if party == 'Democrat':
                    party = 'Democratic'

                p.add_party(party)

                if web['Photo'] :
                    p.image = web['Photo']

                contact_types = {
                    "City Hall Office": ("address", "City Hall Office"),
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

                if web["E-mail"]:
                    p.add_contact_detail(type="email",
                                         value=web['E-mail']['url'],
                                         note='E-mail')

                if web['Web site']:
                    p.add_link(web['Web site']['url'], note='web site')

                p.extras = {'Notes' : web['Notes']}

                source_urls = self.person_sources_from_office(term)
                person_api_url, person_web_url = source_urls
                p.add_source(person_api_url, note='api')
                p.add_source(person_web_url, note='web')

                members[member] = p

        for body in self.bodies():
            # TODO: Figure out which bodies to scrape
            pass



PARENT_ORGS = {
    'Subcommittee on Landmarks, Public Siting and Maritime Uses' : 'Committee on Land Use',
    'Subcommittee on Libraries' : 'Committee on Cultural Affairs, Libraries and International Intergroup Relations',
    'Subcommittee on Non-Public Schools' : 'Committee on Education',
    'Subcommittee on Planning, Dispositions and Concessions' : 'Committee on Land Use',
    'Subcommittee on Senior Centers' : 'Committee on Aging',
    'Subcommittee on Zoning and Franchises' : 'Committee on Land Use'}
