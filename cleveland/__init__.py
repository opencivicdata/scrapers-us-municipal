from pupa.scrape import Jurisdiction

from .people import ClevelandPersonScraper
from .events import ClevelandEventScraper


class Cleveland(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:oh/place:cleveland/council'

    name = 'Cleveland City Council'
    url = 'http://www.clevelandcitycouncil.org/'

    scrapers = {
        "people": ClevelandPersonScraper,
        "events": ClevelandEventScraper
    }
