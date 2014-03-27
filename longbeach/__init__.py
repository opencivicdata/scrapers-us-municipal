from pupa.scrape import Jurisdiction

from .bills import BillScraper


class Jurisdiction(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:ca/place:longbeach'

    name = 'Long Beach City Council'
    url = 'http://www.longbeach.gov/cityclerk/council_online.asp'
    provides = ['people']
    parties = [ {'name': 'Democratic' }, {'name': 'Republican' } ]
    sessions = [ {'name': '2013', '_scraped_name': '2013'} ]

    def get_scraper(self, session, scraper_type):
        if scraper_type == 'bills':
            return BillScraper

    def scrape_session_list(self):
        return ['2013']

