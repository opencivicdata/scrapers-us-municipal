from pupa.scrape import Jurisdiction, Organization

from .people import ChicagoPersonScraper
from .events import ChicagoEventsScraper
from .bills import ChicagoBillScraper


class Chicago(Jurisdiction):
    division_id = 'ocd-division/country:us/state:il/place:chicago'
    classification='government'
    name = 'Chicago City Government'
    url =  'https://chicago.legistar.com/'
    parties = [ {'name': 'Democrats' } ]

    scrapers = {
        "people": ChicagoPersonScraper,
        "events": ChicagoEventsScraper,
        "bills": ChicagoBillScraper,
    }

    legislative_sessions = [{"identifier":"2015",
            "name":"2015 Regular Session",
            "start_date": "2015-05-18",
            "end_date": "2019-05-17"},
            {"identifier":"2011",
            "name":"2011 Regular Session",
            "start_date": "2011-05-18",
            "end_date": "2015-05-17"},
            {"identifier":"2007",
            "name":"2007 Regular Session",
            "start_date": "2007-05-18",
            "end_date": "2011-05-17"}
            ]

    def get_organizations(self):
        org = Organization(name="Chicago City Council", classification="legislature")

        org.add_post("Clerk", "Clerk")

        org.add_post("Mayor", "Mayor")

        for x in range(1, 51):
            org.add_post(
                "Ward {}".format(x),
                "Alderman")

        yield org
