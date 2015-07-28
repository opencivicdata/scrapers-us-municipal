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
                'bills' : NYCBillScraper,
                'events': NYCEventsScraper
    }

    legislative_sessions = [{"identifier":"2015",
            "name":"2015 Regular Session",
            "start_date": "2015-05-18",
            "end_date": "2019-05-17"},
            {"identifier":"2011",
            "name":"2011 Regular Session",
            "start_date": "2011-05-18",
            "end_date": "2015-05-17"},
            {"identifier":"2007",
            "name":"2007 Regular Session",
            "start_date": "2007-05-18",
            "end_date": "2011-05-17"}
            ]


    def get_organizations(self):
        council = Organization('New York City Council', classification='legislature')
        for x in range(1,52):
            council.add_post("District {}".format(x),
                             role='Council Member')
        yield council

        mayor = Organization('Mayor', classification='executive')

        yield mayor

    LEGISTAR_ROOT_URL = 'http://legistar.council.nyc.gov/'

