from pupa.scrape import Jurisdiction
from .events import PhillyEventsScraper


class Philadelphia(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:pa/place:philadelphia/council'

    name = 'Philadelphia City Council'
    url = 'http://philadelphiacitycouncil.net/'

    scrapers = {
        "events": PhillyEventsScraper
    }
