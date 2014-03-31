from pupa.scrape import Jurisdiction

from .people import PersonScraper
from .bills import BillScraper


class Rialto(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:az/place:rialto/council'

    name = 'Rialto City Council'
    url = 'http://http://www.ci.rialto.ca.us/'
    provides = ['bills']
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]

    def get_scraper(self, scraper_type):
        if scraper_type == 'people':
            return PersonScraper
        if scraper_type == 'bills':
            return BillScraper
