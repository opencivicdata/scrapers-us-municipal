from pupa.scrape import Jurisdiction

from .people import PersonScraper
from .bills import BillScraper


class Albequerque(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:az/place:rialto/council'

    def get_metadata(self):
        return {
            'name': 'Rialto City Council',
            'url': 'http://http://www.ci.rialto.ca.us/',
            'terms': [{
                'name': '2013-2015',
                'start_year': 2013,
                'end_year': 2015,
                'sessions': ['2013'],
                }],
            'provides': ['bills'],
            'parties': [
                {'name': 'Democratic' },
                {'name': 'Republican' },
               ],
            'session_details': {
                '2013': {'_scraped_name': '2013'}
                },
            'feature_flags': [],
               }

    def get_scraper(self, term, session, scraper_type):
        if scraper_type == 'people':
            return PersonScraper
        if scraper_type == 'bills':
            return BillScraper

    def scrape_session_list(self):
        return ['2013']

