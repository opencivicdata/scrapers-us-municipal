# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization, Person

from .events import PittsburghEventsScraper
from .people import PittsburghPersonScraper
from .bills import PittsburghBillScraper

import datetime


class Pittsburgh(Jurisdiction):
    division_id = "ocd-division/country:us/state:pa/place:pittsburgh"
    classification = "government"
    name = "Pittsburgh City Government"
    timezone = "America/New_York"
    url = "https://pittsburgh.legistar.com"

    scrapers = {
        "events": PittsburghEventsScraper,
        "people": PittsburghPersonScraper,
        "bills": PittsburghBillScraper,
    }

    legislative_sessions = []

    for year in range(2001, 2030):
        legislative_sessions.append({"identifier": str(year),
                                     "name": str(year) + " Session",
                                     "start_date": str(year) + "-01-01",
                                     "end_date": str(year) + "-12-31"})

    def get_organizations(self):
        org = Organization(name="Pittsburgh City Council", classification="legislature")
        for x in range(1, 10):
            org.add_post(
                "District {}".format(x),
                "Councilmember",
                division_id="ocd-division/country:us/state:pa/place:pittsburgh/council_district:{}".format(x))
        yield org

        standing_committee = Organization(name="Standing Committee", classification="committee")
        standing_committee.add_source("http://pittsburghpa.gov/council/standing-committees", note="web")
        yield standing_committee

        mayor = Organization(name="Mayor", classification="executive")
        mayor.add_post("Mayor", "Mayor", division_id="ocd-division/country:us/state:pa/place:pittsburgh")
        mayor.add_source("http://pittsburghpa.gov/mayor/index.html", note="web")
        yield mayor

        # TODO: figure out disambiguation for councilman/mayor positions (using birth_date?)

        # peduto = Person(name="William Peduto", birth_date=datetime.date(1964, 10, 30))
        # peduto.add_term("Mayor",
        #                 "executive",
        #                 start_date=datetime.date(2014, 1 ,6),
        #                 appointment=True)
        # peduto.add_source("http://pittsburghpa.gov/mayor/mayor-profile")
        # yield peduto

        # ravenstahl = Person(name="Luke Ravenstahl", birth_date=datetime.date(1980, 2, 6))
        # ravenstahl.add_term("Mayor",
        #                 "executive",
        #                 start_date=datetime.date(2006, 9, 1),
        #                 end_date=datetime.date(2014, 1 ,6),
        #                 appointment=True)
        # ravenstahl.add_source("https://www.post-gazette.com/local/city/2006/09/01/Ravenstahl-sworn-in-as-Pittsburgh-mayor/stories/200609010229")
        # yield ravenstahl

        city_clerk = Organization(name="City Clerk", classification="department")
        city_clerk.add_post("City Clerk", "City Clerk", division_id="ocd-division/country:us/state:pa/place:pittsburgh")
        city_clerk.add_source("http://pittsburghpa.gov/clerk/", note="web")
        yield city_clerk

        pree = Person(name="Brenda Pree")
        pree.add_term("City Clerk",
                      "department",
                      start_date=datetime.date(2017, 8, 29),
                      appointment=True)
        pree.add_source("http://pittsburghpa.gov/clerk/clerk-bio")
        yield pree

        doheny = Person(name="Mary Beth Doheny")
        doheny.add_term("City Clerk",
                        "department",
                        start_date=datetime.date(2014, 3, 18),
                        end_date=datetime.date(2017, 8, 28),
                        appointment=True)
        doheny.add_source("http://pittsburghpa.gov")
        yield doheny

        # "All Members", frustratingly, has a Person entry in Pittsburgh
        # Legistar, so the import trips without this. Going strong since 1816!

        all_members = Person(name="All Members")
        all_members.add_term("City Council",
                              "legislature",
                              start_date=datetime.date(1816, 3, 18))
        all_members.add_source("http://pittsburghpa.gov/council/index.html")
        yield all_members
