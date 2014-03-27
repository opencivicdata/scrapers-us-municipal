from pupa.scrape import Jurisdiction

from .people import PersonScraper
from .bills import BillScraper


class Albequerque(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:nm/place:albequerque/council'

    name= 'Albequerque City Council'
    url = 'http://www.cabq.gov/council/'
    provides = ['people', 'bills'],
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]
    sessions = [ {'name': '2013', '_scraped_name': '2013'} ]
    feature_flags = []

    def get_scraper(self, session, scraper_type):
        if scraper_type == 'people':
            return PersonScraper
        if scraper_type == 'bills':
            return BillScraper

    def scrape_session_list(self):
        return ['2013']

