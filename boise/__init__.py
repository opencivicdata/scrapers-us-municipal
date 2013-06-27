from pupa.scrape import Jurisdiction

from .events import BoiseEventScraper
from .people import PersonScraper
from .bills import BillScraper


class Boise(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:id/place:boise_city/council'

    def get_metadata(self):
        return {'name': 'Boise City Council',
                'legislature_name': 'Boise City Council',
                'legislature_url': 'http://mayor.cityofboise.org/city-council/',
                'terms': [{'name': '2010-2014', 'sessions': ['2013'],
                           'start_year': 2010, 'end_year': 2014
                          }],
                'provides': ['people', 'bills', 'events'],
                'parties': [{'name': 'Democratic' },
                            {'name': 'Republican' },
                           ],
                'session_details': {'2013': {'_scraped_name': '2013'}},
                'feature_flags': [],
               }

    def get_scraper(self, term, session, scraper_type):
        if scraper_type == 'people':
            return PersonScraper
        if scraper_type == 'bills':
            return BillScraper
        if scraper_type == 'events':
            return BoiseEventScraper

    def scrape_session_list(self):
        return ['2013']

