# Copyright (c) Sunlight Labs, 2013, under the terms of the BSD-3 clause
# license.
#
#  Contributors:
#
#    - Paul Tagliamonte <paultag@sunlightfoundation.com>


from pupa.scrape import Jurisdiction
from .events import RoswellEventsScraper


class Roswell(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:nm/place:roswell/council'

    def get_metadata(self):
        return {'name': 'Roswell',
                'legislature_name': 'Roswell City Council',
                'legislature_url': 'http://www.roswell-nm.gov/staticpages/'
                                       'index.php/cc1-citycouncil',
                'terms': [{'name': '2013-2014', 'sessions': ['2013'],
                           'start_year': 2013, 'end_year': 2014
                          }],
                'provides': ['events'],
                'parties': [],  # No parties on the city council
                'session_details': {'2013': {'_scraped_name': '2013'}},
                'feature_flags': [],}

    def get_scraper(self, term, session, scraper_type):
        bits = {
            "events": RoswellEventsScraper
        }
        if scraper_type in bits:
            return bits[scraper_type]

    def scrape_session_list(self):
        return ['2013']
