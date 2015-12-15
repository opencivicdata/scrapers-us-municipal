from pupa.scrape import Jurisdiction

from .events import CaryEventsScraper


class Cary(Jurisdiction):
    jurisdiction_id = 'ocd-jurisdiction/country:us/state:nc/place:cary/council'
    name = 'Cary Town Council'
    url = 'http://www.townofcary.org/town_council/cary_town_council.htm'

    scrapers = {'events': CaryEventsScraper}
