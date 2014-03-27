from pupa.scrape import Jurisdiction

from .events import BoiseEventScraper
from .people import PersonScraper
from .bills import BillScraper


class Boise(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:id/place:boise_city/council'

    name = 'Boise City Council'
    url = 'http://mayor.cityofboise.org/city-council/'
    provides = ['people', 'bills', 'events']
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]
    sessions = [ {'name': '2013', '_scraped_name': '2013'} ]

    def get_scraper(self, session, scraper_type):
        if scraper_type == 'people':
            return PersonScraper
        if scraper_type == 'bills':
            return BillScraper
        if scraper_type == 'events':
            return BoiseEventScraper

    def scrape_session_list(self):
        return ['2013']

