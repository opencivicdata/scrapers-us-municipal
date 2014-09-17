from pupa.scrape import Jurisdiction, Organization

from .people import ChicagoPersonScraper
from .events import ChicagoEventsScraper
from .bills import ChicagoBillScraper


class Chicago(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:il/place:chicago/council'
    division_id = 'ocd-jurisdiction/country:us/state:il/place:chicago'
    classification='council'
    name = 'Chicago City Council'
    url =  'https://chicago.legistar.com/'
    parties = [ {'name': 'Democrats' } ]

    scrapers = {
        "people": ChicagoPersonScraper,
        "events": ChicagoEventsScraper,
        "bills": ChicagoBillScraper,
    }


    def get_organizations(self):
        org = Organization(name="Chicago City Council", classification="legislature")
        for x in range(1, 51):
            org.add_post(
                "Ward {}".format(x),
                "Alderman",
                division_id="ocd-jurisdiction/country:us/state:il/place:chicago"
            )
        yield org
