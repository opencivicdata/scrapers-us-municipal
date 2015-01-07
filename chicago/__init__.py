from pupa.scrape import Jurisdiction, Organization

from .people import ChicagoPersonScraper
from .events import ChicagoEventsScraper
from .bills import ChicagoBillScraper


class Chicago(Jurisdiction):
    division_id = 'ocd-division/country:us/state:il/place:chicago'
    classification='council'
    name = 'Chicago City Council'
    url =  'https://chicago.legistar.com/'
    parties = [ {'name': 'Democrats' } ]

    scrapers = {
        #"people": ChicagoPersonScraper,
        #"events": ChicagoEventsScraper,
        "bills": ChicagoBillScraper,
    }


    def get_organizations(self):
        org = Organization(name="Chicago City Council", classification="legislature")

        org.add_post("Clerk", "Clerk",
             division_id="ocd-division/country:us/state:il/place:chicago")

        org.add_post("Mayor", "Mayor",
             division_id="ocd-division/country:us/state:il/place:chicago")

        for x in range(1, 51):
            org.add_post(
                "Ward {}".format(x),
                "Alderman",
                division_id="ocd-division/country:us/state:il/place:chicago"
            )
        yield org
