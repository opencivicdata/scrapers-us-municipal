# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization
# from .events import AnnarborEventScraper
from .people import AnnarborPersonScraper
from .bills import AnnarborBillScraper
# from .vote_events import AnnarborVoteEventScraper


class Annarbor(Jurisdiction):
    division_id = "ocd-division/country:us/state:mi/place:ann_arbor"
    classification = "legislature"
    name = "City of Ann Arbor"
    url = "https://www.a2gov.org/departments/city-council/Pages/Home.aspx"
    scrapers = {
        # "events": AnnarborEventScraper,
        "people": AnnarborPersonScraper,
        "bills": AnnarborBillScraper,
        # "vote_events": AnnarborVoteEventScraper,
    }

    legislative_sessions = [{"identifier": "{}".format(year),
                             "name": "{} Session".format(year),
                             "start_date": "{}-11-15".format(year),
                             "end_date": "{}-11-14".format(year + 1)}
                            for year in range(2007, 2018)]
    legislative_sessions.append({"identifier": "2018",
                                 "name": "2018 Session",
                                 "start_date": "2018-11-15",
                                 "end_date": "2020-11-14"})
    legislative_sessions.append({"identifier": "before"})

    def get_organizations(self):
        council = Organization(name="Ann Arbor City Council", classification="legislature")

        # OPTIONAL: add posts to your organizaion using this format,
        # where label is a human-readable description of the post (eg "Ward 8 councilmember")
        # and role is the position type (eg councilmember, alderman, mayor...)
        # skip entirely if you're not writing a people scraper.
        # vorg.add_post(label="position_description", role="position_type")

        yield council

        clerk = Organization('City Clerk', classification='executive')
        yield clerk

        mayor = Organization("Mayor's Office", classification='executive')
        yield mayor
