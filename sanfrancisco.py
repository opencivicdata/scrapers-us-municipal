from pupa.scrape import Jurisdiction, Organization
from legistar.people import LegistarPersonScraper

class SFPersonScraper(LegistarPersonScraper):
    EXTRA_FIELDS = ('notes',)

#TODO: add district?

class SanFrancisco(Jurisdiction):
    name = 'San Francisco'
    classification = 'government'
    division_id = 'ocd-division/country:us/state:ca/place:san_francisco'
    timezone = 'America/Los_Angeles'
    url = 'http://sfgov.org'

    LEGISTAR_ROOT_URL = 'https://sfgov.legistar.com'
    scrapers = {'people': SFPersonScraper}

    def get_organizations(self):
        council = Organization('San Francisco Board of Supervisors', classification='legislature')
        for x in range(1,12):
            council.add_post(str(x), role='Supervisor')
        yield council


    #TOPLEVEL_ORG_MEMBERSHIP_TITLE = 'Supervisor'
    #TOPLEVEL_ORG_MEMBERSHIP_NAME = 'Board of Supervisors'
    #EVT_SEARCH_TABLE_TEXT_AUDIO = 'Audio'  # sfgov has this
    #EVT_SEARCH_TIME_PERIOD = 'This Year'
    #BILL_SEARCH_TABLE_TEXT_INTRO_DATE = 'Introduced'

    #def get_district(self, data):
    #    return self.DEFAULT_AT_LARGE_STRING
