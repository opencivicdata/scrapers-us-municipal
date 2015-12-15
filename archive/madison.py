from pupa.scrape import Jurisdiction, Organization
from legistar.people import LegistarPersonScraper


class MadisonPersonScraper(LegistarPersonScraper):

    EXTRA_FIELDS = ('notes',)
    DATE_FORMATS = ('%m/%d/%Y', '%m/%d/%Y*',)

    def skip_item(self, item):
        #return item['name'] in ('VACANCIES', 'Al Matano')
        # TODO: this skips all non-city councilors, check to make sure it doesn't skip other
        # interesting people?
        return 'district' not in item['url']


class Madison(Jurisdiction):
    division_id = 'ocd-division/country:us/state:wi/place:madison'
    classification = 'government'
    timezone = 'America/Chicago'
    name = 'Madison'
    url = 'http://www.cityofmadison.com/'

    scrapers = {'people': MadisonPersonScraper}
    # HTTPS is vital here, without it pagination doesn't work!
    LEGISTAR_ROOT_URL = 'https://madison.legistar.com/'

    def get_organizations(self):
        council = Organization('City of Madison Common Council', classification='legislature')
        for x in range(1,21):
            council.add_post(str(x), role='Alder')
        yield council

        #ORG_CLASSIFICATIONS = {
        #    'ALLIED AREA TASK FORCE': 'commission',
        #    'TRANSPORT 2020 IMPLEMENTATION TASK FORCE': 'commission',
        #    'COMMON COUNCIL': 'legislature',
        #    'COMMON COUNCIL - DISCUSSION': 'commission',
        #    'COMMUNITY ACTION COALITION FOR SOUTH CENTRAL WISCONSIN INC': 'commission',
        #    'COMMUNITY DEVELOPMENT AUTHORITY': 'commission',
        #    'MADISON COMMUNITY FOUNDATION': 'commission',
        #    'MADISON FOOD POLICY COUNCIL': 'commission',
        #    'MADISON HOUSING AUTHORITY': 'commission',
        #    'PARKING COUNCIL FOR PEOPLE WITH DISABILITIES': 'commission',
        #}

        #def person_district(self, data):
        #    '''This corresponds to the label field on organizations posts.
        #    '''
        #    # First try to get it from bio.
        #    dist = re.findall(r'District\s+\d+', data['notes'])
        #    if dist:
        #        return dist.pop()

        #    # Then try website.
        #    dist = re.findall(r'/district(\d+)/', data['website'])
        #    if dist:
        #        return dist.pop()

        #    # Then email.
        #    dist = re.findall(r'district(\d+)', data['email'])
        #    if dist:
        #        return dist.pop()
