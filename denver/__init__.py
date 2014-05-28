from pupa.scrape import Jurisdiction

# from .events import BoiseEventScraper
from .people import PersonScraper
from .bills import BillScraper


class Denver(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:co/place:denver/council'

    name = 'Denver City Council'
    url = 'https://www.denvergov.org/citycouncil'
    parties = [{'name': 'Democratic' }, {'name': 'Republican' }, ]

    scrapers = {'people': PersonScraper, 'bills': BillScraper}
