# encoding=utf-8

from pupa.scrape import Jurisdiction, Organization, Person
from .events import MountainviewEventsScraper

# from .people import MountainviewPersonScraper
# from .bills import MountainviewBillScraper
# from .vote_events import MountainviewVoteEventScraper
import datetime

class Mountainview(Jurisdiction):
    division_id = "ocd-division/country:us/state:ca/place:mountainview"
    classification = "legislature"
    name = "City of Mountain View"
    url = "http://www.mountainview.gov"
    scrapers = {
        "events": MountainviewEventsScraper
        # "people": MountainviewPersonScraper,
        # "bills": MountainviewBillScraper,
        # "vote_events": MountainviewVoteEventScraper,
    }

    legislative_sessions = [
        {"identifier": "2019",
         "name": "2019 Regular Session",
         "start_date": "2019-05-20",
         "end_date": "2023-05-19"}
        # {"identifier": "2015",
        #  "name": "2015 Regular Session",
        #  "start_date": "2015-05-18",
        #  "end_date": "2019-05-19"},
        # {"identifier": "2011",
        #  "name": "2011 Regular Session",
        #  "start_date": "2011-05-18",
        #  "end_date": "2015-05-17"},
        # {"identifier": "2007",
        #  "name": "2007 Regular Session",
        #  "start_date": "2007-05-18",
        #  "end_date": "2011-05-17"}
    ]

    def get_organizations(self):
        #REQUIRED: define an organization using this format
        #where org_name is something like Seattle City Council
        #and classification is described here:
        org = Organization(name="Mountain View City Council", classification="legislature")

        # REQUIRED: yield the organization
        yield org

        # OPTIONAL: add posts to your organizaion using this format,
        # where label is a human-readable description of the post (eg "Ward 8 councilmember")
        # and role is the position type (eg councilmember, alderman, mayor...)
        # skip entirely if you're not writing a people scraper.
        city = Organization('City of Mountain View', classification='executive')
        city.add_post('Mayor', 'Mayor', division_id='ocd-division/country:us/state:ca/place:mountainview')
        city.add_post('City Manager', 'City Manager', division_id='ocd-division/country:us/state:ca/place:mountainview')
        city.add_post('City Clerk', 'City Clerk', division_id='ocd-division/country:us/state:ca/place:mountainview')

        yield city

        abekoga = Person(name="Abe-Koga, Margaret")
        abekoga.add_term('Mayor',
                       'executive',
                       start_date=datetime.date(1989, 4, 24),
                       end_date=datetime.date(2011, 5, 16),
                       appointment=True)
        abekoga.add_source('https://mountainview.legistar.com/People.aspx')
        yield abekoga