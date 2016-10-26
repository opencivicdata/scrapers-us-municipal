# encoding=utf-8
from pupa.scrape import Jurisdiction, Organization
from .people import NYCPersonScraper
from .events import NYCEventsScraper
from .bills import NYCBillScraper

class NYC(Jurisdiction):
    classification = 'government'
    division_id = 'ocd-division/country:us/state:ny/place:new_york'
    name = 'New York City'
    timezone = 'America/New_York'
    url = 'http://nyc.gov'

    parties = [
        {'name': 'Democratic'},
        {'name': 'Republican'}
    ]
    scrapers = {'people': NYCPersonScraper,
#                'bills' : NYCBillScraper,
#                'events': NYCEventsScraper
    }

    legislative_sessions = [{"identifier": str(start_year),
                             "name": ("%s Regular Session" % str(start_year)),
                             "start_date": ("%s-01-01" % str(start_year)),
                             "end_date": ("%s-12-31" % str(start_year + 3))}
                            for start_year
                            in range(1978, 2015, 4)]

    def get_organizations(self):
        council = Organization('New York City Council', classification='legislature')
        for x in range(1,52):
            council.add_post("District {}".format(x),
                             role='Council Member',
                             division_id='ocd-division/country:us/state:ny/place:new_york/council_district:{}'.format(x))
        yield council

        mayor = Organization('Mayor', classification='executive')

        yield mayor

    LEGISTAR_ROOT_URL = 'http://legistar.council.nyc.gov/'

