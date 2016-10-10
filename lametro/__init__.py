# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization
from .bills import LametroBillScraper
from .people import LametroPersonScraper
from .events import LametroEventScraper


class Lametro(Jurisdiction):
    division_id = "ocd-division/country:us/state:ca/county:los_angeles"
    classification = "transit_authority"
    name = "Los Angeles County"
    url = "https://www.metro.net/"
    scrapers = {
        "bills": LametroBillScraper,
        #"people": LametroPersonScraper,
        #"events": LametroEventScraper,
    }

    def get_organizations(self):
        #REQUIRED: define an organization using this format
        #where org_name is something like Seattle City Council
        #and classification is described here:
        org = Organization(name="Los Angeles County Metropolitan Transportation Authority", classification="legislature")

        # OPTIONAL: add posts to your organizaion using thi format,
        # where label is a human-readable description of the post (eg "Ward 8 councilmember")
        # and role is the positoin type (eg conucilmember, alderman, mayor...)
        # skip entirely if you're not writing a people scraper.
        #org.add_post(label="position_description", role="position_type")

        #REQUIIRED: yield the organization
        yield org
