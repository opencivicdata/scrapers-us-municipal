from pupa.scrape import Jurisdiction
from legistar.ext.pupa import LegistarPeopleScraper


class Madison(Jurisdiction):
    division_id = 'ocd-division/country:us/state:wi/place:madison'
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:wi/place:madison/government'

    name = 'Madison City Council'
    url = 'http://madison.legistar.com/'

    scrapers = {
        "people": LegistarPeopleScraper,
    }
