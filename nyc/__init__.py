# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization
from .bills import NycBillScraper
from .events import NycEventScraper
from .people import NycPersonScraper


class Nyc(Jurisdiction):
    division_id = "ocd-division/country:us/state:ny/place:new_york"
    classification = "government"
    name = "City of New York"
    url = "council.nyc.gov"
    scrapers = {
        "bills": NycBillScraper,
        "events": NycEventScraper,
        "people": NycPersonScraper,
    }

    def get_organizations(self):
        #REQUIRED: define an organization using this format
        #where org_name is something like Seattle City Council
        #and classification is described here:
        org = Organization(name="org_name", classification="legislature")

        #OPTIONAL: add posts to your organizaion using thi format,
        #where label is a human-readable description of the post (eg "Ward 8 conucilmember")
        #and role is the positoin type (eg conucilmember, alderman, mayor...)
        #skip entirely if you're not writing a people scraper.
        org.add_post(label="position_description", role="position_type")

        #REQUIIRED: yield the organization
        yield org
