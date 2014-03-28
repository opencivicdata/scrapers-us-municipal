from pupa.scrape import Jurisdiction

from .events import NewYorkCityEventsScraper
from .people import NewYorkCityPersonScraper


class NewYorkCity(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ny/place:new_york/council'

    name = 'New York City Council'
    url = 'http://council.nyc.gov/'
    provides = ['people', 'events']
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]

    def get_scraper(self, session, scraper_type):
        scrapers = {
            "people": NewYorkCityPersonScraper,
            "events": NewYorkCityEventsScraper
        }
        if scraper_type in scrapers:
            return scrapers[scraper_type]
