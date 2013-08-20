from pupa.scrape import Jurisdiction

from .people import PersonScraper


class Example(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ex/place:example'

    def get_metadata(self):
        return {
            'name': 'Example',
            'legislature_name': 'Example Legislature',
            'legislature_url': 'http://example.com',
            'terms': [{
                'name': '2013-2014',
                'sessions': ['2013'],
                'start_year': 2013,
                'end_year': 2014
                }],
            'provides': ['people'],
            'parties': [
                {'name': 'Independent' },
                {'name': 'Green' },
                {'name': 'Bull-Moose'}
               ],
            'session_details': {
                '2013': {'_scraped_name': '2013'}
                },
            'feature_flags': [],
               }

    def get_scraper(self, term, session, scraper_type):
        if scraper_type == 'people':
            return PersonScraper

    def scrape_session_list(self):
        return ['2013']

