# Copyright (c) Sunlight Labs, 2013, under the terms of the BSD-3 clause
# license.
#
#  Contributors:
#
#    - Paul Tagliamonte <paultag@sunlightfoundation.com>


from pupa.scrape import Jurisdiction

from .events import BostonEventsScraper
from .people import BostonPersonScraper
from .vote import BostonVoteScraper


class Boston(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ma/place:boston/council'

    def get_metadata(self):
        return {'name': 'Boston City Council',
                'url': 'http://www.cityofboston.gov/citycouncil/',
                'terms': [{'name': '2013-2014', 'sessions': ['2013'],
                           'start_year': 2013, 'end_year': 2014
                          }],
                'provides': ['people', 'events', 'votes'],
                'parties': [],  # No parties on the city council
                'session_details': {'2013': {'_scraped_name': '2013'}},
                'feature_flags': [],}

    def get_scraper(self, term, session, scraper_type):
        bits = {
            "people": BostonPersonScraper,
            "events": BostonEventsScraper,
            "votes": BostonVoteScraper,
        }
        if scraper_type in bits:
            return bits[scraper_type]

    def scrape_session_list(self):
        return ['2013']
