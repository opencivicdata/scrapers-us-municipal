from pupa.scrape import Jurisdiction
from legistar.ext.pupa import LegistarPeopleScraper


class Jonesboro(Jurisdiction):
    division_id = 'ocd-division/country:us/state:ar/place:jonesboro'
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ar/place:jonesboro/government'

    name = 'Jonesboro City Council'
    url = 'http://jonesboro.legistar.com/'

    scrapers = {
        "people": LegistarPeopleScraper,
    }
