# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization
from .people import StLouisPersonScraper


class StLouis(Jurisdiction):
    division_id = "ocd-division/country:us/state:mo/place:st_louis"
    jurisdiction_id = "ocd-jurisdiction/country:us/state:mo/place:st_louis"
    classification = "legislature"
    name = "St. Louis city Board of Aldermen"
    url = "https://www.stlouis-mo.gov/government/departments/aldermen/"
    scrapers = {
        "people": StLouisPersonScraper,
    }

    def get_organizations(self):

        WARD_COUNT = 28

        #REQUIRED: define an organization using this format
        #where org_name is something like Seattle City Council
        #and classification is described here:
        org = Organization(name="St Louis Board of Aldermen", 
                           classification="legislature")

        # OPTIONAL: add posts to your organizaion using thi format,
        # where label is a human-readable description of the post (eg "Ward 8 councilmember")
        # and role is the positoin type (eg conucilmember, alderman, mayor...)
        # skip entirely if you're not writing a people scraper.
        org.add_post(label="position_description", role="position_type")
        for ward_num in range(1, WARD_COUNT + 1):
            org.add_post(label="Ward {} Alderman".format(ward_num),
                         role="Alderman")

        #REQUIIRED: yield the organization
        yield org
