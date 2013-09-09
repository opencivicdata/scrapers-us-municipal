from pupa.scrape import Jurisdiction

from .people import PersonScraper
from .events import TemeculaEventScraper


class Temecula(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ca/place:temecula/council'

    def get_metadata(self):
        return {'name': 'Temecula City Council',
                'url': 'http://www.cityoftemecula.org/Temecula/Government/CouncilCommissions/CityCouncil/',
                'terms': [{'name': '2010-2014', 'sessions': ['2013'],
                           'start_year': 2010, 'end_year': 2014
                          }],
                'provides': ['people'],
                'parties': [{'name': 'Democratic' },
                            {'name': 'Republican' },
                           ],
                'session_details': {'2013': {'_scraped_name': '2013'}},
                'feature_flags': [],
               }

    def get_scraper(self, term, session, scraper_type):
        if scraper_type == 'people':
            return PersonScraper

        if scraper_type == 'events':
            return TemeculaEventScraper

    def scrape_session_list(self):
        return ['2013']
