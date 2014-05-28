from pupa.scrape import Jurisdiction

from .bills import BillScraper


class Example(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:az/place:maricopa'
    name = 'Maricopa City Council'
    url = 'http://www.maricopa-az.gov/web/'
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]
    scrapers = {'bills': BillScraper}
