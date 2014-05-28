from pupa.scrape import Jurisdiction

from .events import BoiseEventScraper
from .people import PersonScraper
from .bills import BillScraper


class Boise(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:id/place:boise_city/council'
    name = 'Boise City Council'
    url = 'http://mayor.cityofboise.org/city-council/'
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]

    scrapers = {'people': PersonScraper, 'bills': BillScraper, 'events': BoiseEventScraper}
