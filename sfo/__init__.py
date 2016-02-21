from pupa.scrape import Jurisdiction, Organization, Person

from .bills import SFBillScraper
from .events import SFEventScraper
from .people import SFPersonScraper
from .organizations import SFOrganizationScraper

import datetime


class SanFrancisco(Jurisdiction):
    division_id = 'ocd-division/country:us/state:ca/county:san_francisco'
    classification = 'government'
    name = 'City and County of San Francisco'
    url =  'https://sfgov.legistar.com/'
    timezone = 'US/Pacific'

    council_name = 'San Francisco Board of Supervisors'

    scrapers = {
        "people": SFPersonScraper,
        "events": SFEventScraper,
        "bills": SFBillScraper,
        "organizations": SFOrganizationScraper,
    }

    legislative_sessions = [{"identifier": str(start_year),
                             "name": ("%s Regular Session" % str(start_year)),
                             "start_date": ("%s-01-08" % str(start_year)),
                             "end_date": ("%s-01-07" % str(start_year + 1))}
                            for start_year
                            in range(1998, 2017)]


    def get_organizations(self):
        org = Organization(name=self.council_name, classification="legislature")
        for x in range(1, 12):
            org.add_post(
                "District {}".format(x),
                "Supervisor",
                division_id='{}/council_district:{}'.format(self.division_id, x))

        yield org

        mayor = Organization('Office of the Mayor', classification='executive')

        yield mayor

        lee = Person(name="Edwin M. Lee",
                       primary_org='executive',
                       role='Mayor',
                       primary_org_name='Office of the Mayor',
                       start_date=datetime.date(2011, 1, 11))
        lee.add_name('Mayor')
        lee.add_source('https://en.wikipedia.org/wiki/Ed_Lee_%28politician%29')

        yield lee
