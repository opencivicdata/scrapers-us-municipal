from pupa.scrape import Jurisdiction

from .people import ClevelandPersonScraper
from .events import ClevelandEventScraper


class Cleveland(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:oh/place:cleveland/council'

    name = 'Cleveland City Council'
    url = 'http://www.clevelandcitycouncil.org/'
    provides = ['people', 'events']

    def get_scraper(self, scraper_type):
        scrapers = {
            "people": ClevelandPersonScraper,
            "events": ClevelandEventScraper
        }

        if scraper_type in scrapers:
            return scrapers[scraper_type]
