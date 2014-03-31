from pupa.scrape import Jurisdiction

from .people import ChicagoPersonScraper
from .events import ChicagoEventsScraper
from .bills import ChicagoBillScraper


class Chicago(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:il/place:chicago/council'

    name = 'Chicago City Council'
    url =  'https://chicago.legistar.com/'
    provides = ['people', 'events', 'bills']
    parties = [ {'name': 'Democrats' } ]

    scrapers = {
        "people": ChicagoPersonScraper,
        "events": ChicagoEventsScraper,
        "bills": ChicagoBillScraper,
    }
