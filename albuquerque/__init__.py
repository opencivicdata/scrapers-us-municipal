from pupa.scrape import Jurisdiction

from .people import PersonScraper
from .bills import BillScraper


class Albequerque(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:nm/place:albequerque/council'
    name= 'Albequerque City Council'
    url = 'http://www.cabq.gov/council/'
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]
    scrapers = {'people': PersonScraper, 'bills': BillScraper}
