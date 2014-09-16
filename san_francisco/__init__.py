from pupa.scrape import Jurisdiction

# from .events import NewYorkCityEventsScraper
from legistar.ext.pupa import LegistarPeopleScraper


class NewYorkCity(Jurisdiction):
    division_id = 'ocd-division/country:us/state:ca/place:san_francisco'
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ca/place:san_francisco/government'
    name = 'City and County of San Francisco Board of Supervisors'
    url = 'https://sfgov.legistar.com/'
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]

    scrapers = {
        "people": LegistarPeopleScraper,
        # "events": NewYorkCityEventsScraper
    }
