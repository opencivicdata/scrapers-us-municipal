from pupa.scrape import Jurisdiction

from .people import PersonScraper
from .bills import BillScraper


class Rialto(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:az/place:rialto/council'

    name = 'Rialto City Council'
    url = 'http://http://www.ci.rialto.ca.us/'
    provides = ['bills']
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]
    sessions = [ {'name': '2013', '_scraped_name': '2013'} ]

    def get_scraper(self, session, scraper_type):
        if scraper_type == 'people':
            return PersonScraper
        if scraper_type == 'bills':
            return BillScraper

    def scrape_session_list(self):
        return ['2013']

