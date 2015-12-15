# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization
from .events import CookcountyEventScraper
from .bills import CookcountyBillScraper
from .people import CookcountyPersonScraper


class Cookcounty(Jurisdiction):
    division_id = "ocd-division/country:us/state:il/county:cook"
    classification = "legislature"
    name = "Cook County"
    url = "http://www.cookcountyil.gov/board-of-commissioners/"
    scrapers = {
        #"events": CookcountyEventScraper,
        #"bills": CookcountyBillScraper,
        "people": CookcountyPersonScraper,
    }

    def get_organizations(self):
        org = Organization(name="Cook County Board of Commissioners", classification="legislature")

        for x in range(1, 18):
            org.add_post(
                "District {}".format(x),
                "Commissioner",
                division_id='ocd-division/country:us/state:il/county:cook/council_district:{}'.format(x))

        org.add_post(
            "Board President",
            "Board President",
            division_id='ocd-division/country:us/state:il/county:cook')

        yield org
