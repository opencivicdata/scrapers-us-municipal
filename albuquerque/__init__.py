from pupa.scrape import Jurisdiction

from .people import PersonScraper
from .bills import BillScraper


class Albequerque(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:nm/place:albequerque/council'

    name= 'Albequerque City Council'
    url = 'http://www.cabq.gov/council/'
    provides = ['people', 'bills'],
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]
    feature_flags = []

    def get_scraper(self, session, scraper_type):
        if scraper_type == 'people':
            return PersonScraper
        if scraper_type == 'bills':
            return BillScraper
