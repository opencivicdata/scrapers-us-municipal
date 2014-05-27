from pupa.scrape import Jurisdiction

# from .events import NewYorkCityEventsScraper
from legistar.ext.pupa import LegistarPeopleScraper


class NewYorkCity(Jurisdiction):
    division_id = 'ocd-division/country:us/state:ny/place:new_york'
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ny/place:new_york/government'
    name = 'New York City Council'
    url = 'http://council.nyc.gov/'
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]

    scrapers = {
        "people": LegistarPeopleScraper,
        # "events": NewYorkCityEventsScraper
    }
