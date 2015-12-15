from pupa.scrape import Jurisdiction

from .bills import BillScraper


class Jurisdiction(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ca/place:longbeach'
    name = 'Long Beach City Council'
    url = 'http://www.longbeach.gov/cityclerk/council_online.asp'
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]
    scrapers = {'bills': BillScraper}
