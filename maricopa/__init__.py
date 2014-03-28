from pupa.scrape import Jurisdiction

from .bills import BillScraper


class Example(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:az/place:maricopa'

    name = 'Maricopa City Council'
    url = 'http://www.maricopa-az.gov/web/'
    provides = ['bills']
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]

    def get_scraper(self, session, scraper_type):
        if scraper_type == 'bills':
            return BillScraper
