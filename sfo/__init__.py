from pupa.scrape import Jurisdiction, Organization, Person

from .people import SFPersonScraper

import datetime


class SanFrancisco(Jurisdiction):
    division_id = 'ocd-division/country:us/state:ca/county:san_francisco'
    classification = 'government'
    name = 'City and County of San Francisco'
    url =  'https://sfgov.legistar.com/'
    timezone = 'US/Pacific'

    scrapers = {
        "people": SFPersonScraper,
    }

    def get_organizations(self):
        org = Organization(name="San Francisco Board of Supervisors", classification="legislature")
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
        lee.add_source('https://en.wikipedia.org/wiki/Ed_Lee_%28politician%29')

        yield lee
