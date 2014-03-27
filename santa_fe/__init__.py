from pupa.scrape import Jurisdiction
from .events import SantaFeEventsScraper


class SantaFe(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:nm/place:santa_fe/council'

    name = 'Santa Fe City Council'
    url = 'http://www.santafenm.gov/index.aspx?nid=72'
    provides = ['events']
    sessions = [ {'name': '2013', '_scraped_name': '2013'} ]

    def get_scraper(self, session, scraper_type):
        bits = {
            "events": SantaFeEventsScraper
        }
        if scraper_type in bits:
            return bits[scraper_type]

    def scrape_session_list(self):
        return ['2013']
