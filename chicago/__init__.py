from pupa.scrape import Jurisdiction

from .people import PersonScraper



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
            'provides': ['people'],
            'parties': [
                {'name': 'Democrats' }
               ],
            'session_details': {
                '2011': {'_scraped_name': '2011'}
                },
            'feature_flags': [],
               }

    def get_scraper(self, term, session, scraper_type):
        if scraper_type == 'people':
            return PersonScraper

    def scrape_session_list(self):
        return ['2011']

