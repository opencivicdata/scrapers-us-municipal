# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization
from .people import StLouisPersonScraper


class StLouis(Jurisdiction):
    division_id = "ocd-division/country:us/state:mo/place:st_louis"

    # FIXME
    # Do we need jurisdiction_id? pupa did not auto-generate this field 
    # like division_id, I made it myself.
    # And is this the correct id? or should it be 
    # .../place:st_louis/council ? or .../place:st_louis/government ?
    jurisdiction_id = "ocd-jurisdiction/country:us/state:mo/place:st_louis"
    
    classification = "legislature"
    name = "St. Louis city Board of Aldermen"
    url = "https://www.stlouis-mo.gov/government/departments/aldermen/"
    scrapers = {
        "people": StLouisPersonScraper,
    }

    WARD_COUNT = 28

    def get_organizations(self):
        # create an Organization for the BofA
        org = Organization(name="St Louis Board of Aldermen", 
                           classification="legislature")
        # add a post for each Ward
        for ward_num in range(1, self.WARD_COUNT + 1):
            org.add_post(label="Ward {} Alderman".format(ward_num),
                         role="Alderman")
        yield org
