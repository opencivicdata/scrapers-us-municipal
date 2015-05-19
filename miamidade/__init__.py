# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization
from .events import MiamidadeEventScraper
from .bills import MiamidadeBillScraper
from .people import MiamidadePersonScraper


class Miamidade(Jurisdiction):
    division_id = "ocd-division/country:us/state:fl/county:miami-dade"
    classification = "legislature"
    name = "Miami-Dade County Government"
    url = "http://miamidade.gov/wps/portal/Main/government"
    parties = []

    scrapers = {
        "events": MiamidadeEventScraper,
        "bills": MiamidadeBillScraper,
        "people": MiamidadePersonScraper,
    }

    legislative_sessions = [{"identifier":"2014",
            "name":"2014 Regular Session",
            "start_date": "2014-11-20",
            "end_date": "2016-11-20"},
            ]


    def get_organizations(self):
        org = Organization(name="Miami-Dade County Commission",
            classification="legislature")
        
        #label=human readable
        #role=what we can pull with the scraper
        org.add_post(label="Clerk, Circuit and County Courts",
            role="Clerk, Circuit and County Courts",
            division_id=self.division_id)
        
        org.add_post(label="Mayor",role="Office of the Mayor",
            division_id=self.division_id)

        org.add_post("Property Appraiser","Property Appraiser",
            division_id=self.division_id)

        for x in range(1,14):
            org.add_post(label="District {dist} Commissioner".format(dist=x),
                role="District {dist}".format(dist=x),
                division_id=self.division_id)
        
        yield org
