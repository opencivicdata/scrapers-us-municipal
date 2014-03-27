from pupa.scrape import Jurisdiction

from .events import CaryEventsScraper


class Cary(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:nc/place:cary/council'

    name = 'Cary Town Council'
    url = 'http://www.townofcary.org/town_council/cary_town_council.htm'
    provides = ['events']
    parties = []
    sessions = [ {'name': '2013', '_scraped_name': '2013'} ]
    feature_flags = []

    def get_scraper(self, session, scraper_type):
        bits = {
            "events": CaryEventsScraper
        }
        if scraper_type in bits:
            return bits[scraper_type]

    def scrape_session_list(self):
        return ['2013']
