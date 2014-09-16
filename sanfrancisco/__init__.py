from pupa.scrape import Jurisdiction

from granicus.pupa.events import make_event_scraper


class SanFrancisco(Jurisdiction):
    division_id = 'ocd-division/country:us/state:ca/place:san_francisco'
    name = 'San Francisco'
    url =  'http://sfgov.org/'
    classification = "government"

    scrapers = {
        "events": make_event_scraper("sanfrancisco"),
    }
