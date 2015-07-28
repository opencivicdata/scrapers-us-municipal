# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization
from .people import NYCPersonScraper
from .events import NYCEventsScraper

class NYC(Jurisdiction):
    classification = 'government'
    division_id = 'ocd-division/country:us/state:ny/place:new_york'
    name = 'New York City'
    timezone = 'America/New_York'
    url = 'http://nyc.gov'

    parties = [
        {'name': 'Democratic'},
        {'name': 'Republican'}
    ]
    scrapers = {'people': NYCPersonScraper,
                'events': NYCEventsScraper}

    def get_organizations(self):
        council = Organization('New York City Council', classification='legislature')
        for x in range(1,52):
            council.add_post("District {}".format(x),
                             role='Council Member')
        yield council

    LEGISTAR_ROOT_URL = 'http://legistar.council.nyc.gov/'

