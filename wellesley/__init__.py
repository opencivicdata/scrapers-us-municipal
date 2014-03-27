from pupa.scrape import Jurisdiction

from .people import WellesleyPersonScraper


class Wellesley(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ma/place:wellesley/council'

    name = 'Wellesley Board of Selectmen'
    url = 'http://www.wellesleyma.gov/Pages/WellesleyMA_Selectmen/index'
    provides = ['people']
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]
    sessions = [ {'name': '2013', '_scraped_name': '2013'} ]

    def get_scraper(self, session, scraper_type):
        bits = {
            "people": WellesleyPersonScraper,
        }
        if scraper_type in bits:
            return bits[scraper_type]

    def scrape_session_list(self):
        return ['2013']
