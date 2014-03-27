from pupa.scrape import Jurisdiction

from .people import ChicagoPersonScraper
from .events import ChicagoEventsScraper
from .bills import ChicagoBillScraper


class Chicago(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:il/place:chicago/council'

    name = 'Chicago City Council'
    url =  'https://chicago.legistar.com/'
    provides = ['people', 'events', 'bills']
    parties = [
                {'name': 'Democrats' }
               ]
    sessions = [
        {'name': '2011', '_scraped_name': '2011'}
    ]

    def get_scraper(self, session, scraper_type):
        bits = {
            "people": ChicagoPersonScraper,
            "events": ChicagoEventsScraper,
            "bills": ChicagoBillScraper,
        }
        if scraper_type in bits:
            return bits[scraper_type]

    def scrape_session_list(self):
        return ['2011']

