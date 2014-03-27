from pupa.scrape import Jurisdiction
from .events import PhillyEventsScraper


class Philadelphia(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:pa/place:philadelphia/council'

    name = 'Philadelphia City Council'
    url = 'http://philadelphiacitycouncil.net/'
    provides = ['events']
    sessions = [ {'name': '2013', '_scraped_name': '2013'} ]

    def get_scraper(self, session, scraper_type):
        bits = {
            "events": PhillyEventsScraper
        }
        if scraper_type in bits:
            return bits[scraper_type]

    def scrape_session_list(self):
        return ['2013']
