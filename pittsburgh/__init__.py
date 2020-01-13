# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization, Person, Membership

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

        city = Organization('City of Pittsburgh', classification='executive')
        city.add_post('Mayor', 'Mayor', division_id='ocd-division/country:us/state:pa/place:pittsburgh')
        city.add_post('City Clerk', 'City Clerk', division_id='ocd-division/country:us/state:pa/place:pittsburgh')

        standing_committee = Organization(name="Standing Committee", classification="committee")
        standing_committee.add_source("http://pittsburghpa.gov/council/standing-committees", note="web")
        yield standing_committee

        # there are a number of committees that no longer exist but have old bills attached to them
        construction_committee = Organization(name="Committee on Engineering & Construction",
                                              classification="committee")
        construction_committee.add_source(self.url, note="web")
        yield construction_committee

        forestry_committee = Organization(name="Committee on Engineering, Fleet and Forestry",
                                          classification="committee")
        forestry_committee.add_source(self.url, note="web")
        yield forestry_committee

        facilities_committee = Organization(name="Committee on Facilities, Technology & the Arts",
                                            classification="committee")
        facilities_committee.add_source(self.url, note="web")
        yield facilities_committee

        budget_committee = Organization(name="Committee on Finance & Budget", classification="committee")
        budget_committee.add_source(self.url, note="web")
        yield budget_committee

        purchasing_committee = Organization(name="Committee on Finance, Law and Purchasing", classification="committee")
        purchasing_committee.add_source(self.url, note="web")
        yield purchasing_committee

        govt_services_committee = Organization(name="Committee on General and Government Services",
                                               classification="committee")
        govt_services_committee.add_source(self.url, note="web")
        yield govt_services_committee

        telecom_committee = Organization(name="Committee on General Services & Telecommunications",
                                         classification="committee")
        telecom_committee.add_source(self.url, note="web")
        yield telecom_committee

        arts_committee = Organization(name="Committee on General Services, Technology & the Arts",
                                      classification="committee")
        arts_committee.add_source(self.url, note="web")
        yield arts_committee

        housing_committee = Organization(name="Committee on Housing, Economic Development & Promotion",
                                         classification="committee")
        housing_committee.add_source(self.url, note="web")
        yield housing_committee

        parks_committee = Organization(name="Committee on Parks, Recreation & Youth Policy", classification="committee")
        parks_committee.add_source(self.url, note="web")
        yield parks_committee

        zoning_committee = Organization(name="Committee on Planning, Zoning & Land Use", classification="committee")
        zoning_committee.add_source(self.url, note="web")
        yield zoning_committee

        env_committee = Organization(name="Committee on Public Works & Environmental Services",
                                     classification="committee")
        env_committee.add_source(self.url, note="web")
        yield env_committee

        # for whatever reason these the clerk's office has also classified these next 3 as committees in Legistar
        mayor_agenda = Organization(name="Mayor's Agenda - Legislation to be Presented", classification="committee")
        mayor_agenda.add_source(self.url, note="web")
        yield mayor_agenda

        post_agenda = Organization(name="Post Agenda Meeting", classification="committee")
        post_agenda.add_source(self.url, note="web")
        yield post_agenda

        hearing_sched = Organization(name="PUBLIC HEARING SCHEDULE", classification="committee")
        hearing_sched.add_source(self.url, note="web")
        yield hearing_sched

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
