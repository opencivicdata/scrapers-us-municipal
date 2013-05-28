# Copyright (c) Sunlight Labs, 2013, under the terms of the BSD-3 clause
# license.
#
#  Contributors:
#
#    - Paul Tagliamonte <paultag@sunlightfoundation.com>


from pupa.scrape import Jurisdiction
from .events import SantaFeEventsScraper


class SantaFe(Jurisdiction):
    jurisdiction_id = 'us-nm-saf'

    def get_metadata(self):
        return {'name': 'SantaFe',
                'legislature_name': 'Santa Fe City Council',
                'legislature_url': 'http://www.santafenm.gov/index.aspx?nid=72',
                'terms': [{'name': '2013-2014', 'sessions': ['2013'],
                           'start_year': 2013, 'end_year': 2014
                          }],
                'provides': ['events'],
                'parties': [],  # No parties on the city council
                'session_details': {'2013': {'_scraped_name': '2013'}},
                'feature_flags': [],}

    def get_scraper(self, term, session, scraper_type):
        bits = {
            "events": SantaFeEventsScraper
        }
        if scraper_type in bits:
            return bits[scraper_type]

    def scrape_session_list(self):
        return ['2013']
