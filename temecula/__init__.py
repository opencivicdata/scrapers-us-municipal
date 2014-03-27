from pupa.scrape import Jurisdiction

from .people import PersonScraper
from .events import TemeculaEventScraper


class Temecula(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ca/place:temecula/council'

    name = 'Temecula City Council'
    url = 'http://www.cityoftemecula.org/Temecula/Government/CouncilCommissions/CityCouncil/'
    provides = ['people']
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]
    sessions = [ {'name': '2013', '_scraped_name': '2013'} ]

    def get_scraper(self, session, scraper_type):
        if scraper_type == 'people':
            return PersonScraper

        if scraper_type == 'events':
            return TemeculaEventScraper

    def scrape_session_list(self):
        return ['2013']
