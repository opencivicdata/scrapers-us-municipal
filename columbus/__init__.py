from pupa.scrape import Jurisdiction

from .people import ColumbusPersonScraper
from .events import ColumbusEventScraper


class Columbus(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:oh/place:columbus/council'

    name = 'Columbus City Council'
    url = 'http://council.columbus.gov/'
    provides = ['people', 'events',]

    def get_scraper(self, session, scraper_type):
        bits = {
            "people": ColumbusPersonScraper,
            "events": ColumbusEventScraper,
        }
        if scraper_type in bits:
            return bits[scraper_type]
