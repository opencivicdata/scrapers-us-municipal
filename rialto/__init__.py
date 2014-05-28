from pupa.scrape import Jurisdiction

from .people import PersonScraper
from .bills import BillScraper


class Rialto(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:az/place:rialto/council'
    name = 'Rialto City Council'
    url = 'http://http://www.ci.rialto.ca.us/'
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]
    scrapers = {'bills': BillScraper, 'people': PersonScraper}
