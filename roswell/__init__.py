from pupa.scrape import Jurisdiction
from .events import RoswellEventsScraper


class Roswell(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:nm/place:roswell/council'

    name = 'Roswell City Council'
    url = 'http://www.roswell-nm.gov/staticpages/index.php/cc1-citycouncil'
    provides = ['events']

    def get_scraper(self, session, scraper_type):
        bits = {
            "events": RoswellEventsScraper
        }
        if scraper_type in bits:
            return bits[scraper_type]
