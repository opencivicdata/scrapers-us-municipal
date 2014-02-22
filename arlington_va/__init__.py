from pupa.scrape import Jurisdiction

from .people import PersonScraper
from .events import EventScraper


class Example(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:va/place:arlington/council'
    name = 'Arlington County Board'
    url = 'http://www.arlingtonva.us/Departments/CountyBoard/CountyBoardMain.aspx'
    terms = [{
        'name': '2014-2015',
        'sessions': ['2014'],
        'start_year': 2014,
        'end_year': 2015
    }]
    provides = ['people']
    parties = [
        {'name': 'Democratic' },
        {'name': 'Green' },
        {'name': 'Republican'}
    ]
    session_details = {
        '2014': {'_scraped_name': '2014'}
    }

    def get_scraper(self, term, session, scraper_type):
        if scraper_type == 'people':
            return PersonScraper
        elif scraper_type == 'events':
            return EventScraper

    def scrape_session_list(self):
        return ['2014']

