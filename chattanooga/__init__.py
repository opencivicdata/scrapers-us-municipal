from pupa.scrape import Jurisdiction

from .people import ChattanoogaCouncilPersonScraper

class Chattanooga(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:tn/place:chattanooga/council'
    name = 'Chattanooga City Council'
    url = 'http://www.chattanooga.gov/city-council'
    terms = [{
        'name': '2013-2017',
        'sessions': ['2013', '2014'],
        'start_year': 2013,
        'end_year': 2017
    }]
    provides = ['people']
    parties = [
        {'name': 'Independent' },
        {'name': 'Republican' },
        {'name': 'Democrat' },
    ]
    session_details = {
        '2013': {'_scraped_name': '2013'},
        '2014': {'_scraped_name': '2014'},
    }

    def scrape_session_list(self):
        return ['2014']

    def get_scraper(self, term, session, scraper_type):
        if scraper_type == 'people':
            return ChattanoogaCouncilPersonScraper
