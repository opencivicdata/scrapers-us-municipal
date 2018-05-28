# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization
from .events import NashvilleEventScraper
from .people import NashvillePersonScraper
from .bills import NashvilleBillScraper
from .vote_events import NashvilleVoteEventScraper


class Nashville(Jurisdiction):
    division_id = "ocd-division/country:us/state:tn/place:nashville"
    classification = "government"
    name = "Metropolitan Government of Nashville & Davidson County"
    url = "https://www.nashville.gov/"

    scrapers = {
        # "events": NashvilleEventScraper,
        "people": NashvillePersonScraper,
        "bills": NashvilleBillScraper,
        # "vote_events": NashvilleVoteEventScraper,
    }

    def get_organizations(self):
        # Mayor's Office
        mayors_office = Organization(
            name="Mayor's Office", classification="executive")

        mayors_office.add_post(label="Mayor", role="mayor")
        # Copied from https://www.nashville.gov/Mayors-Office.aspx
        mayors_office.add_post(label="Receptionist / Administrative Assistant",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Metro General Services Photographer",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Press Secretary",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(
            label="Communications Director", role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Director, Mayor’s Office of Transportation and Sustainability",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Special Assistant to the Mayor / Scheduler",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Director, Mayor’s Office of Housing",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(
            label="Deputy Resilience Officer", role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Senior Advisor, Workforce, Diversity and Inclusion",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Transportation & Sustainability Manager",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(
            label="Chief Strategy Officer", role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Manager, Small Business/Creative Economy",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Executive Director, The Barnes Fund",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Chief of Staff",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Director, Mayor’s Office of Neighborhoods and Community Engagement",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Director of Community Engagement",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Early Childhood Education Project Manager",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(
            label="Senior Advisor for Education", role="staff", division_id=self.division_id)
        mayors_office.add_post(
            label="Senior Legislative Advisor", role="staff", division_id=self.division_id)
        mayors_office.add_post(
            label="Chief Operating Officer", role="staff", division_id=self.division_id)
        mayors_office.add_post(
            label="Youth Policy Consultant", role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Executive Assistant to Chief Operating Officer",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Executive Assistant to the Mayor",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(
            label="Community Relations Liaison", role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Director, Constituent Response/hubNashville",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Director, Mayor’s Office of Economic and Community Development",
                               role="staff", division_id=self.division_id)
        mayors_office.add_post(
            label="Senior Legislative Advisor", role="staff", division_id=self.division_id)
        mayors_office.add_post(label="Senior Advisor for Health and Wellness Policy",
                               role="staff", division_id=self.division_id)

        yield mayors_office
        # City Council
        city_council = Organization(
            name="Nashville Metropolitan Council", classification="legislature")
        city_council.add_post(label="Vice Mayor",
                              role="vicemayor", division_id=self.division_id)
        AT_LARGE_SEATS = 4
        for at_large_seat in range(1, AT_LARGE_SEATS + 1):
            city_council.add_post(label="At Large({})".format(
                at_large_seat), role="councilmember", division_id=self.division_id)
        DISTRICTS = 3
        for district in range(1, DISTRICTS + 1):
            city_council.add_post(label="District {}".format(
                district), role="councilmember", division_id=self.division_id)

        yield city_council
