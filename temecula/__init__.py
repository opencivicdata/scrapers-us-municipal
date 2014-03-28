from pupa.scrape import Jurisdiction

from .people import PersonScraper
from .events import TemeculaEventScraper


class Temecula(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ca/place:temecula/council'

    name = 'Temecula City Council'
    url = 'http://www.cityoftemecula.org/Temecula/Government/CouncilCommissions/CityCouncil/'
    provides = ['people']
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]

    def get_scraper(self, session, scraper_type):
        if scraper_type == 'people':
            return PersonScraper

        if scraper_type == 'events':
            return TemeculaEventScraper
