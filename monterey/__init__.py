from pupa.scrape import Jurisdiction
from legistar.ext.pupa import LegistarPeopleScraper


class Jonesboro(Jurisdiction):
    division_id = 'ocd-division/country:us/state:ca/place:monterey'
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ca/place:monterey/government'

    name = 'City of Monterey Board of Supervisors'
    url = 'https://monterey.legistar.com/People.aspx'

    scrapers = {
        "people": LegistarPeopleScraper,
    }
