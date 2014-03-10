from pupa.scrape import Jurisdiction

from .people import ChicagoPersonScraper
from .events import ChicagoEventsScraper
from .bills import ChicagoBillScraper


class Chicago(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:il/place:chicago/council'

    name = 'Chicago City Council'
    url =  'https://chicago.legistar.com/'
    terms = [{
        'name': '2011-2015',
        'sessions': ['2011'],
        'start_year': 2011,
        'end_year': 2015
    }]
    provides = ['people', 'events', 'bills']
    parties = [
                {'name': 'Democrats' }
               ]
    session_details = {
        '2011': {'_scraped_name': '2011'}
    }

    def get_scraper(self, term, session, scraper_type):
        bits = {
            "people": ChicagoPersonScraper,
            "events": ChicagoEventsScraper,
            "bills": ChicagoBillScraper,
        }
        if scraper_type in bits:
            return bits[scraper_type]

    def scrape_session_list(self):
        return ['2011']

