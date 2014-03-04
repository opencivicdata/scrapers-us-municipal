from pupa.scrape import Jurisdiction

from .people import ChicagoPersonScraper
from .events import ChicagoEventsScraper


class Chicago(Jurisdiction):
    jurisdiction_id = 'ocd-division/country:us/state:il/place:chicago/council'

    def get_metadata(self):
        return {
            'name': 'Chicago City Council',
            'url': 'https://chicago.legistar.com/',
            'terms': [{
                'name': '2011-2015',
                'sessions': ['2011'],
                'start_year': 2011,
                'end_year': 2015
                }],
            'provides': ['people', 'events'],
            'parties': [
                {'name': 'Democrats' }
               ],
            'session_details': {
                '2011': {'_scraped_name': '2011'}
                },
            'feature_flags': [],
               }

    def get_scraper(self, term, session, scraper_type):
        bits = {
            "people": ChicagoPersonScraper,
            "events": ChicagoEventsScraper,
        }
        if scraper_type in bits:
            return bits[scraper_type]

    def scrape_session_list(self):
        return ['2011']

