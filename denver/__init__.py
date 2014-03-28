from pupa.scrape import Jurisdiction

# from .events import BoiseEventScraper
from .people import PersonScraper
from .bills import BillScraper


class Denver(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:co/place:denver/council'

    name = 'Denver City Council'
    url = 'https://www.denvergov.org/citycouncil'
    provides = ['bills']
    parties = [{'name': 'Democratic' }, {'name': 'Republican' }, ]

    def get_scraper(self, session, scraper_type):
        if scraper_type == 'people':
            return PersonScraper
        if scraper_type == 'bills':
            return BillScraper
        # if scraper_type == 'events':
        #     return BoiseEventScraper
