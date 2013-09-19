from pupa.scrape import Jurisdiction

from .bills import BillScraper


class Jurisdiction(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ca/place:longbeach'

    def get_metadata(self):
        return {
            'name': 'Long Beach City Council',
            'url': 'http://www.longbeach.gov/cityclerk/council_online.asp',
            'terms': [{
                'name': '2013-2014',
                'sessions': ['2013'],
                'start_year': 2013,
                'end_year': 2014
                }],
            'provides': ['people'],
            'parties': [
                {'name': 'Republican' },
                {'name': 'Democratic' },
               ],
            'session_details': {
                '2013': {'_scraped_name': '2013'}
                },
            'feature_flags': [],
               }

    def get_scraper(self, term, session, scraper_type):
        if scraper_type == 'bills':
            return BillScraper

    def scrape_session_list(self):
        return ['2013']

