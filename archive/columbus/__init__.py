from pupa.scrape import Jurisdiction

from .people import ColumbusPersonScraper
from .events import ColumbusEventScraper


class Columbus(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:oh/place:columbus/council'

    name = 'Columbus City Council'
    url = 'http://council.columbus.gov/'

    scrapers = {
        "people": ColumbusPersonScraper,
        "events": ColumbusEventScraper,
    }
