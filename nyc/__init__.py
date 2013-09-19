# Copyright (c) Sunlight Labs, 2013, under the terms of the BSD-3 clause
# license.
#
#  Contributors:
#
#    - Paul Tagliamonte <paultag@sunlightfoundation.com>


from pupa.scrape import Jurisdiction

from .events import NewYorkCityEventsScraper
from .people import NewYorkCityPersonScraper


class NewYorkCity(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ny/place:new_york/council'

    def get_metadata(self):
        return {'name': 'New York City Council',
                'url': 'http://council.nyc.gov/',
                'terms': [{'name': '2013-2014', 'sessions': ['2013'],
                           'start_year': 2013, 'end_year': 2014
                          }],
                'provides': ['people', 'events'],
                'parties': [{'name': 'Democrat' },
                            {'name': 'Republican'},
                            {'name': 'other'}],
                'session_details': {'2013': {'_scraped_name': '2013'}},
                'feature_flags': [],}

    def get_scraper(self, term, session, scraper_type):
        scrapers = {
            "people": NewYorkCityPersonScraper,
            "events": NewYorkCityEventsScraper
        }
        if scraper_type in scrapers:
            return scrapers[scraper_type]

    def scrape_session_list(self):
        return ['2013']
