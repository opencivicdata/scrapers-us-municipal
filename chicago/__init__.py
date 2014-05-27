from pupa.scrape import Jurisdiction

from .people import ChicagoPersonScraper
from .events import ChicagoEventsScraper
from .bills import ChicagoBillScraper


class Chicago(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:il/place:chicago/council'
    division_id = 'ocd-jurisdiction/country:us/state:il/place:chicago'
    name = 'Chicago City Council'
    url =  'https://chicago.legistar.com/'
    parties = [ {'name': 'Democrats' } ]

    scrapers = {
        "people": ChicagoPersonScraper,
        "events": ChicagoEventsScraper,
        "bills": ChicagoBillScraper,
    }
