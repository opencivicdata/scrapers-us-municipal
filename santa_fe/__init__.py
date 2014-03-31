from pupa.scrape import Jurisdiction
from .events import SantaFeEventsScraper


class SantaFe(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:nm/place:santa_fe/council'

    name = 'Santa Fe City Council'
    url = 'http://www.santafenm.gov/index.aspx?nid=72'
    provides = ['events']

    scrapers = {
        "events": SantaFeEventsScraper
    }
